import numpy as np
from scipy import interpolate
import scipy.integrate
from scipy.sparse import spdiags
import scipy.sparse.linalg as splin
from constants import *


def solver(a_U, a_D, a_P, b):
    '''
    function for solving matrix problem

    :param a_U:
    :param a_D:
    :param a_P:
    :param b:

    :return phi_t:
    '''

    nz = np.size(b)

    diags = (np.append([a_U, -a_P], [a_D], axis = 0))
    cols = np.array([1, 0, -1])

    big_A = spdiags(diags, cols, nz, nz, format = 'csc')
    big_A = big_A.T

    rhs = -b
    phi_t = splin.spsolve(big_A, rhs)

    return phi_t

def transient_solve_TR(z_edges, z_P_vec, nt, dt, Gamma_P, phi_0, nz_P, nz_fv, phi_s, tot_rho, airdict=None):
    '''
    transient 1-d diffusion finite volume method

    :param z_edges:
    :param z_P_vec:
    :param nt:
    :param dt:
    :param Gamma_P:
    :param phi_0:
    :param nz_P:
    :param nz_fv:
    :param phi_s:

    :return phi_t:
    '''

    phi_t = phi_0

    for i_time in range(nt):
        Z_P = z_P_vec
        # print(len(Z_P))
        # dZ = np.concatenate(([1], np.diff(z_edges), [1]))

        # dzev = np.diff(z_edges)
        # dZ = np.concatenate(([dzev[0]], dzev, [dzev[-1]]))

        dZ = np.diff(z_edges)
        # print('dZ:', dZ)
        # print('len dZ:', len(dZ))


        # if (dZ<=0).any():
        #   ind10 = np.where(dZ<=0)[0]
        #   print('!!!!!!')
        #   print('ind10:',ind10)
        #   print('z ind', Z_P[0:ind10[0]+3])
        #   print('z z_edges', z_edges[0:ind10[0]+3])
        #   print('dz ind', dZ[0:ind10[0]+3])
        #   input('enter to continue')

        dZ_u = np.diff(Z_P)
        dZ_u = np.append(dZ_u[0], dZ_u)
        
        dZ_d = np.diff(Z_P)
        dZ_d = np.append(dZ_d, dZ_d[-1])

        # f_u = np.append(0, (1 - (z_P_vec[1:] - z_edges) / dZ_u[1:]))
        # f_d = np.append(1 - (z_edges - z_P_vec[0: -1]) / dZ_d[0: -1], 0)

        f_u = 1 - (z_P_vec[:] - z_edges[0:-1]) / dZ_u[:]
        f_d = 1 - (z_edges[1:] - z_P_vec[:]) / dZ_d[:]

        # Gamma_U = np.append(Gamma_P[0], Gamma_P[0: -1] )
        # Gamma_D = np.append(Gamma_P[1:], Gamma_P[-1])

        # Gamma_u =  1 / ((1 - f_u) / Gamma_P + f_u / Gamma_U)
        # Gamma_d =  1 / ((1 - f_d) / Gamma_P + f_d / Gamma_D)

        ##################
        if airdict!=None: # this part for gas diffusion, which takes a bit more physics
            Gamma_Po    = Gamma_P * airdict['por_op']
            
            Gamma_U     = np.append(Gamma_Po[0], Gamma_Po[0: -1] )
            Gamma_D     = np.append(Gamma_Po[1:], Gamma_Po[-1])
            Gamma_u     =  1 / ((1 - f_u) / Gamma_Po + f_u / Gamma_U)
            Gamma_d     =  1 / ((1 - f_d) / Gamma_Po + f_d / Gamma_D)

            d_eddy_P    = airdict['d_eddy'] * airdict['por_op']
            d_eddy_U    = np.append(d_eddy_P[0], d_eddy_P[0:-1] )
            d_eddy_D    = np.append(d_eddy_P[1:], d_eddy_P[-1])
            d_eddy_u    =  1/ ( (1 - f_u)/d_eddy_P + f_u/d_eddy_U )
            d_eddy_d    =  1/ ( (1 - f_d)/d_eddy_P + f_d/d_eddy_D )
            
            if airdict['gravity']=="off" and airdict['thermal']=="off":
                S_C_0   = 0.0

            elif airdict['gravity']=='on' and airdict['thermal']=='off':
                S_C_0   = (-Gamma_d + Gamma_u) * (airdict['deltaM'] * GRAVITY / (R * airdict['Tz'])) / airdict['dz'] #S_C is independent source term in Patankar

            elif airdict['gravity']=='on' and airdict['thermal']=='on':
                dTdz    = np.gradient(airdict['Tz'])/airdict['dz']
                S_C_0   = (Gamma_d-Gamma_u) * ((-airdict['deltaM'] * GRAVITY / (R * airdict['Tz'])) + (airdict['omega'] * dTdz)) / airdict['dz'] # should thermal still work in LIZ? if so use d_eddy+diffu
            
            S_C         = S_C_0 * phi_t # Should this be phi_0 instead?
            b_0         = S_C * dZ

            rho_edges = np.interp(z_edges,Z_P,airdict['rho'])
            
            w_edges = w(airdict, z_edges, rho_edges, Z_P, dZ) # advection term (upward relative motion due to porosity changing)

            w_p = np.interp(Z_P,z_edges,w_edges) # Units m/s
            w_edges[z_edges>airdict['z_co']] = 0.0          
            w_u = w_edges[0:-1]
            w_d = w_edges[1:]

            D_u = ((Gamma_u+d_eddy_u) / dZ_u) # Units m/s
            D_d = ((Gamma_d+d_eddy_d) / dZ_d)   
            F_u =  w_u * airdict['por_op'] # Units m/s
            F_d =  w_d * airdict['por_op']
            
            P_u = F_u / D_u
            P_d = F_d / D_d
            
            a_U = D_u * A( P_u ) + F_upwind(  F_u )
            a_D = D_d * A( P_d ) + F_upwind( -F_d )

            # a_U = D_u # 8/14/17: use this for now - check on Lagrangian need for upwinding.
            # a_D = D_d 
        
            a_P_0 = airdict['por_op'] * dZ / dt
        #######################################

        else: #just for heat, isotope diffusion
            Gamma_U = np.append(Gamma_P[0], Gamma_P[0: -1] )
            Gamma_D = np.append(Gamma_P[1:], Gamma_P[-1])

            Gamma_u =  1 / ((1 - f_u) / Gamma_P + f_u / Gamma_U) # Patankar eq. 4.9
            Gamma_d =  1 / ((1 - f_d) / Gamma_P + f_d / Gamma_D)

            S_C = 0
            S_C = S_C * np.ones(nz_P)
            
            #print('-----Solver-------') #TODO
            #print(Gamma_P)
            #print(Gamma_U)
            #print(str((1 - f_u) / Gamma_P + f_u / Gamma_U))
            #print('--------------')

            D_u = (Gamma_u / dZ_u)
            D_d = (Gamma_d / dZ_d)

            b_0 = S_C * dZ

            a_U = D_u 
            a_D = D_d 

            # a_P_0 = dZ / dt
            a_P_0 = tot_rho * dZ / dt
            # a_P_0 = RHO_I * c_firn * dZ / dt
            

        S_P     = 0.0
        a_P     = a_U + a_D + a_P_0 - S_P*dZ

        bc_u_0  = phi_s # need to pay attention for gas
        bc_type = 1
        bc_u    = np.concatenate(([ bc_u_0], [bc_type]))

        bc_d_0  = 0
        bc_type = 2
        bc_d    = np.concatenate(([ bc_d_0 ], [ bc_type ]))

        b       = b_0 + a_P_0 * phi_t

        #Upper boundary
        a_P[0]  = 1
        a_U[0]  = 0
        a_D[0]  = 0
        b[0]    = bc_u[0]

        #Down boundary
        a_P[-1] = 1
        a_D[-1] = 0
        a_U[-1] = 1
        b[-1]   = dZ_u[-1] * bc_d[0]

        phi_t = solver(a_U, a_D, a_P, b)
        a_P = a_U + a_D + a_P_0

    if airdict!=None:
        return phi_t, w_p
    else:
        return phi_t

