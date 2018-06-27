#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 18 11:14:50 2018

@author: GalinaJonat
"""

# Script to run all models in parallel
import subprocess
from plotDrhoDt import dip100
import os
from threading import Thread

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

def call_script(*arg):
    subprocess.call(arg)           


def realExperiment2(setupFolder='setupInput2/', sites=sites):
    t = {}
    for s in sites:
        for m in models:
            cmd = ['python', 'main.py', os.path.join(setupFolder, s+'_Setup_'+m+'.json')]
            #subprocess.Popen(cmd)
            #subprocess.call(cmd)
            
            t[s+m] = Thread(target=call_script, args=cmd)
            t[s+m].start()
        for m in models:
            t[s+m].join(timeout=3600)