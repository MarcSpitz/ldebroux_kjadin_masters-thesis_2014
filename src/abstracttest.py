#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Debroux Léonard  <leonard.debroux@gmail.com>
# @author: Jadin   Kevin    <contact@kjadin.com>

from abc import ABCMeta, abstractmethod

import sys, os, random
import subprocess
from utils import Utils
from setup import Setup
import logging as log
import csv

from networkgraph import NetworkGraph
from pylab import boxplot, show, savefig, figure, plot
from matplotlib import rc
import numpy

from setupparser import parseConfigArguments

class AbstractTest(object):
  """ Abstract test """
  __metaclass__ = ABCMeta

  def __init__(self):

    # reset setup once so that the static configuration dictionary is set
    Setup.reset_setup()

    args = parseConfigArguments(sys.argv) 

    verbosity = args['verbosity']
    Utils.configure_logger(verbosity)

    log.debug("args: %s" % args)

    self.config_file = os.path.basename(args['setupsFile'])
    self.config_file = self.config_file.replace('.', '_')
    
    self.working_directory = args['directory']

    topologyDict = args['topology']
    self.topology            = topologyDict['topology']
    self.weight_attribute    = topologyDict['weight_attribute']
    self.shortest_paths_file = topologyDict['shortest_paths_file']
    self.root                = topologyDict['root']

    self.colors = {
      'green' :'lightgreen',
      # 'red'   :'#fd522b',
      'orange'   :'#FF6633',
      'red'   :'#ef4141',
      'gray'  :'#777777',
      'black' :'#000000',
      # 'blue'  :'#3366FF',
      'blue'  :'#2edbd9',
      'yellow':'#fce94f',
      'lightorange':'#fcaf3e'
    }
    
    kset  = [1]#, 2, 3, 4]#[1]
    self.NGdict = self.compute_NGdict(self.topology, self.weight_attribute, self.shortest_paths_file, kset)

    # reset once more before beginning
    Setup.reset_setup()
    

    ### DATASETS ###

    # TODO maybe proba and lifeTime should be different for every dataSet in order to have a setup comparison that has more coverage
    self.dataSets = args['datasets']


    ### TEST ###
    main, setupsList  = args['testing']

    self.testname     = main['name']
    self.refColumn    = main['columnRef']
    self.tests        = main['tests']
    
    self.setupDicts = setupsList

    # print csv representation for setups
    self.printCSVSetups()

    # reset once more before beginning
    Setup.reset_setup()

    self.configGraphFont()
    
  def printCSVSetups(self):
    """ output a csv representation for each setup used """

    defaultSetup = Setup.default_setup()
    parameters = sorted(defaultSetup.keys())
    for i in range(len(self.setupDicts)):

      # output a csv to be used later on
      filename = "setup%s.csv" % (i)
      # filename = "%s_%s" % (args['setupsFile'], filename) 
      filename = os.path.join(self.working_directory, filename)

      with open(filename, 'w') as fp:
        log.info('exporting setup %i to file %s' % (i, filename))
        writer = csv.writer(fp, delimiter=',')
        writer.writerow(parameters) # parameters as header
        setup = self.setupDicts[i]
        fullSetup = Setup.merge(defaultSetup, setup)
        orderedValues = [fullSetup[k] for k in parameters]
        writer.writerow(orderedValues)

  def configGraphFont(self):
    font = {'family' : 'monospace',
        # 'weight' : 'bold',
        'size'   : 18}

    rc('font', **font)

  def compute_NGdict(self, topology, weight_attribute, shortest_paths_file, kset):
    NGdict = dict()
    for k in kset:
      log.info('building NetworkGraph structure for k = %s' % k)
      Setup.configure(dict(k_shortest_paths = k))
      NGdict[k] = NetworkGraph(topology, weight_attribute, shortest_paths_file)
    return NGdict

  def print_logs(self):
    log.debug('%20s = %s' % ('topology file', self.topology))
    log.debug('%20s = %s' % ('weight attribute', self.weight_attribute))
    log.debug('%20s = %s' % ('root', self.root))
    Setup.log()

  def log_progression(self, dsIndex, dsNumber, setupIndex, setupNumber, testname):
    log.info('\t>>> \"%s\" progression: %s/%s, %s/%s <<<' % (testname, dsIndex, dsNumber, setupIndex, setupNumber))

  def addImproveToDataSet(self, ds): # ds is a list of tuples, some are ('t', _) to represent the ticks
    actionTuples = []
    ip, it = Setup.get('improve_period'), Setup.get('improve_maxtime')
    tick = 0
    for action, arg in ds:
      if action == 't':
        tick += 1
        if tick % ip == 0:
          actionTuples.append(('i', it))
      actionTuples.append((action, arg))

    lastAction, _ = actionTuples[-1]
    # print actionTuples
    # if lastAction != 'i':
    #   actionTuples.append(('i', it))
    return actionTuples

  def writeNewline(self, line, f):
    f.write('%s\n' % line) 

  def writeDataHeader(self, f, dataSetIndex, setupIndex, idx):
    self.writeNewline('', f)
    self.writeNewline('dataset %s' % dataSetIndex, f)
    self.writeNewline('setup %s' % setupIndex, f)
    self.writeNewline('test %s' % idx, f)

  @abstractmethod
  def run(self):
    """ this method should be implemented by the search method """
    pass
