# -*- coding: utf-8 -*-

import matplotlib.pyplot as plt 
import h5py as h5
import os
import numpy as np
import scipy as sp
import pickle
import csv
import matplotlib.gridspec as gridspec
import pandas as pd
from sklearn import linear_model
import csv

def dipTrendToFile(site, coords):
    # always there: models
    models = ["HLdynamic","HLSigfus","Li2011","Helsen2008","Arthern2010S","Goujon2003","Barnola1991","KuipersMunneke2015",'Simonsen2013', 'Crocus', 'Arthern2010T'] 
    
    # create hdf5 - File
    with h5.File('./CFMauto/diptrends'+str(site)+'.hdf5', 'w') as hf:
        try: 
            hf["coords"].resize((hf["coords"].shape[0] + coords.shape[0]), axis = 0)
            hf["coords"][-coords.shape[0]:] = coords
        except:
            hf.create_dataset('coords',data = coords) #TODO: maxshape
    
    
        for m in models:
            rfolder = 'CFMexperimentsInput2'
            rfile='CFM_'+site+'_results_'+m+'.hdf5'
                
            fn = os.path.join(rfolder,rfile)
                    
            try:
                f = h5.File(fn,'r')
            except:
                continue
        
            time = f['DIP'][1:,0]
            dip = f['DIP'][1:,1]
            
            diptrend = [findDIPtrend(time, dip)]
            
            try: 
                hf[m].resize((hf[m].shape[0] + 1), axis = 0)
                hf[m][-1:] = diptrend
            except:
                hf.create_dataset(m, data = diptrend)

        try:
            t6 = hf['time']
        except:
            hf.create_dataset('time', data = time)
            
        hf.close()
        
def dipTrendToCSV(site, coords,csvName='diptrendsAuto', rfolder = 'CFMauto'):
    
    # always there: models
    models = ["HLdynamic","HLSigfus","Li2011","Helsen2008","Arthern2010S","Goujon2003","Barnola1991","KuipersMunneke2015","Simonsen2013", "Crocus","Arthern2010T"] 
    #csvName = csvName+'_'+site
    diptrendModels = [np.nan]*(len(models))
    
    for m in models:
        rfile='CFM_'+site+'_results_'+m+'.hdf5'
                
        fn = os.path.join(rfolder,rfile)
        
        i=models.index(m)
        
        try:
            f = h5.File(fn,'r')
            time = f['DIP'][1:,0]
            dip = f['DIP'][1:,1]
            diptrendModels[i] = findDIPtrend(time, dip)
        except:
            diptrendModels[i] = np.nan

    coords.extend(diptrendModels)
    
    with open(os.path.join(rfolder, csvName+'.csv'), 'a') as f:
        writer = csv.writer(f)
        writer.writerow(coords)
    


def findDIPtrend(time, dip):
    t = time.reshape(-1,1)
    
    dip_norm = [((d - dip.mean()) / (dip.max() - dip.min())) for d in dip]
    
    regr = linear_model.LinearRegression()
    try:
        regr.fit(t, dip_norm)
        diptrend = regr.coef_[0]
    except:
        diptrend = np.nan
    return diptrend