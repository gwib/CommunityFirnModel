from solver import transient_solve_TR
from constants import *
import numpy as np
from scipy import interpolate

'''
code to handle diffusion (heat, enthalpy, isotope)
calls solver
Draws from Numerical Heat Transfer and Heat Flow (Patankar, 1980)
'''

def heatDiff(self,iii):
    '''
    Heat diffusion function

    :param z:
    :param dz:
    :param Ts:
    :param rho:

    :returns self.Tz:
    :returns self.T10m:
    '''

    nz_P             = len(self.z)
    nz_fv             = nz_P - 2
    nt                 = 1

    # z_edges_vec     = self.z[1:-2] + self.dz[2:-1] / 2
    # z_edges_vec     = np.concatenate(([self.z[0]], z_edges_vec, [self.z[-1]]))
    # z_P_vec         = self.z

    z_edges_vec1 = self.z[0:-1] + np.diff(self.z) / 2
    z_edges_vec = np.concatenate(([self.z[0]], z_edges_vec1, [self.z[-1]]))
    z_P_vec     = self.z
    
    phi_s             = self.Tz[0]
    phi_0             = self.Tz

    #print('------Diffusion--------')
    #print(self.rho)
    K_ice             = 9.828 * np.exp(-0.0057 * phi_0)
    K_firn             = K_ice * (self.rho / 1000) ** (2 - 0.5 * (self.rho / 1000)) #Reference?
    # K_firn             = 0.021 + 2.5 * (self.rho/1000.)**2 #Anderson (1976), from Brandt (1997)
    c_firn             = 152.5 + 7.122 * phi_0

    Gamma_P         = K_firn / (c_firn) #* self.rho)
    tot_rho         = self.rho
    

    self.Tz         = transient_solve_TR(z_edges_vec, z_P_vec, nt, self.dt, Gamma_P, phi_0, nz_P, nz_fv, phi_s, tot_rho)

    fT10m             = interpolate.interp1d(self.z, self.Tz)    #TODO: added fill_value="extrapolate", remove if things go very wrong
    self.T10m         = fT10m(10)

    if np.any(self.Tz>273.15):
        print('WARNING: TEMPERATURE EXCEEDS MELTING TEMPERATURE')
        print('WARM TEMPERATURES HAVE BEEN SET TO 273.15; MODEL RUN IS CONTINUING')
        self.Tz[self.Tz>=273.15]=273.15

    return self.Tz, self.T10m
### end heat diffusion
######################

