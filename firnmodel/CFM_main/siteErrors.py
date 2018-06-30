
# coding: utf-8

# In[1]:


import numpy as np
import pandas as pd
import h5py as h5
import os
from plotDrhoDt import modelColors,mnames
import matplotlib.pyplot as plt


# In[2]:


obsFiles = {'site1': '46Density.tsv', 'site2': 'B26_2011.csv', 'site3': 'NEEM2007shallowcoreDensity.txt'}
rfolder = './CFMexperimentsInput2/'
models = ["HLdynamic","HLSigfus","Li2011","Helsen2008","Arthern2010S","Barnola1991","KuipersMunneke2015","Simonsen2013", "Crocus","Arthern2010T"]
sites = ['site'+str(x) for x in range(1,4)]


# In[3]:


merge = {}
#merge1 = {}
def prepareObsAndModel():

    for s in sites:
        # observation profile
        obsFile = os.path.join('obsProfiles', obsFiles[s])
        obsProfile = pd.read_csv(obsFile)
        
        if s == 'site1': 
            obsTime = 2006.5
        elif s == 'site2':
            obsTime = 2011.5
        elif s=='site3':
             obsTime = 2007.5
        
    
        if len(obsProfile.columns)!=2:
            obsProfile = pd.read_csv(obsFile, delimiter='\t')
        #print(obsProfile.head())
        #modelProfile = {}
        merge[s] = pd.DataFrame()
        i = 1
        for m in models:
            
            rfile='CFM_'+s+'_results_'+m+'.hdf5'

            fn = os.path.join(rfolder,rfile)

            try:
                
                f = h5.File(fn,'r')
                
                # make sure the profile is coming from the right time
                time = list(f['depth'][:,0])
                #print(time)

                timeIndex = time.index(obsTime)
                modelDepth = f['depth'][timeIndex,1:]
                #print(modelDepth)
                modelDensity = f['density'][timeIndex,1:]    
                #print(modelDensity)
                modelProfile = pd.DataFrame()
                modelProfile['Depth [m]'] = modelDepth
                modelProfile[m+'Density [kg/m3]'] = modelDensity

                modelProfile = modelProfile[modelProfile['Depth [m]'] < max(obsProfile['Depth [m]']) ]
        
            except:
                continue
            
            if i==1:
                merge[s] = pd.merge(obsProfile, modelProfile, on='Depth [m]', how='outer')
                #merge[s] = merge1.copy()
            else:
                merge[s] = pd.merge(modelProfile, merge[s], on='Depth [m]', how='outer')
            
            i = i+1
            #print(merge)
        merge[s] = merge[s].sort_values(by='Depth [m]')
        merge[s] = merge[s].interpolate(pad=3) # fill missing values by linear interpolation
        #print(merge[s])
        merge[s] = merge[s][np.isfinite(merge[s]['Density [kg/m3]'])]
    return merge


# In[4]:


def compute_error(trues, predicted):
    mae = round(np.mean(np.abs(predicted - trues)),3)
    rmse = round(np.sqrt(np.mean((predicted - trues)**2)),3)
    return mae, rmse


# In[5]:


me= prepareObsAndModel()


# In[6]:


def plot(dfDict):
    for s in sites:
        sProfileName = obsFiles[s].replace('.csv', '').replace('.txt','').replace('.tsv','')
        
        df = dfDict[s]
        
        obsDepth = df['Depth [m]']
        obsDensity = df['Density [kg/m3]']
        
        plt.figure()
        plt.gca().invert_yaxis()
        
        plt.step(obsDensity, obsDepth, label='Observation', c='black')

        for m in models:
            try: modelDensity = df[m+'Density [kg/m3]']
            except: continue

            plt.step(modelDensity,obsDepth, c=modelColors[m], label=mnames[m], linewidth=0.6)

        plt.legend(fontsize=8)
        plt.ylabel('Depth [m]')
        plt.xlabel('Density [kg/m3]')
        plt.title(sProfileName+'\n Depth Density Profile' )
        plt.show()
        
        if not os.path.exists(rfolder+'/plots'):
            os.makedirs(rfolder+'/plots')
        plt.savefig(rfolder+'/plots/ddp'+s+'.png', bbox_inches='tight')


# In[7]:


plot(me)


# In[8]:


def estimationError(deep=False):
    
    for s in sites:

        dfs = me[s]
        if not deep: dfs = dfs[dfs['Depth [m]'] <= 20]
        print(s)
        obsDensity = dfs['Density [kg/m3]']
        for m in models:
            try:
                modelDensity = dfs[m+'Density [kg/m3]']
                mae, rmse = compute_error(obsDensity, modelDensity)
                print(m, ' &', mae, ' &',rmse, '&')
            except: continue
        


# In[9]:


# rmse for the first 20 m
estimationError()


# In[10]:


# rmse for all
estimationError(True)

