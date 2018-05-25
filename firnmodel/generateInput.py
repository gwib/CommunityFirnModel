# -*- coding: utf-8 -*-
import csv
import numpy as np
import os


def generateStepDataFromFile(inFile):
    
    f = open(inFile, newline='')
    
    reader = csv.reader(f)
    
    timesteps = next(reader)
    print(type(timesteps))
    
    vals = [float(x) for x in next(reader)]
    
    min_val = min(vals)
    max_val = max(vals)
    
    f.close()
    
    n = len(timesteps)
    n_beforeStep = int(n*0.5)
    n_afterStep = n-n_beforeStep
    
    data = [min_val] * n_beforeStep + [max_val]*n_afterStep
    
    
    
    
    return timesteps, data



def generateConstDataFromFile(inFile):
    
    f = open(inFile, newline='')
    
    reader = csv.reader(f)
    
    timesteps = next(reader)
    
    vals = [float(x) for x in next(reader)]
    
    f.close()
    
    n = len(timesteps)
    
    data = [np.mean(vals)] * n
    
    return timesteps, data

def generateExperimentTempData(mode, inFile):
    
    f= open(inFile, newline='')
    
    reader = csv.reader(f)
    
    timesteps = next(reader)
    
    f.close()
    
    n = len(timesteps)
    n_beforeStep = int(n/3)
    n_afterStep = n-n_beforeStep
    
    if mode=='exp1':
        min_val = -50
        max_val = -45
        
    elif mode=='exp2':
        min_val = -40
        max_val = -35
        
    elif mode=='exp3':
        min_val = -30
        max_val = -25
    else:
        min_val = -30
        max_val = -30
    
    data = [min_val] * n_beforeStep + [max_val]*n_afterStep
    
    return timesteps, data


def generateExperimentBdotData(mode, inFile):
    
    f= open(inFile, newline='')
    
    reader = csv.reader(f)
    
    timesteps = next(reader)
    
    f.close()
    
    n = len(timesteps)
    n_beforeStep = int(n/3)
    n_afterStep = n-n_beforeStep
    
    if mode=='exp4':
        min_val = 0.02 #m/a
        max_val = 0.07
        
    elif mode=='exp5':
        min_val = 0.15
        max_val = 0.2
        
    elif mode=='exp6':
        min_val = 0.25
        max_val = 0.3
    else:
        min_val = 0.1
        max_val = 0.1
    
    data = [min_val] * n_beforeStep + [max_val]*n_afterStep
    
    return timesteps, data
        


def createCSVwithInput(inFile, newPath, newFile, mode):
    
    if mode=='step':
        time, data = generateStepDataFromFile(inFile)
    elif mode=='constant':
        time, data = generateConstDataFromFile(inFile)
    
    fn = os.path.join(newPath, newFile)
    
    new_file = open(fn, 'w')
    
    writer = csv.writer(new_file)
    writer.writerow(time)
    writer.writerow(data)
    
    new_file.close()
    
def createExperimentCSV(inputFile, newTempFile, newSmbFile, mode):
    
    expFolder = 'CFM_main/expFiles'
    
    time, tempData = generateExperimentTempData(mode, inputFile)
    _, smbData = generateExperimentBdotData(mode, inputFile)
    
    fnTemp = os.path.join(expFolder, newTempFile)
    
    tempFile = open(fnTemp, 'w')
    
    writer = csv.writer(tempFile)
    writer.writerow(time)
    writer.writerow(tempData)
    
    tempFile.close()
    
    fnSmb = os.path.join(expFolder, newSmbFile)
    
    smbFile = open(fnSmb, 'w')
    
    writer = csv.writer(smbFile)
    writer.writerow(time)
    writer.writerow(smbData)
    
    smbFile.close()
    
