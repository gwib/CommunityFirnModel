import matplotlib.pyplot as plt 
import h5py as h5
import os
import sys
import numpy as np
import scipy as sp
import pickle
import csv
import matplotlib.gridspec as gridspec

def densityPlotSpin(rfolder,rfile):

    '''
    Plot results from the CFM Spin
    '''
    fn = os.path.join(rfolder,rfile)

    f = h5.File(fn,'r')

    # Plot resultsf rom spin run
    age = f['ageSpin'][1:]
    rhoSpin = f['densitySpin'][1:]

# =============================================================================
#     depth = f['depth'][1:,1:]
#     density = f['density'][1:,1:]
#     temperature = f['temperature'][1:,1:]
#     # air = f['gasses'][:,1:]
# =============================================================================

    # time-density plot
    
    f2 = plt.figure()
    ax2 = f2.add_subplot(111)
    plt.plot(age,rhoSpin)
    plt.title('Spin results for the whole spin period')
    #TODO: insert units
    plt.xlabel('age/time')
    plt.ylabel('Density')
    plt.show()




# plot DIP in the first 100 years in the "official run"
def dip100(rfolder,rfile):
    
    fn = os.path.join(rfolder,rfile)

    f = h5.File(fn,'r')

    # Plot resultsf rom spin run
    time = f['DIP'][1:,0]
    dip = f['DIP'][1:,1]
    
    first = 100#int(len(dip)/3)

# =============================================================================
#     depth = f['depth'][1:,1:]
#     density = f['density'][1:,1:]
#     temperature = f['temperature'][1:,1:]
#     # air = f['gasses'][:,1:]
# =============================================================================

    # tim-density plot
    plt.figure()
    plt.plot(time[:first],dip[:first])
    plt.title(rfile.replace('.hdf5', '')+'\n DIP evolvement for the first '+ str(first)+ ' iterations')
    #TODO: insert units
    plt.xlabel('time []')
    plt.ylabel('DIP [«]')
    plt.show()
    
    
    f2 = plt.figure()
    ax2 = f2.add_subplot(111)
    plt.plot(time,dip)
    plt.title(rfile.replace('.hdf5', '')+'\nDIP evolvement for the whole period')
    #TODO: insert units
    plt.xlabel('Time')
    plt.ylabel('DIP')
    plt.show()
    
    
modelColors = {}
models = ["HLdynamic","HLSigfus","Li2011","Helsen2008","Arthern2010S","Goujon2003","Barnola1991","KuipersMunneke2015",'Simonsen2013'] # TODO: "Crocus", ,"Arthern2010T","Spencer2001","Morris2014",



import random

random.seed(200)

def get_random_color(pastel_factor = 0.5):
    return [(x+pastel_factor)/(1.0+pastel_factor) for x in [random.uniform(0,1.0) for i in [1,2,3]]]

def color_distance(c1,c2):
    return sum([abs(x[0]-x[1]) for x in zip(c1,c2)])

def generate_new_color(existing_colors,pastel_factor = 0.5):
    max_distance = None
    best_color = None
    for i in range(0,100):
        color = get_random_color(pastel_factor = pastel_factor)
        if not existing_colors:
            return color
        best_distance = min([color_distance(color,c) for c in existing_colors])
        if not max_distance or best_distance > max_distance:
            max_distance = best_distance
            best_color = color
    return best_color

for m in models:
    modelColors[m] = generate_new_color(list(modelColors.values()))


#from itertools import cycle
#
#cycol = cycle('bgrcmk')
#
#for m in models:
#    modelColors[m]=next(cycol)
    
experiments = ['exp'+str(x) for x in range(1,7)]

def plotDIPForExperiments(rfolder = 'CFMexperiments'):
    
    for e in experiments:
        plt.figure()
        for m in models:
            rfile = 'CFM'+e+"results"+m+".hdf5"
        
            fn = os.path.join(rfolder,rfile)
        
            f = h5.File(fn,'r')
        
            # Plot resultsf rom spin run
            time = f['DIP'][1:,0]
            dip = f['DIP'][1:,1]
            
            plt.plot(time,dip, c=modelColors[m], label=m)
        
            plt.title(e)
            plt.xlabel('Time')
            plt.ylabel('DIP')
            plt.legend()
            plt.show()
    

def plotAllFun(rfolder='CFMexperiments', infolder='CFMexp2'):
    for e in experiments:
        if e in ['exp1', 'exp2', 'exp3']:
            bDotFile = 'bDot_const.csv'
            tskinFile = 'tskin_'+e+'.csv'
        
        else:
            bDotFile = 'bDot_'+e+'.csv'
            tskinFile = 'tskin_const.csv'
            
        fnbDot = os.path.join(infolder,bDotFile)
        fntskin = os.path.join(infolder, tskinFile)
        
        bdotfile = open(fnbDot)
        tempfile = open(fntskin)
        
        readBdot = csv.reader(bdotfile, delimiter=',')
        bDotData = [r for r in readBdot]
        
        readTemp = csv.reader(tempfile, delimiter=',')
        tempData = [r for r in readTemp]
        
        timeData = [float(time) for time in tempData[0]]
        
        temp = [float(t) for t in tempData[1]]
        bDot = [float(bdot) for bdot in bDotData[1]]
        
        bdotfile.close()
        tempfile.close()
        
        plt.figure()
        gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1]) 
        for m in models:
            
            rfile = 'CFM'+e+"results"+m+".hdf5"
        
            fn = os.path.join(rfolder,rfile)
        
            f = h5.File(fn,'r')
        
            # Plot resultsf rom spin run
            time = f['DIP'][1:,0]
            dip = f['DIP'][1:,1]
            
            ax0 = plt.subplot(gs[0])
            ax0.plot(time,dip, c=modelColors[m], label=m)
            ax0.legend()
            
            
        ax2 = plt.subplot(gs[1])
        ax3 = ax2.twinx()
        
        ax2.plot(timeData, temp, 'peru')
        ax2.set_xlabel('time (s)')
        ax2.tick_params(color='peru')
        ax2.set_ylabel('Temperature [°C]', color='peru')
        
        ax3.plot(timeData, bDot, 'blue')
        ax3.tick_params(color='blue')
        ax3.set_ylabel('Surface mass balance [m/a]', color='blue')
        
        
        plt.show()
            
            
            
# =============================================================================
#             plt.subplot(311)
#             plt.plot(time,dip, c=modelColors[m], label=m)
#         
#             plt.title(e)
#             plt.ylabel('DIP')
#             plt.legend()
#             
#         
#         fig, ax1 = plt.subplots()
#         t = timeData
#         ax1.plot(t, bDot)
#         ax1.set_xlabel('time (s)')
#         ax1.set_ylabel('bDot')
#         
#         ax2 = ax1.twinx()
#         ax2.plot(t, temp)
#         ax2.set_ylabel('Temperature [°C]', color='r')
#         
#         fig.tight_layout()
#         plt.show()
#         
#         
#         
#         plt.subplot(312)
#         plt.plot(timeData, temp)
#         plt.ylabel('Temperature [°C]')
#         plt.title('Temperature evolvement in experiment '+e)
#             
#         plt.subplot(313)
#         plt.title('Surface mass balance in experiment '+e)
#         plt.plot(timeData, bDot)
#         plt.ylabel('smb []')
#         plt.xlabel('Time')
#         plt.subplots_adjust(hspace=0.5)
#         plt.show()
# =============================================================================