'''
Functions below are for firn air
'''
def w(airdict, z_edges, rho_edges, Z_P, dZ): # Function for downward advection of air and also calculates total air content. 
    if airdict['advection_type']=='Darcy':
        por_op_edges=np.interp(z_edges,airdict['z'],airdict['por_op'])
        T_edges = np.interp(z_edges,airdict['z'],airdict['Tz'])
        p_star = por_op_edges * np.exp(M_AIR *GRAVITY*z_edges/(R*T_edges))
        dPdz = np.gradient(airdict['air_pressure'],airdict['z'])
        dPdz_edges=np.interp(z_edges,airdict['z'],dPdz)

        # perm = 10.0**(-7.29) * por_op_edges**3.71 # Adolph and Albert, 2014, eq. 5, units m^2
        # perm = 10.0**(-7.7) * por_op_edges**3.4 #Freitag, 2002 
        perm = 10.0**(-7.7) * p_star**3.4 #Freitag, 2002 
        visc = 1.5e-5 #kg m^-1 s^-1, dynamic viscosity, source?
        flux = -1.0 * perm / visc * dPdz_edges # units m/s
        # w_ad = flux / airdict['dt']  / por_op_edges # where did I get this?
        w_ad = flux / p_star / airdict['dt']
        # w_ad = flux / por_op_edges / airdict['dt']

    elif airdict['advection_type']=='Christo':
        por_tot_edges       = np.interp(z_edges,Z_P,airdict['por_tot'])
        por_cl_edges        = np.interp(z_edges,Z_P,airdict['por_cl'])
        por_op_edges        = np.interp(z_edges,Z_P,airdict['por_op'])
        w_firn_edges        = np.interp(z_edges,Z_P,airdict['w_firn'])
        T_edges              = np.interp(z_edges,Z_P,airdict['Tz'])
        p_star              = por_op_edges * np.exp(M_AIR *GRAVITY*z_edges/(R*T_edges))
        dscl                = np.gradient(por_cl_edges,z_edges)
        C                   = np.exp(M_AIR*GRAVITY*z_edges/(R*T_edges))

        # m1 = np.tile(por_op_edges,(len(por_op_edges),1))
        # Xi_up = m1/m1.T
        # m2 = np.tile(w_firn_edges, (len(w_firn_edges),1))
        # Xi_down = 1 + np.log(m2.T / m2)
        # Xi = Xi_up / Xi_down

        op_ind              = np.where(z_edges<=airdict['z_co'])[0]
        co_ind              = op_ind[-1]
        cl_ind              = np.where(z_edges>airdict['z_co'])[0]

        Xi                  = np.zeros((len(op_ind),len(op_ind)))
        Xi_up               = por_op_edges[op_ind]/np.reshape(por_op_edges[op_ind], (-1,1))
        Xi_down             = (1 + np.log( np.reshape(w_firn_edges[op_ind], (-1,1))/ w_firn_edges[op_ind] ))
        Xi                  = Xi_up / Xi_down # Equation 5.10 in Christo's thesis; Xi[i,j] is the pressure increase (ratio) for bubbles at depth[i] that were trapped at depth[j]

        # Xi                  = np.zeros((len(z_edges),len(z_edges)))
        # Xi_up               = por_op_edges/np.reshape(por_op_edges, (-1,1))
        # Xi_down             = (1 + np.log( np.reshape(w_firn_edges, (-1,1))/ w_firn_edges ))
        # Xi                  = Xi_up / Xi_down # Equation 5.10 in Christo's thesis; Xi[i,j] is the pressure increase (ratio) for bubbles at depth[i] that were trapped at depth[j]

        integral_matrix     = (Xi.T*dscl[op_ind]*C[op_ind]).T 
        integral_matrix_sum = integral_matrix.sum(axis=1)

        p_ratio             = np.zeros_like(z_edges)

        p_ratio[op_ind]     = integral_matrix_sum#[op_ind]   #5.11
        # p_ratio[cl_ind]     = p_ratio[co_ind]*Xi[cl_ind, co_ind] # 5.12
        p_ratio[cl_ind]     = integral_matrix_sum[-1] #*Xi[cl_ind, co_ind] # 5.12

        flux                = w_firn_edges[co_ind] * p_ratio[co_ind] * por_cl_edges[co_ind]
        # velocity            = np.minimum(w_firn_edges ,((flux + 1e-10 - w_firn_edges * p_ratio * por_cl_edges) / ((por_op_edges + 1e-10 * C))/airdict['dt']))
        # velocity            = (flux + 1e-10 - w_firn_edges * p_ratio * por_cl_edges) / ((por_op_edges + 1e-10 * C))/airdict['dt']
        # velocity = np.minimum(w_firn_edges, (flux / p_star / airdict['dt']))
        velocity = flux / p_star / airdict['dt']
        w_ad                = velocity - w_firn_edges
        # w_ad[cl_ind] = 0 
        # veldiff = velocity
        # ind4 = np.where()
        # print('vel',velocity[co_ind+5])
        # print('w_firn',w_firn_edges[co_ind+5])
        # print('w_ad',w_ad[co_ind+5])
        # input() 

    elif airdict['advection_type']=='zero':
        w_ad = np.zeros_like(rho_edges)

    return w_ad


