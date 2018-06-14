from diffusion import *
from reader import read_input
from reader import read_init
from writer import write_spin_hdf5
from writer import write_nospin_hdf5
from physics import *
from constants import *
from melt import *
import numpy as np
import csv
import json
import sys
import math
from shutil import rmtree
import os
import shutil
import time
import inspect
import h5py
import scipy.interpolate as interpolate
from firn_air import FirnAir
from regrid import *

class FirnDensityNoSpin:
    '''
    Parameters used in the model, for the initialization as well as the time evolution:

    : gridLen: size of grid used in the model run
                (unit: number of boxes, type: int)
    : dx: vector of width of each box, used for stress calculations
                (unit: m, type: array of ints)
    : dt: number of seconds per time step
                (unit: seconds, type: float)
    : t: number of years per time step
                (unit: years, type: float)
    : modeltime: linearly spaced time vector from indicated start year to indicated end year
                (unit: years, type: array of floats)
    : years: total number of years in the model run
                (unit: years, type: float)
    : stp: total number of steps in the model run
                (unit: number of steps, type: int)
    : T_mean: interpolated temperature vector based on the model time and the initial user temperature data
                (unit: ???, type: array of floats)
    : Ts: interpolated temperature vector based on the model time & the initial user temperature data
                may have a seasonal signal imposed depending on number of years per time step (< 1)
                (unit: ???, type: array of floats)
    : bdot: bdot is meters of ice equivalent/year. multiply by 0.917 for W.E. or 917.0 for kg/year
                (unit: ???, type: )
    : bdotSec: accumulation rate vector at each time step
                (unit: ???, type: array of floats)
    : rhos0: surface accumulate rate vector
                (unit: ???, type: array of floats)
    : bdot_mean: mean accumulation over the lifetime of each parcel
                (units are m I.E. per year)
    :returns D_surf: diffusivity tracker
                (unit: ???, type: array of floats)

    '''

    def __init__(self, configName):
        '''
        Sets up the initial spatial grid, time grid, accumulation rate, age, density, mass, stress, temperature, and diffusivity of the model run
        :param configName: name of json config file containing model configurations
        '''
        ### load in json config file and parses the user inputs to a dictionary
        self.spin = True
        with open(configName, "r") as f:
            jsonString      = f.read()
            self.c          = json.loads(jsonString)
        print("Main run starting")
        print("physics are", self.c['physRho'])

        ### read in initial depth, age, density, temperature from spin-up results
        initDepth   = read_init(self.c['resultsFolder'], self.c['spinFileName'], 'depthSpin')
        initAge     = read_init(self.c['resultsFolder'], self.c['spinFileName'], 'ageSpin')
        initDensity = read_init(self.c['resultsFolder'], self.c['spinFileName'], 'densitySpin')
        initTemp    = read_init(self.c['resultsFolder'], self.c['spinFileName'], 'tempSpin')

        try:
            self.doublegrid = bool(self.c['doublegrid'])
            if self.doublegrid:
                initGrid = read_init(self.c['resultsFolder'], self.c['spinFileName'], 'gridSpin')
                self.gridtrack = initGrid[1:]
                self.nodestocombine = self.c['nodestocombine']

        except:
            self.doublegrid = False
            print('you should add "doublegrid" to the json')


        ### set up the initial age and density of the firn column
        self.age        = initAge[1:]
        self.rho        = initDensity[1:]

        ### set up model grid
        self.z          = initDepth[1:]
        self.dz         = np.diff(self.z)
        self.dz         = np.append(self.dz, self.dz[-1])
        self.gridLen    = np.size(self.z)
        self.dx         = np.ones(self.gridLen)

        ### get temperature and accumulation rate from input csv file
        input_temp, input_year_temp = read_input(os.path.join(self.c['InputFileFolder'],self.c['InputFileNameTemp']))
        if input_temp[0] < 0.0:
            input_temp         = input_temp + K_TO_C
        input_temp[input_temp>T_MELT] = T_MELT

        input_bdot, input_year_bdot = read_input(os.path.join(self.c['InputFileFolder'],self.c['InputFileNamebdot']))

        try:
            if bool(self.c['MELT']):
                input_snowmelt, input_year_snowmelt = read_input(os.path.join(self.c['InputFileFolder'],self.c['InputFileNamemelt']))
                self.MELT             = True
                self.LWC             = np.zeros_like(self.z)
                print("Melt is initialized")
            else:
                self.MELT             = False
                print("No melt")
                input_snowmelt         = None
                input_year_snowmelt = None
                self.LWC             = np.zeros_like(self.z)

        except:
            self.MELT                 = False
            print("No melt; json does not include a melt field")
            input_snowmelt             = None
            input_year_snowmelt     = None
            self.LWC                 = np.zeros_like(self.z)

        #####################
        ### time ############
        # year to start and end, from the input file. If inputs have different start/finish, take only the overlapping times
        yr_start        = max(input_year_temp[0], input_year_bdot[0])   # start year
        yr_end          = min(input_year_temp[-1], input_year_bdot[-1]) # end year
        
        self.years      = np.ceil((yr_end - yr_start) * 1.0) 
        self.dt         = S_PER_YEAR / self.c['stpsPerYear']
        self.stp        = int(self.years * S_PER_YEAR/self.dt)       # total number of time steps, as integer

        # self.modeltime  = np.linspace(yr_start, yr_end, self.stp + 1)   # vector of time of each model step
        self.modeltime  = np.linspace(yr_start, yr_end, self.stp)
        self.t          = 1.0 / self.c['stpsPerYear']                   # years per time step
        #####################

        
        ###############################
        ### surface boundary conditions
        ### temperature, accumulation, melt, isotopes, surface density
        ###############################
        int_type            = self.c['int_type']
        print('Climate interpolation method is %s' %int_type)


        ### Temperature #####        
        Tsf                 = interpolate.interp1d(input_year_temp,input_temp,int_type,fill_value='extrapolate') # interpolation function
        self.Ts             = Tsf(self.modeltime) # surface temperature interpolated to model time
        # self.T_mean         = np.mean(self.Ts)
        if bool(self.c['SeasonalTcycle']): #impose seasonal temperature cycle of amplitude 'TAmp'
            # self.Ts         = self.Ts + self.c['TAmp'] * (np.cos(2 * np.pi * np.linspace(0, self.years, self.stp)) + 0.3 * np.cos(4 * np.pi * np.linspace(0, self.years, self.stp))) # Orsi
            self.Ts         = self.Ts - self.c['TAmp'] * (np.cos(2 * np.pi * np.linspace(0, self.years, self.stp))) # This is basic for Greenland (for Antarctica the it should be a plus instead of minus)
        #####################

        ### Accumulation ####
        bsf                 = interpolate.interp1d(input_year_bdot,input_bdot,int_type,fill_value='extrapolate') # interpolation function
        self.bdot             = bsf(self.modeltime)
        # self.bdotSec        = self.bdot / S_PER_YEAR / (self.stp / self.years) # accumulation rate in per second
        self.bdotSec           = self.bdot / S_PER_YEAR / self.c['stpsPerYear'] # accumulation for each time step (meters i.e. per second)
        self.iceout         = np.mean(self.bdot) # this is the rate of ice flow advecting out of the column, units m I.E. per year.
        self.w_firn         = np.mean(self.bdot) * RHO_I / self.rho 
        #####################
        
        ### Melt ############
        if self.MELT:
            ssf                 = interpolate.interp1d(input_year_snowmelt,input_snowmelt,int_type,fill_value='extrapolate')
            self.snowmelt         = ssf(self.modeltime)
            self.snowmeltSec    = self.snowmelt / S_PER_YEAR / self.c['stpsPerYear'] # melt for each time step (meters i.e. per second)
        #####################

        ### Isotopes ########
        if bool(self.c['isoDiff']):
            init_del_z            = read_init(self.c['resultsFolder'], self.c['spinFileName'], 'IsoSpin')
            try:
                input_iso, input_year_iso = read_input(self.c['InputFileNameIso'])
                self.del_s      = np.interp(self.modeltime, input_year_iso, input_iso)
                # del_s0 = input_iso[0]
            except:
                print('No external file for surface isotope values found, but you specified in the config file that isotope diffusion is on. The model will generate its own synthetic isotope data for you.')
                # del_s0 = -50.0
                ar1             = 0.9   # red noise memory coefficient
                std_rednoise     = 2    # red noise standard deviation
                self.del_s         = std_rednoise*np.random.randn(self.stp)    # white noise

                for x in range(1,self.stp):
                    self.del_s[x] = self.del_s[x-1]*ar1 + np.random.randn()  # create red noise from white

                self.del_s         = self.del_s - 50
                #impose seasonal isotope cycle
                # self.del_s     = self.del_s + 5 * (np.cos(2 * np.pi * np.linspace(0, self.years, self.stp )) + 0.3 * np.cos(4 * np.pi * np.linspace(0, self.years, self.stp )))
        #####################
 
         ### Surface Density #
        try:
            if bool(self.c['variable_srho']):
                if self.c['srho_type']=='userinput':
                    input_srho, input_year_srho = read_input(self.c['InputFileNamesrho'])
                    self.rhos0      = np.interp(self.modeltime, input_year_srho, input_srho)
                elif self.c['srho_type']=='param':
                    self.rhos0        = 481.0 + 4.834 * (self.Ts - T_MELT) # Kuipers Munneke, 2015
                elif self.c['srho_type']=='noise':
                    rho_stdv         = 100 # the standard deviation of the surface density (I made up 25)
                    self.rhos0      = np.random.normal(self.c['rhos0'], rho_stdv, self.stp)
                    self.rhos0[self.rhos0>600]=600
                    self.rhos0[self.rhos0<300]=300
                
                elif self.c['srho_type']=='reeh':
                    T_f = (self.Ts - K_TO_C)
                    self.rhos0 = 625.0 + 18.7*T_f + 0.293*T_f**2
                    #print(self.rhos0)
            else:
                self.rhos0      = self.c['rhos0'] * np.ones(self.stp)       # density at surface

        except:
            print("you should alter the json to include all variable surface rho fields")
            self.rhos0          = self.c['rhos0'] * np.ones(self.stp)       # density at surface
        #####################

        ### Layer tracker ###
        self.D_surf     = self.c['D_surf'] * np.ones(self.stp)      # layer traking routine (time vector). 
        self.Dcon       = self.c['D_surf'] * np.zeros(self.gridLen)  # layer tracking routine (initial depth vector)
        #####################

        ###############################
        ### set up vector of times data will be written
        Tind                 = np.nonzero(self.modeltime>=-25000)[0][0]
        # print('Caution: writing all data')
        self.TWrite         = self.modeltime[Tind::self.c['TWriteInt']]
        # self.TWrite         = np.append(self.modeltime[10],self.TWrite)
        # self.TWrite         = self.modeltime[-2::self.c['TWriteInt']]
        # self.TWrite_out     = self.TWrite
        TWlen               = len(self.TWrite) #- 1
        self.WTracker         = 1

        ### you can choose to write certain fields at different times.
        # Tind2                 = np.nonzero(self.modeltime>=1958.0)[0][0]
        # self.TWrite2         = self.modeltime[Tind2::self.c['TWriteInt']]
        # self.TWrite         = np.append(self.modeltime[10],self.TWrite)
        # self.TWrite2         = self.modeltime[0::self.c['TWriteInt']]
        # self.TWrite_out     = self.TWrite
        # TWlen2               = len(self.TWrite2) #- 1
        # self.WTracker2         = 1
        ###############################

        ### set up initial mass, stress, and mean accumulation rate
        self.mass           = self.rho * self.dz
        self.sigma          = (self.mass + self.LWC * RHO_W_KGM) * self.dx * GRAVITY
        self.sigma          = self.sigma.cumsum(axis = 0)
        self.mass_sum       = self.mass.cumsum(axis = 0)
        ### mean accumulation over the lifetime of the parcel:
        self.bdot_mean      = (np.concatenate(([self.mass_sum[0] / (RHO_I * S_PER_YEAR)], self.mass_sum[1:] / (self.age[1:] * RHO_I / self.t))))*self.c['stpsPerYear']*S_PER_YEAR
        ### It is the mass of the overlying firn divided by the age of the parcel.
        #######################

        ### set up longitudinal strain rate
        if bool(self.c['strain']):
            self.du_dx         = np.zeros(self.gridLen)
            self.du_dx[1:]     = self.c['du_dx']/(S_PER_YEAR)
        #######################
        #print(self.z)
        
        self.Tz             = initTemp[1:]
        self.T_mean         = np.mean(self.Tz[self.z<50])
        self.T10m           = self.T_mean

        self.compboxes         = len(self.z[self.z<80])
        #######################

        ### model outputs
        self.output_list     = self.c['outputs']
        print(self.output_list)
        if ((not self.MELT) and ('LWC' in self.output_list)):
            self.output_list.remove('LWC')
            print('removed LWC from output list (melt is not on)')
        if ((not bool(self.c['FirnAir'])) and ('gasses' in self.output_list)):
            self.output_list.remove('gasses')
            print('removed gasses from output list (firn air is not on)')            
        if 'density' in self.output_list:
            self.rho_out             = np.zeros((TWlen+1,len(self.dz)+1),dtype='float32')
            self.rho_out[0,:]       = np.append(self.modeltime[0], self.rho)
        if 'temperature' in self.output_list:
            self.Tz_out             = np.zeros((TWlen+1,len(self.dz)+1),dtype='float32')
            self.Tz_out[0,:]        = np.append(self.modeltime[0], self.Tz)
        if 'age' in self.output_list:
            self.age_out             = np.zeros((TWlen+1,len(self.dz)+1),dtype='float32')
            self.age_out[0,:]        = np.append(self.modeltime[0], self.age/S_PER_YEAR)
        if 'depth' in self.output_list:
            self.z_out                 = np.zeros((TWlen+1,len(self.dz)+1),dtype='float32')
            self.z_out[0,:]            = np.append(self.modeltime[0], self.z)
        if 'dcon' in self.output_list:
            self.D_out                 = np.zeros((TWlen+1,len(self.dz)+1),dtype='float32')
            self.D_out[0,:]            = np.append(self.modeltime[0], self.Dcon)
        if 'bdot_mean' in self.output_list:
            self.bdot_out             = np.zeros((TWlen+1,len(self.dz)+1),dtype='float32')
            self.bdot_out[0,:]        = np.append(self.modeltime[0], self.bdot_mean)
        if 'climate' in self.output_list:
            self.Clim_out             = np.zeros((TWlen+1,3),dtype='float32')
            self.Clim_out[0,:]        = np.append(self.modeltime[0], [self.bdot[0], self.Ts[0]])  # not sure if bdot or bdotSec
        if 'compaction' in self.output_list:
            self.crate_out             = np.zeros((TWlen+1,self.compboxes+1),dtype='float32')
            self.crate_out[0,:]        = np.append(self.modeltime[0], np.zeros(self.compboxes))
        if 'LWC' in self.output_list:
            self.LWC_out             = np.zeros((TWlen+1,len(self.dz)+1),dtype='float32')
            self.LWC_out[0,:]        = np.append(self.modeltime[0], self.LWC)
        try:
            print('rho_out size (MB):', self.rho_out.nbytes/1.0e6) # print the size of the output for reference
        except:
            pass
        #####################

        ### initial grain growth (if specified in config file)
        if bool(self.c['physGrain']):
            initr2                  = read_init(self.c['resultsFolder'], self.c['spinFileName'], 'r2Spin')
            self.r2                 = initr2[1:]
            r20                     = self.r2
            self.dr2_dt             = np.zeros_like(self.z)
            if 'grainsize' in self.output_list:
                self.r2_out         = np.zeros((TWlen+1,len(self.dz)+1),dtype='float32')
                self.r2_out[0,:]    = np.append(self.modeltime[0], self.r2)
                self.dr2_dt_out     = np.zeros((TWlen+1,len(self.dz)+1),dtype='float32')
                self.dr2_dt_out[0,:]= np.append(self.modeltime[0], self.dr2_dt)
            else:
                self.r2_out         = None
                self.dr2_dt_out        = None            
        else:            
            self.r2                 = None
            self.dr2_dt             = None
        #######################

        ### temperature history for Morris physics
        if self.c['physRho'] == 'Morris2014':
            self.THist              = True
            initHx                  = read_init(self.c['resultsFolder'], self.c['spinFileName'], 'HxSpin')
            self.Hx                 = initHx[1:]
            if 'temp_Hx' in self.output_list:
                self.Hx_out         = np.zeros((TWlen+1,len(self.dz)+1),dtype='float32')
                self.Hx_out[0,:]    = np.append(self.modeltime[0], self.Hx)
            else:
                self.Hx_out         = None
        else:
            self.THist              = False
        #####################    
        
        ### Isotopes ########
        if bool(self.c['isoDiff']):
            self.del_z              = init_del_z[1:]
            if 'isotopes' in self.output_list:
                self.iso_out        = np.zeros((TWlen+1,len(self.dz)+1),dtype='float32')
                self.iso_out[0,:]   = np.append(self.modeltime[0], self.del_z)
            else:
                self.iso_out        = None
        #######################

        ### DIP, DHdt, LIZ, BCO ###
        self.dHAll       = []
        bcoAgeMart, bcoDepMart, bcoAge830, bcoDep830, LIZAgeMart, LIZDepMart, bcoAge815, bcoDep815     = self.update_BCO()
        intPhi, intPhi_c = self.update_DIP()
        
        self.dHAll.append(0)
        dHOut     = 0 # surface elevation change since last time step
        dHOutC     = 0 # cumulative surface elevation change since start of model run

        if 'DIP' in self.output_list:
            self.DIP_out         = np.zeros((TWlen+1,4),dtype='float32')   
            self.DIP_out[0,:]    = np.append(self.modeltime[0], [intPhi, dHOut, dHOutC])
            self.DIPc_out         = np.zeros((TWlen+1,len(self.dz)+1),dtype='float32')
            self.DIPc_out[0,:]    = np.append(self.modeltime[0], intPhi_c)
        if 'BCO' in self.output_list:
            self.BCO_out         = np.zeros((TWlen+1,9),dtype='float32')
            self.BCO_out[0,:]    = np.append(self.modeltime[0], [bcoAgeMart, bcoDepMart, bcoAge830, bcoDep830, LIZAgeMart, LIZDepMart, bcoAge815, bcoDep815])
        #####################

        ##### Firn Air ######
        ### each gas of interest gets its own instance of the class
        if bool(self.c['FirnAir']):
            print('Firn air initialized')
            with open(self.c['AirConfigName'], "r") as f:
                jsonString         = f.read()
                self.cg         = json.loads(jsonString)
            self.FA = {}
            self.gas_out = {}
            self.Gz = {}
            for gas in self.cg['gaschoice']:
                self.FA[gas] = FirnAir(self.cg,input_year_temp,self.z, self.modeltime, self.Tz, self.rho, self.dz, gas)
                if "gasses" in self.cg['outputs']:
                    self.gas_out[gas]             = np.zeros((TWlen+1,len(self.dz)+1),dtype='float32')
                    self.gas_out[gas][0,:]        = np.append(self.modeltime[0], np.ones_like(self.rho))
            if "diffusivity" in self.cg['outputs']:
                self.diffu_out             = np.zeros((TWlen+1,len(self.dz)+1),dtype='float32')
                self.diffu_out[0,:]        = np.append(self.modeltime[0], np.ones_like(self.rho))
            if "advection_rate" in self.cg['outputs']:
                self.w_air_out             = np.zeros((TWlen+1,len(self.dz)+1),dtype='float32')
                self.w_air_out[0,:]        = np.append(self.modeltime[0], np.ones_like(self.rho))                
                self.w_firn_out         = np.zeros((TWlen+1,len(self.dz)+1),dtype='float32')
                self.w_firn_out[0,:]    = np.append(self.modeltime[0], np.ones_like(self.rho))
        #####################

    ####################    
    ##### END INIT #####
    ####################

    def time_evolve(self):
        '''
        Evolve the spatial grid, time grid, accumulation rate, age, density, mass, stress, temperature, and diffusivity through time
        based on the user specified number of timesteps in the model run. Updates the firn density using a user specified 
        '''
        self.steps = 1 / self.t # steps per year
        start_time=time.time() # this is a timer to keep track of how long the model run takes.
        
        ####################################
        ##### START TIME-STEPPING LOOP #####
        ####################################
        
        for iii in range(self.stp):
            mtime = self.modeltime[iii]
            # print(iii,mtime)
            self.D_surf[iii] = iii
            ### dictionary of the parameters that get passed to physics
            PhysParams = {
                'iii':          iii,
                'steps':        self.steps,
                'gridLen':      self.gridLen,
                'bdotSec':      self.bdotSec,
                'bdot_mean':    self.bdot_mean,
                'bdot_type':    self.c['bdot_type'],
                'Tz':           self.Tz,
                'T_mean':       self.T_mean,
                'T10m':         self.T10m,
                'rho':          self.rho,
                'mass':         self.mass,
                'sigma':        self.sigma,
                'dt':           self.dt,
                'Ts':           self.Ts,
                'r2':           self.r2,
                'age':          self.age,
                'physGrain':    bool(self.c['physGrain']),
                'calcGrainSize': bool(self.c['calcGrainSize']),
                'r2s0':         self.c['r2s0'],
                'GrGrowPhysics':self.c['GrGrowPhysics'],
                'z':            self.z,
                'rhos0':        self.rhos0[iii],
                'dz':           self.dz,
                'LWC':            self.LWC,
                'MELT':         bool(self.MELT),
            }
            
            if self.THist: #add Hx to dictionary if physics is Morris
                PhysParams['Hx']=self.Hx

            ### choose densification-physics based on user input
            physicsd = {
                'HLdynamic':            FirnPhysics(PhysParams).HL_dynamic,
                'HLSigfus':             FirnPhysics(PhysParams).HL_Sigfus,
                'Barnola1991':          FirnPhysics(PhysParams).Barnola_1991,
                'Li2004':               FirnPhysics(PhysParams).Li_2004,
                'Li2011':               FirnPhysics(PhysParams).Li_2011,
                'Ligtenberg2011':       FirnPhysics(PhysParams).Ligtenberg_2011,
                'Arthern2010S':         FirnPhysics(PhysParams).Arthern_2010S,
                'Simonsen2013':         FirnPhysics(PhysParams).Simonsen_2013,
                'Morris2014':           FirnPhysics(PhysParams).Morris_HL_2014,
                'Helsen2008':           FirnPhysics(PhysParams).Helsen_2008,
                'Arthern2010T':         FirnPhysics(PhysParams).Arthern_2010T,
                'Goujon2003':           FirnPhysics(PhysParams).Goujon_2003,
                'KuipersMunneke2015':   FirnPhysics(PhysParams).KuipersMunneke_2015,
                'Crocus':               FirnPhysics(PhysParams).Crocus
            }

            RD         = physicsd[self.c['physRho']]()
            drho_dt = RD['drho_dt']

            ### update density and age of firn
            self.rho_old    = np.copy(self.rho)
            #print('-----nospin run------')
            #print('dt ', self.dt)
            #print('drho_dt ',drho_dt)
            self.rho         = self.rho + self.dt * drho_dt
            self.dz_old     = np.copy(self.dz) # model volume thicknesses before the compaction
            self.sdz_old     = np.sum(self.dz) # old total column thickness
            self.z_old         = np.copy(self.z)
            self.dz         = self.mass / self.rho * self.dx # new dz after compaction
            
            if self.THist:
                self.Hx     = FirnPhysics(PhysParams).THistory()

            if (self.MELT and self.snowmeltSec[iii]>0): #i.e. there is melt               
                self.rho, self.age, self.dz, self.Tz, self.z, self.mass, self.dzn, self.LWC = percolation_bucket(self,iii)
            else: # no melt, dz after compaction
                self.dzn     = self.dz[0:self.compboxes]

            ### heat diffusion
            if (bool(self.c['heatDiff']) and not self.MELT): # no melt, so use regular heat diffusion
                #print('----Evolving nospin------')
                #print(self.rho)
                self.Tz, self.T10m     = heatDiff(self,iii)
            elif (bool(self.c['heatDiff']) and self.MELT): # there is melt, so use enthalpy method
                self.Tz, self.T10m, self.rho, self.mass, self.LWC = enthalpyDiff(self,iii)
            else: # no heat diffusion, so just set the temperature of the new box on top.
                # self.Tz     = np.concatenate(([self.Ts[iii]], self.Tz[:-1]))
                pass # box gets added below

            self.T_mean     = np.mean(self.Tz[self.z<50])
            
            if bool(self.c['FirnAir']): # Update firn air
                AirParams = {
                    'Tz':           self.Tz,
                    'rho':          self.rho,
                    'dt':           self.dt,
                    'z':            self.z,
                    'rhos0':        self.rhos0[iii],
                    'dz_old':        self.dz_old,
                    'dz':           self.dz,
                    'rho_old':        self.rho_old,
                    'w_firn':        self.w_firn
                }
                for gas in self.cg['gaschoice']:        
                    self.Gz[gas], self.diffu, w_p     = self.FA[gas].firn_air_diffusion(AirParams,iii)

            if bool(self.c['isoDiff']): # Update isotopes
                self.del_z     = isoDiff(self,iii)
                ### new box gets added on within isoDiff function
                
            if bool(self.c['strain']): #update horizontal strain
                self.dz     = ((-self.du_dx)*self.dt + 1)*self.dz
                self.mass     = self.mass*((-self.du_dx)*self.dt + 1)

            self.sdz_new     = np.sum(self.dz) #total column thickness after densification, melt, horizontal strain,  before new snow added

            ### Dcon: user-specific code goes here. 
            # self.Dcon[self.LWC>0] = self.Dcon[self.LWC>0] + 1 # for example, keep track of how many times steps the layer has had water
            
            ### update model grid, mass, stress, and mean accumulation rate
            if self.bdotSec[iii]>0: # there is accumulation at this time step
            # MS 2/10/17: should double check that everything occurs in correct order in time step (e.g. adding new box on, calculating dz, etc.)                 
                self.age         = np.concatenate(([0], self.age[:-1])) + self.dt                     
                self.dzNew         = self.bdotSec[iii] * RHO_I / self.rhos0[iii] * S_PER_YEAR
                self.dz         = np.concatenate(([self.dzNew], self.dz[:-1]))
                self.z             = self.dz.cumsum(axis = 0)
                znew = np.copy(self.z) 
                self.z             = np.concatenate(([0], self.z[:-1]))
                self.rho          = np.concatenate(([self.rhos0[iii]], self.rho[:-1]))
                self.LWC         = np.concatenate(([0], self.LWC[:-1]))
                self.Tz         = np.concatenate(([self.Ts[iii]], self.Tz[:-1]))
                self.Dcon        = np.concatenate(([self.D_surf[iii]], self.Dcon[:-1]))
                massNew         = self.bdotSec[iii] * S_PER_YEAR * RHO_I
                self.mass         = np.concatenate(([massNew], self.mass[:-1]))
                self.compaction = np.append(0,(self.dz_old[0:self.compboxes-1]-self.dzn[0:self.compboxes-1]))#/self.dt*S_PER_YEAR)
                if self.doublegrid:
                    self.gridtrack = np.concatenate(([1],self.gridtrack[:-1]))

            else: # no accumulation during this time step
                self.age         = self.age + self.dt
                self.z             = self.dz.cumsum(axis=0)
                znew = np.copy(self.z)
                self.z             = self.z - self.z[0] # shift so zero still on top
                self.compaction    = (self.dz_old[0:self.compboxes]-self.dzn)#/self.dt*S_PER_YEAR

            self.w_firn = (znew - self.z_old) / self.dt # advection rate of the firn, m/s
            # if ((iii>500) & (iii<510)):
            #     print(iii)
            #     bb=((self.z>60) & (self.z<80))
            #     print('w_firn',w_firn[bb])
            # i_zrate = np.where(self.z>=60)[0][0]
            # zrate = self.z[i_zrate+1]-self.z[i_zrate]
            # print(zrate)

            ### find the compaction rate
            ### this should all be old (11/28/17)
            # zdiffnew         = (self.z[1:]-self.z[1])
            # zdiffold         = (self.z_old[0:-1]-self.z_old[0])

            # zdn             = self.z[1:]
            # zdo             = self.z_old[0:-1]
            # self.strain     = np.cumsum(zdo-zdn)
            # self.tstrain     = np.sum(zdo-zdn)
            # self.compaction=np.append((zdiffold-zdiffnew)/self.dt*S_PER_YEAR,self.tstrain) #this is cumulative compaction rate in m/yr from 0 to the node specified in depth
            # if not self.snowmeltSec[iii]>0:
            # self.compaction=np.append(0,np.cumsum((self.dz_old[0:compboxes]-self.dz[1:compboxes+1])/self.dt*S_PER_YEAR))

            self.sigma         = (self.mass + self.LWC * RHO_W_KGM) * self.dx * GRAVITY
            self.sigma         = self.sigma.cumsum(axis = 0)
            self.mass_sum      = self.mass.cumsum(axis = 0)
            
            self.bdot_mean     = (np.concatenate(([self.mass_sum[0] / (RHO_I * S_PER_YEAR)], self.mass_sum[1:] * self.t / (self.age[1:] * RHO_I))))*self.c['stpsPerYear']*S_PER_YEAR
            
            if bool(self.c['physGrain']): # update grain radius
                self.r2, self.dr2_dt     = FirnPhysics(PhysParams).grainGrowth()

            ### write results as often as specified in the init method
            if mtime in self.TWrite:                
                ind         = np.where(self.TWrite == mtime)[0][0]
                mtime_plus1 = self.TWrite[ind] 

                if 'density' in self.output_list:
                    self.rho_out[self.WTracker,:]     = np.append(mtime_plus1, self.rho)
                if 'temperature' in self.output_list:
                    self.Tz_out[self.WTracker,:]       = np.append(mtime_plus1, self.Tz)
                if 'age' in self.output_list:
                    self.age_out[self.WTracker,:]      = np.append(mtime_plus1, self.age/S_PER_YEAR)
                if 'depth' in self.output_list:
                    self.z_out[self.WTracker,:]        = np.append(mtime_plus1, self.z)
                if 'dcon' in self.output_list:    
                    self.D_out[self.WTracker,:]     = np.append(mtime_plus1, self.Dcon)
                if 'climate' in self.output_list:   
                    self.Clim_out[self.WTracker,:]     = np.append(mtime_plus1, [self.bdot[int(iii)], self.Ts[int(iii)]])
                if 'bdot_mean' in self.output_list:   
                    self.bdot_out[self.WTracker,:]     = np.append(mtime_plus1, self.bdot_mean)
                if 'compaction' in self.output_list:    
                    self.crate_out[self.WTracker,:] = np.append(mtime_plus1, self.compaction)
                if 'LWC' in self.output_list:
                    self.LWC_out[self.WTracker,:]     = np.append(mtime_plus1, self.LWC)
                if 'grainsize' in self.output_list:
                    self.r2_out[self.WTracker,:]     = np.append(mtime_plus1, self.r2)
                    self.dr2_dt_out[self.WTracker,:]= np.append(mtime_plus1, self.dr2_dt)
                if 'temp_Hx' in self.output_list:
                    self.Hx_out[self.WTracker,:]     = np.append(mtime_plus1, self.Hx)
                if 'isotopes' in self.output_list:
                    self.iso_out[self.WTracker,:]     = np.append(mtime_plus1, self.del_z)
                if bool(self.c['FirnAir']):
                    if "gasses" in self.cg['outputs']:
                        for gas in self.cg['gaschoice']:                        
                            self.gas_out[gas][self.WTracker,:]     = np.append(mtime_plus1, self.Gz[gas])
                    if "diffusivity" in self.cg['outputs']:
                        self.diffu_out[self.WTracker,:] = np.append(mtime_plus1, self.diffu)
                    if "advection_rate" in self.cg['outputs']:
                        self.w_air_out[self.WTracker,:] = np.append(mtime_plus1, w_p)
                        self.w_firn_out[self.WTracker,:] = np.append(mtime_plus1, self.w_firn)

                # self.WTracker = self.WTracker + 1

            # if mtime in self.TWrite2:                
                # ind         = np.where(self.TWrite2 == mtime)[0][0]
                # mtime_plus1 = self.TWrite2[ind] 

                bcoAgeMart, bcoDepMart, bcoAge830, bcoDep830, LIZAgeMart, LIZDepMart, bcoAge815, bcoDep815     = self.update_BCO()
                intPhi, intPhi_c         = self.update_DIP()
                dH, dHtot                 = self.update_dH()

                if 'BCO' in self.output_list:
                    self.BCO_out[self.WTracker,:]       = np.append(mtime_plus1, [bcoAgeMart, bcoDepMart, bcoAge830, bcoDep830, LIZAgeMart, LIZDepMart, bcoAge815, bcoDep815])                    
                if 'DIP' in self.output_list:
                    self.DIP_out[self.WTracker,:]       = np.append(mtime_plus1, [intPhi, dH, dHtot])
                    self.DIPc_out[self.WTracker,:]         = np.append(mtime_plus1, intPhi_c)

                self.WTracker = self.WTracker + 1

            if self.doublegrid:
                if self.gridtrack[-1]==2:
                    # print('regridding now at ', iii)
                    self.dz, self.z, self.rho, self.Tz, self.mass, self.sigma, self. mass_sum, self.age, self.bdot_mean, self.LWC, self.gridtrack, self.r2 = regrid(self)
                    if iii<100:
                        tdep = np.where(self.gridtrack==1)[0][-1]
                        print('transition at:', self.z[tdep])

        ##################################
        ##### END TIME-STEPPING LOOP #####
        ##################################

        write_nospin_hdf5(self)

    ###########################
    ##### END time_evolve #####
    ###########################

    def update_BCO(self):
        '''
        Updates the bubble close-off depth and age based on the Martinerie criteria as well as through assuming the critical density is 815 kg/m^3
        '''
        try:
            bcoMartRho     = 1 / (1 / (917.0) + self.T10m * 6.95E-7 - 4.3e-5)  # Martinerie density at close off; see Buizert thesis (2011), Blunier & Schwander (2000), Goujon (2003)
            bcoAgeMart     = min(self.age[self.rho >= bcoMartRho]) / S_PER_YEAR  # close-off age from Martinerie
            bcoDepMart     = min(self.z[self.rho >= (bcoMartRho)])

            # bubble close-off age and depth assuming rho_crit = 815kg/m^3
            bcoAge830     = min(self.age[self.rho >= 830.0]) / S_PER_YEAR  # close-off age where rho = 815 kg m^-3
            bcoDep830     = min(self.z[self.rho >= 830.0])
            bcoAge815     = min(self.age[self.rho >= (RHO_2)]) / S_PER_YEAR  # close-off age where rho = 815 kg m^-3
            bcoDep815     = min(self.z[self.rho >= (RHO_2)])

            bcoMartRho = 1 / (1 / (917.0) + self.T10m * 6.95E-7 - 4.3e-5) # Martinerie density at close off; see Buizert thesis (2011), Blunier & Schwander (2000), Goujon (2003)
            LIZMartRho = bcoMartRho - 14.0  # LIZ depth (Blunier and Schwander, 2000)
            LIZAgeMart = min(self.age[self.rho > LIZMartRho]) / S_PER_YEAR  # lock-in age
            LIZDepMart = min(self.z[self.rho >= (LIZMartRho)])  # lock in depth

        except:
            
            bcoAgeMart     = -9999
            bcoDepMart     = -9999
            bcoAge830     = -9999
            bcoDep830     = -9999

            LIZDepMart     = -9999
            LIZAgeMart     = -9999
            bcoAge815     = -9999
            bcoDep815     = -9999

            
        return bcoAgeMart, bcoDepMart, bcoAge830, bcoDep830, LIZAgeMart, LIZDepMart, bcoAge815, bcoDep815

    ### end update_BCO ########
    ###########################

    def update_DIP(self):
        '''
        Updates the depth-integrated porosity
        '''

        bcoMartRho = 1 / (1 / (917.0) + self.T10m * 6.95E-7 - 4.3e-5) # Martinerie density at close off; see Buizert thesis (2011), Blunier & Schwander (2000), Goujon (2003)
        phi = 1 - self.rho / RHO_I  # total porosity
        phi[phi <= 0] = 1e-16
        phiC = 1 - bcoMartRho / RHO_I;  # porosity at close off
        phiClosed = 0.37 * phi * (phi / phiC) ** -7.6  # Closed porosity, from Goujon. See Buizert thesis (eq. 2.3) as well

        phiOpen = phi - phiClosed  # open porosity
        phiOpen[phiOpen <= 0] = 1.e-10  # don't want negative porosity.

        intPhi = np.sum(phi * self.dz)  # depth-integrated porosity
        intPhi_c = np.cumsum(phi * self.dz)
        # self.intPhiAll.append(intPhi)

        return intPhi, intPhi_c
    ### end update_DIP ########
    ###########################

    def update_dH(self):
        '''
        updates the surface elevation change
        '''

        # self.dH = (self.sdz_new-self.sdz_old)+self.dzNew-(self.bdot_mean[0]*S_PER_YEAR) #
        
        # self.dH = (self.sdz_new-self.sdz_old)+self.dzNew-(self.iceout/(self.rho_old[-1]/RHO_I))*self.t #

        self.dH = (self.sdz_new - self.sdz_old) + self.dzNew - (self.iceout*self.t) # iceout has units m ice/year, t is years per time step. 

        self.dHAll.append(self.dH)

        self.dHtot = np.sum(self.dHAll)

        # self.dHOut.append(self.dH)
        # self.dHOutC.append(self.dHtot)

        return self.dH, self.dHtot

    ###########################

