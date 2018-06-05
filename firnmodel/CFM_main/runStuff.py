#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 18 11:14:50 2018

@author: GalinaJonat
"""

# Script to run all models in parrallel
import subprocess
from plotDrhoDt import dip100

experiments = ['exp'+str(x) for x in range(1,7)]
models = ["Arthern2010S","HLdynamic","HLSigfus","Li2011","Helsen2008","Goujon2003","Barnola1991","KuipersMunneke2015","Crocus", 'Simonsen2013',"Arthern2010T",]#TODO: ,"Morris2014"
sites = ['site'+str(x) for x in range(1,4)]

def generatePaperOutput():
    for e in experiments:
        for m in models:
            cmd = ['python', 'main.py', 'experimentSetups/'+e+'Setup_'+m+'.json']
            subprocess.Popen(cmd)

def plotDIPforAll():
    e = 'exp1'
    for m in models:
        dip100('CFMexperiments', 'CFM'+e+"results"+m+".hdf5")

def generatePaperOutput15000():
    for e in experiments:
        for m in models:
            cmd = ['python', 'main.py', 'experimentSetups15000/'+e+'Setup_'+m+'.json']
            subprocess.Popen(cmd)

def realExperiment():
    for s in sites:
        for m in models:
            cmd = ['python', 'main.py', 'setupInput2-1/'+s+'_Setup_'+m+'.json']
            subprocess.Popen(cmd)
            
def realExperiment2():
    for s in sites:
        for m in models:
            cmd = ['python', 'main.py', 'setupInput2/'+s+'_Setup_'+m+'.json']
            subprocess.Popen(cmd)