def A(P): # Power-law scheme, Patankar eq. 5.34
    A = np.maximum( (1 - 0.1 * np.abs( P ) )**5, np.zeros(np.size(P) ) )
    return A    

def F_upwind(F): # Upwinding scheme
    F_upwind = np.maximum( F, 0 )
    return F_upwind


# def w(z_edges,rho_edges,por_op,T,p_a,por_tot,por_cl,Z_P,dz, w_firn): # Function for downward advection of air and also calculates total air content. 
    
#     por_tot_edges=np.interp(z_edges,Z_P,por_tot)
#     por_cl_edges=np.interp(z_edges,Z_P,por_cl)
#     por_op_edges=np.interp(z_edges,Z_P,por_op)
#     teller_co=np.argmax(por_cl_edges)
#     # w_firn_edges=Accu*rho_i/rho_edges #Check this - is there a better way?
#     w_firn_edges=np.interp(z_edges,Z_P,w_firn)
    
#     # if ad_method=='ice_vel':
#     #     w_ad=w_firn_edges
#     #     trapped = 0.0
#     #     bubble_pres = np.zeros_like(z_edges)
    

#     ### Christo's Method from his thesis (chapter 5). This (maybe) could be vectorized to speed it up.
    
#     bubble_pres = np.zeros_like(z_edges)
#     # print(len(np.diff(por_cl)))
#     # print(len(dz))
#     # dscl = np.append(0, np.diff(por_cl)/dz)
#     dscl = np.append(0, np.gradient(por_cl,dz))
#     T_edges = np.interp(z_edges,Z_P,T)
#     C=np.exp(M_AIR*GRAVITY*z_edges/(R*T_edges))
#     strain = np.gradient(np.log(w_firn),dz)
#     s=por_op_edges+por_cl_edges
    
