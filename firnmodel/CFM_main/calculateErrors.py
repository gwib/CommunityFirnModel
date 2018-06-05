# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
import h5py as h5

def prepareObsAndModel(obsFile, modelFile):
    
    # observation profile
    obsProfile = pd.read_csv(obsFile)
    
    if len(obsProfile.columns)!=2:
        obsProfile = pd.read_csv(obsFile, delimiter='\t')
    
    f = h5.File(modelFile,'r')

    modelDepth = f['depth'][-1,1:]
    modelDensity = f['density'][-1,1:]    
    
    modelProfile = pd.DataFrame()
    modelProfile['Depth [m]'] = modelDepth
    modelProfile['modelDensity [kg/m3]'] = modelDensity
    
    modelProfile = pd.DataFrame()
    modelProfile['Depth [m]'] = modelDepth
    modelProfile['modelDensity [kg/m3]'] = modelDensity
    modelProfile = modelProfile[modelProfile['Depth [m]'] < max(obsProfile['Depth [m]']) ]
    
    merge = pd.merge(modelProfile, obsProfile, on='Depth [m]', how='outer')
    merge = merge.sort_values('Depth [m]')
    merge = merge.interpolate() # fill missing values by linear interpolation
    
    return merge




def compute_error(trues, predicted):
    corr = np.corrcoef(predicted, trues)[0,1]
    mae = np.mean(np.abs(predicted - trues))
    rae = np.sum(np.abs(predicted - trues)) / np.sum(np.abs(trues - np.mean(trues)))
    rmse = np.sqrt(np.mean((predicted - trues)**2))
    r2 = max(0, 1 - np.sum((trues-predicted)**2) / np.sum((trues - np.mean(trues))**2))
    return corr, mae, rae, rmse, r2