def enthalpyDiff(self,iii):
    '''
    enthalpy diffusion function

    '''
    enthalpy = np.zeros_like(self.dz)
    porosity = 1 - self.rho/RHO_I

    self.Tz[self.LWC>0] = 273.15

    ### method from Aschwanden, 2012
    LWCmass     = self.LWC * RHO_W_KGM
    LWCmass_old = np.copy(LWCmass)
    
    tot_rho     = (self.mass + LWCmass) / self.dz # Aschwanden, eq

    rho_h         = np.copy(self.rho)
    Tzold         = np.copy(self.Tz)
    tot_mass    = self.mass + LWCmass
    omega       = (LWCmass/self.dz) / tot_rho # Aschwanden, eq 2

    # c_firn      = 152.5 + 7.122 * self.Tz
    # Hs          = T_MELT * CP_I  # inline, page 450 second column, right before eq 76. Setting T_0 = 0.
    Hs             = 0 # inline, page 450 second column, right before eq 76. Setting T_0 = 0.
 
    enthalpy[self.Tz<T_MELT]    = (self.Tz[self.Tz<T_MELT] - T_MELT) * CP_I
    enthalpy[self.Tz>=T_MELT]   = (self.Tz[self.Tz>=T_MELT] - T_MELT) * CP_I + omega[self.Tz>=T_MELT] * LF_I

    enthalpy_h = np.copy(enthalpy)

    # enthalpy = enthalpy*tot_rho

    nz_P     = len(self.z)
    nz_fv     = nz_P - 2
    nt         = 1

    ## this is the older, (semi) working bit.
    z_edges_vec1 = self.z[0:-1] + np.diff(self.z) / 2
    z_edges_vec = np.concatenate(([self.z[0]], z_edges_vec1, [self.z[-1]]))
    z_P_vec     = self.z
    
    ##

    # z_edges_vec = self.z
    # z_edges_vec = np.concatenate(([z_edges_vec[0]], z_edges_vec, [z_edges_vec[-1]]))
    # z_P_vec     = z_edges_vec[0:-1] + np.diff(z_edges_vec) / 2
    # z_P_vec = np.concatenate(([z_edges_vec[0]], z_P_vec1, [z_edges_vec[-1]]))
    
    # print(iii)
    # print('z',self.z[0:6])
    # print('dz',self.dz[0:6])
    # print('sum dz', np.cumsum(self.dz[0:6]))
    # print('z_edges_vec', z_edges_vec[0:6])
    # print('z_P_vec', z_P_vec[0:6])
    # # print('z_diff',z_diff[0:6])
    # print('len z_edges_vec', len(z_edges_vec))
    # print('len z_P_vec', len(z_P_vec))
    # print('len rho:', len(self.rho))

    phi_s         = enthalpy[0] # phi surface; upper boundary condition
    phi_0         = enthalpy # initial guess
    
    ### conductivity. Choose your favorite!
    # k_i         = (1-porosity)*2.1 # Meyer and Hewitt, 2017
    # k_i         = 0.021 + 2.5 * (self.rho/1000.)**2 # Brandt, 1997
    # k_i         = 2.22362 * (self.rho/1000.)**1.885 # Yen (1981), also in van der Veen (2013)
    # k_i         = 0.0784 + 2.697 * (self.rho/1000.)**2 # Jiawen (1991)
    # k_i         = 3.e-6*self.rho**2 - 1.06e-5*self.rho + 0.024 #Riche and Schneebeli (2013)
    k_ice             = 9.828 * np.exp(-0.0057 * self.Tz)
    k_i             = k_ice * (self.rho / 1000) ** (2 - 0.5 * (self.rho / 1000)) # Reference?
    
    bigKi                     = k_i / CP_I
    bigKi[enthalpy>=Hs]     = bigKi[enthalpy>=Hs] / 20 # from Aschwanden
    # bigKi[enthalpy>=Hs]     = 5.0e-5 # from Aschwanden. Can play with this number, but things break if it gets too small.

    e_less                 = np.where(enthalpy<Hs)[0]
    e_great             = np.where(enthalpy>=Hs)[0]
    Gamma_P             = np.zeros_like(self.dz)
    Gamma_P[e_less]     = bigKi[e_less] #/tot_rho[e_less]
    Gamma_P[e_great]     = bigKi[e_great] #/tot_rho[e_great]

    # if (iii>30 and iii<40):
    #     print(iii)
    #     print('max rho ',np.max(self.rho))
    #     print('min rho ',np.min(self.rho))
    #     # print('max drho ',np.max(drho_dt))
    #     print('min T',np.min(self.Tz))
    #     print('max T ',np.max(self.Tz))
    #     # ind1 = np.where(drho_dt==np.max(drho_dt))[0][0]
    #     ind1 = np.where(self.dz>2.0)[0][0]
    #     print('ind1, ', ind1)
    #     print('depth', self.z[ind1-3:ind1+4])
    #     print('temp', self.Tz[ind1])
    #     print('tempr', self.Tz[ind1-3:ind1+4])
    #     print('lwc', self.LWC[ind1])
    #     print('lwcr', self.LWC[ind1-3:ind1+4])
    #     print('rho', self.rho[ind1])
    #     print('rhor', self.rho[ind1-3:ind1+4])                
    #     # print('min drho ',np.min(drho_dt))
    #     print('tot_rho',tot_rho[ind1-3:ind1+4])
    #     input()

    enthalpy = transient_solve_TR(z_edges_vec, z_P_vec, nt, self.dt, Gamma_P, phi_0, nz_P, nz_fv, phi_s, tot_rho)

    e_less                 = np.where(enthalpy<Hs)[0]
    e_great             = np.where(enthalpy>=Hs)[0]
    self.Tz[e_less]     = enthalpy[e_less] / CP_I + T_MELT
    self.Tz[e_great]     = T_MELT

    omega_new             = np.zeros_like(omega)
    omega_new[e_great]     = (enthalpy[e_great] - Hs) / (LF_I)

    LWCrho                 = omega_new * tot_rho
    LWCmass_new         = LWCrho * self.dz

    self.rho             = tot_rho - LWCrho
    self.mass             = self.rho * self.dz
    self.LWC              = LWCmass_new / RHO_W_KGM

    tot_mass_new         = self.mass + LWCmass_new

    print('---------------')
    print(self.z)
    print(self.Tz)
    print('-------')
    fT10m                 = interpolate.interp1d(self.z, self.Tz)                               # temp at 10m depth
    self.T10m             = fT10m(10)

    return self.Tz, self.T10m, self.rho, self.mass, self.LWC