#     for teller1 in range (0,teller_co+1): 
#         integral = np.zeros(teller1+1)
#         integral2 = np.zeros(teller1+1)
        
#         for teller2 in range(0,teller1+1):
#             # integral[teller2] = dscl[teller2]*C[teller2]*(s[teller2]/s[teller1])/(1+scipy.integrate.trapz(strain[teller2:teller1+1],dz)) #need to get this indexing correct 6/19/14: I think it is fine.
#             integral[teller2] = dscl[teller2]*C[teller2]*(s[teller2]/s[teller1])/(1+scipy.integrate.trapz(strain[teller2:teller1+1],z_edges[teller2:teller1+1])) #need to get this indexing correct 6/19/14: I think it is fine.
#             if dscl[teller2]==0:
#                 dscl[teller2]=1e-14
#             integral2[teller2] = dscl[teller2]
            
#         bubble_pres[teller1] = (np.mean(dz)*np.sum(integral))/(np.mean(dz)*np.sum(integral2))
    
#     bubble_pres[teller_co+1:] = bubble_pres[teller_co]*(s[teller_co]/s[teller_co+1:])/(w_firn_edges[teller_co+1:]/w_firn_edges[teller_co])
    
#     bubble_pres[0] = 1
#     #print 'bubble pressure = %s' % bubble_pres
    
#     flux= w_firn_edges[teller_co]*bubble_pres[teller_co]*por_cl[teller_co]

#     velocity = np.minimum(w_firn_edges ,((flux+(1e-10)-w_firn_edges*bubble_pres*por_cl_edges)/((por_op_edges+1e-10)*C)))
#     #velocity = velocity * 2   
#     w_ad=velocity


#     return w_ad #, bubble_pres