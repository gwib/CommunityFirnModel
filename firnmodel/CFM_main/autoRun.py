# -*- coding: utf-8 -*-

import subprocess
import os
from createJsonSetupFiles import generateAutoRunFiles
from runStuff import realExperiment2
import numpy as np
import random
import matlab.engine
from dipTrend import dipTrendToCSV
import pickle

def runAuto():
    
    try:
        fp = open('indexFile.txt', 'rb')
        indices1 = pickle.load(fp)
        fp.close()
    except:
        indices1 = np.random.randint(1,50078, size=50078)
        indexSet = set(indices1)
        indices1 = random.sample(indexSet, len(indexSet))
        
    indices = [int(i) for i in indices1]
    
    for i in indices:
        print(i)
        eng = matlab.engine.start_matlab()
        lat, lon = eng.extractData2(i,nargout=2)
        coords = [lat, lon]
        eng.quit()
        
        
        generateAutoRunFiles(i)
        realExperiment2(setupFolder='setupAuto', sites=[str(i)])
        dipTrendToCSV(str(i),coords)

def runMatlab(i):
    eng = matlab.engine.start_matlab()
    lat,lon = eng.extractData2(i,nargout=2)
    eng.quit()
    return lat,lon
    
    
    #todo: try this:
    #from mlabwrap import mlab
    #mlab.myFunction('testadaptor', './', 'image.png')


# get temp and smb from matlab

# generate json files

# run for all models