### end enthalpy diffusion
########################## 

def isoDiff(self,iii):
    '''
    Isotope diffusion function

    :param iter:
    :param z:
    :param dz:
    :param rho:
    :param iso:

    :returns self.phi_t:
    '''
    nz_P         = len(self.z)                                           # number of nodes in z
    nz_fv         = nz_P - 2                                              # number of finite volumes in z
    nt             = 1                                                     # number of time steps

    z_edges_vec = self.z[1:-2] + self.dz[2:-1] / 2                        # uniform edge spacing of volume edges
    z_edges_vec = np.concatenate(([self.z[0]], z_edges_vec, [self.z[-1]]))
    z_P_vec     = self.z

    ### Node positions
    phi_s         = self.del_z[0]                                            # isotope value at surface
    phi_0         = self.del_z                                               # initial isotope profile

    ### Define diffusivity for each isotopic species
    ### Establish values needed for diffusivity calculation
    m             = 0.018                                                   # kg/mol; molar mass of water
    pz             = 3.454 * np.power(10, 12) * np.exp(-6133 / self.Tz)    # Pa; saturation vapor pressure over ice

    alpha_18_z     = 0.9722 * np.exp(11.839 / self.Tz)                        # fractionation factor for 18_O
    # alpha_18_z     = np.exp(11.839/Tz-28.224*np.power(10,-3))            # alternate formulation from Eric's python code
    alpha_D_z     = 0.9098 * np.exp(16288 / np.power(self.Tz, 2))            # fractionation factor for D
    Po             = 1.0                                                     # reference pressure in atm
    P             = 1.0

    ### Set diffusivity in air (units of m^2/s)
    # Da         = 2.1 * np.power(10.0, -5.) * np.power(self.Tz / 273.15, 1.94) * (Po / P)
    Da             = 2.1 * 1.0e-5 * (self.Tz / 273.15)**1.94 * (Po / P)
    Da_18         = Da / 1.0285                  # account for fractionation factor for 18_O, fixed Johnsen typo
    Da_D         = Da / 1.0251                # account for fractionation factor for D, fixed Johnsen typo

    ### Calculate tortuosity
    invtau         = np.zeros(int(len(self.dz)))
    b             = 0.25                                                                    # Tortuosity parameter
    invtau[self.rho < RHO_I / np.sqrt(b)]     = 1.0 - (b * (self.rho[self.rho < RHO_I / np.sqrt(b)] / RHO_I)) ** 2
    invtau[self.rho >= RHO_I / np.sqrt(b)]     = 0.0

    ### Set diffusivity for each isotope
    if self.c['iso'] == '18':
        D             = m * pz * invtau * Da_18 * (1 / self.rho - 1 / RHO_I) / (R * self.Tz * alpha_18_z)
        D             = D + 1.5e-15
        self.del_z     = transient_solve_TR(z_edges_vec, z_P_vec, nt, self.dt, D, phi_0, nz_P, nz_fv, phi_s)
    elif self.c['iso'] == 'D':
        D             = m * pz * invtau * Da_D * (1 / self.rho - 1 / RHO_I) / (R * self.Tz * alpha_D_z)
        D[D<=0.0]     = 1.0e-20
        self.del_z     = transient_solve_TR(z_edges_vec, z_P_vec, nt, self.dt, D, phi_0, nz_P, nz_fv, phi_s)
    elif self.c['iso'] == 'NoDiffusion':
        pass
        
    ### Solve for vertical isotope profile at this time step i
    self.del_z = np.concatenate(([self.del_s[iii]], self.del_z[:-1]))

    return self.del_z
### end isotope diffusion
##########################