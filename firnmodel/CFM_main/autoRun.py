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
        indices = pickle.load(fp)
        fp.close()
    except:
        indices = np.random.randint(1,50078, size=50078)
        indexSet = set(indices)
        indices = random.sample(indexSet, len(indexSet))
    
    for i in indices:
        eng = matlab.engine.start_matlab()
        [lat, lon] = eng.extractData2(i)
        coords = [lat, lon]
        eng.quit()
        
        
        generateAutoRunFiles(i)
        realExperiment2(setupFolder='setupAuto', sites=[str(i)])
        dipTrendToCSV(str(i),coords)

def runMatlab(i):
    eng = matlab.engine.start_matlab()
    [lat, lon] = eng.extractData2(i)
    coords = [lat, lon]
    eng.quit()


# get temp and smb from matlab

# generate json files

# run for all models

