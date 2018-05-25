# -*- coding: utf-8 -*-
import json


def generateDataFile(expNum, modelname):
    
    if expNum in ['exp1', 'exp2', 'exp3']:
        bDotFile = 'bDot_const.csv'
        tskinFile = 'tskin_'+expNum+'.csv'
    else:
        bDotFile = 'bDot_'+expNum+'.csv'
        tskinFile = 'tskin_const.csv'
        
    if modelname=='Arthern2010T':
        smodelname='Arthern2010S'
    else: smodelname = modelname

    
    data = {
    "InputFileFolder": "CFMexp2",
    "InputFileNameTemp": tskinFile,
    "InputFileNamebdot": bDotFile,
    "resultsFolder": "./CFMexperiments",
    "physRho": modelname,
    #"_physRhoOptions":["HLdynamic","HLSigfus","Li2004","Li2011","Helsen2008","Arthern2010S","Arthern2010T","Spencer2001","Goujon2003","Barnola1991","Morris2014","KuipersMunneke2015","Crocus"],
    "MELT": 0, #false
    "FirnAir": 0, #false
    "TWriteInt": 1,
    "int_type": "nearest",
    #"int_type_options": ["nearest","linear"],
    "SeasonalTcycle": 0, #false
    "TAmp":10.0,
    "physGrain": 1,
    "calcGrainSize": 0,
    "heatDiff": 1,
    "variable_srho": 0,
    "rhos0": 360.0,
    "r2s0": 1.0e-8,
    "AutoSpinUpTime": 1,#'true',
    "yearSpin": 10000,
    "stpsPerYearSpin": 1.0,
    "H": 3000,
    "HbaseSpin": 2750.0,
    "stpsPerYear": 1.0,
    "D_surf": 1.0,
    "GrGrowPhysics": "Arthern",
    "_GrGrowPhysics_options": ["Arthern", "Katsushima"],
    "bdot_type": "mean",
    #"bdot_options": ["instant","mean","stress"],
    "isoDiff": 0,#'false',
    "iso": "NoDiffusion",
    #"_isoOptions":["18","D","NoDiffusion"],
    "spacewriteint": 1,
    "strain": 0,
    "du_dx": 1e-5,
    "outputs": ["density", "depth", "compaction","DIP","BCO","temperature","LWC","gasses"],
    #"output_options": ["density", "depth", "temperature", "age", "dcon", "bdot_mean", "climate", "compaction", "grainsize", "temp_Hx", "isotopes", "BCO", "LIZ", "DIP","LWC","gasses"],
    "resultsFileName": "CFM"+expNum+"results"+modelname+".hdf5",
    "spinFileName": "CFM"+expNum+"spin"+smodelname+".hdf5",
    "doublegrid": 0, # use 0 and 1 instead of true/false
    "nodestocombine": 50,
    "grid1bottom": 10.0
    }


    with open('experimentSetups/'+expNum+'Setup_'+modelname+'.json', 'w') as outfile:
        #json.dumps(data, outfile, indent=4)
        outfile.write(json.dumps(data, indent=4))



def generate15000DataFile(expNum, modelname):
    
    if expNum in ['exp1', 'exp2', 'exp3']:
        bDotFile = 'bDot_const.csv'
        tskinFile = 'tskin_'+expNum+'.csv'
    else:
        bDotFile = 'bDot_'+expNum+'.csv'
        tskinFile = 'tskin_const.csv'
        
    if modelname=='Arthern2010T':
        smodelname='Arthern2010S'
    else: smodelname = modelname

    
    data = {
    "InputFileFolder": "CFMexp2",
    "InputFileNameTemp": tskinFile,
    "InputFileNamebdot": bDotFile,
    "resultsFolder": "./CFMexperiments15000",
    "physRho": modelname,
    #"_physRhoOptions":["HLdynamic","HLSigfus","Li2004","Li2011","Helsen2008","Arthern2010S","Arthern2010T","Spencer2001","Goujon2003","Barnola1991","Morris2014","KuipersMunneke2015","Crocus"],
    "MELT": 0, #false
    "FirnAir": 0, #false
    "TWriteInt": 1,
    "int_type": "nearest",
    #"int_type_options": ["nearest","linear"],
    "SeasonalTcycle": 0, #false
    "TAmp":10.0,
    "physGrain": 1,
    "calcGrainSize": 0,
    "heatDiff": 1,
    "variable_srho": 0,
    "rhos0": 360.0,
    "r2s0": 1.0e-8,
    "AutoSpinUpTime": 0,#'false',
    "yearSpin": 15000,
    "stpsPerYearSpin": 1.0,
    "H": 3000,
    "HbaseSpin": 2750.0,
    "stpsPerYear": 1.0,
    "D_surf": 1.0,
    "GrGrowPhysics": "Arthern",
    "_GrGrowPhysics_options": ["Arthern", "Katsushima"],
    "bdot_type": "mean",
    #"bdot_options": ["instant","mean","stress"],
    "isoDiff": 0,#'false',
    "iso": "NoDiffusion",
    #"_isoOptions":["18","D","NoDiffusion"],
    "spacewriteint": 1,
    "strain": 0,
    "du_dx": 1e-5,
    "outputs": ["density", "depth", "compaction","DIP","BCO","temperature","LWC","gasses"],
    #"output_options": ["density", "depth", "temperature", "age", "dcon", "bdot_mean", "climate", "compaction", "grainsize", "temp_Hx", "isotopes", "BCO", "LIZ", "DIP","LWC","gasses"],
    "resultsFileName": "CFM"+expNum+"results"+modelname+".hdf5",
    "spinFileName": "CFM"+expNum+"spin"+smodelname+".hdf5",
    "doublegrid": 0, # use 0 and 1 instead of true/false
    "nodestocombine": 50,
    "grid1bottom": 10.0
    }


    with open('experimentSetups15000/'+expNum+'Setup_'+modelname+'.json', 'w') as outfile:
        #json.dumps(data, outfile, indent=4)
        outfile.write(json.dumps(data, indent=4))
 
        
# generate JSON Files for all models
def generateSetupFiles():
    experiments = ['exp'+str(x) for x in range(1,7)]
    models = ["HLdynamic","HLSigfus","Li2011","Helsen2008","Arthern2010S","Arthern2010T","Goujon2003","Barnola1991","Morris2014","KuipersMunneke2015","Crocus", 'Simonsen2013']
    
    for e in experiments:
        for m in models:
            generateDataFile(e, m)
            
    
def generateSetupFiles15000():
    experiments = ['exp'+str(x) for x in range(1,7)]
    models = ["HLdynamic","HLSigfus","Li2011","Helsen2008","Arthern2010S","Arthern2010T","Goujon2003","Barnola1991","Morris2014","KuipersMunneke2015","Crocus", 'Simonsen2013']
    
    for e in experiments:
        for m in models:
            generate15000DataFile(e,m)