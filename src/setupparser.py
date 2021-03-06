#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Debroux Léonard  <leonard.debroux@gmail.com>
# @author: Kevin Jadin      <contact@kjadin.com>

import sys, os
import configparser
from setup import Setup
from datasets import readDataset
import argparse
import logging as log
from utils import Utils

def getValueForKey(dictionary, key):
  if not key in dictionary:
    raise Exception('malformed configuration file: missing entry %s' % key)
  return dictionary[key]

def readSetupsConfig(configFile):
  config = configparser.ConfigParser()
  config.read(configFile)

  sections = config.sections()
  log.debug("sections: %s" % sections)

  main_section_string = 'main'
  main_section = getValueForKey(config, main_section_string)
  testname  = getValueForKey(main_section, 'name')
  tests     = getValueForKey(main_section, 'tests')
  log.debug("testname: %s" % testname)

  main = dict(
      name = testname,
      tests = int(tests),
      columnRef = int(getValueForKey(main_section, 'columnRef') if 'columnRef' in main_section else -1)
    )

  # setups
  setups = sections[1:]
  log.debug("setups: %s" % setups)

  def validateDict(dictionary):
    for (k,v) in dictionary.iteritems():
      dictionary[k] = Setup.autocast(k,v)

  setupsList = list()
  for setupName in setups:
    setupDict = dict(config[setupName])
    validateDict(setupDict)
    log.debug("setupDict: %s" % setupDict)
    setupsList.append(setupDict)

  log.debug("setupsList: %s" % setupsList)

  return main, setupsList

def readTopologyConfig(configFile):
  config = configparser.ConfigParser()
  config.read(configFile)

  sections = config.sections()
  log.debug("sections: %s" % sections)

  main_section_string = 'main'
  main_section = getValueForKey(config, main_section_string)

  topologyDict = dict(topology_name     = getValueForKey(main_section, 'name'),
                      topology          = getValueForKey(main_section, 'topology'),
                      weight_attribute  = getValueForKey(main_section, 'weight_attribute'),
                      root = int(getValueForKey(main_section, 'root')),
                      shortest_paths_file = getValueForKey(main_section, 'shortest_paths_file')
                      )
  
  log.debug("topologyDict: %s" % topologyDict)
  return topologyDict

def configure_parser():
  parser = argparse.ArgumentParser()
  parser.add_argument('--config', '-c',
                      type=str,
                      help="setups file")
  parser.add_argument('--topology', '-t',
                      type=str,
                      help="topology file")
  parser.add_argument('--datasets', '-d',
                      nargs='+',
                      type=str,
                      help="topology file")

  parser.add_argument("-v", "--verbosity",
                      action="count",
                      default=1,
                      help="verbosity level")

  parser.add_argument('-w', '--working-directory',
                      type=str,
                      action='store', dest='directory',
                      default=os.path.dirname(sys.argv[0]),
                      help='specify directory')

  return parser

def readDatasets(datasetFiles):
  datasets = list()
  for datasetFile in datasetFiles:
    ds = readDataset(datasetFile)
    datasets.append(ds)

  return datasets

def parseConfigArguments(argv):
  parser = configure_parser()
  options = parser.parse_args()

  topologyFile = options.topology
  if not topologyFile:
    parser.error("no topology file given")
  elif not os.path.isfile(topologyFile):
    parser.error("%s file does not exist" % topologyFile)

  setupsFile = options.config
  if not setupsFile:
    parser.error("no setups file given")
  elif not os.path.isfile(setupsFile):
    parser.error("%s file does not exist" % setupsFile)

  datasetFiles = options.datasets
  if not datasetFiles:
    parser.error("no datasets file(s) given")
  for dsFile in datasetFiles:
    if not os.path.isfile(dsFile):
      parser.error("%s file does not exist" % dsFile)

  Utils.configure_logger(options.verbosity)

  args    = dict( topology    = readTopologyConfig(topologyFile),
                  testing     = readSetupsConfig(setupsFile),
                  setupsFile  = setupsFile,
                  datasets    = readDatasets(datasetFiles),
                  directory   = options.directory,
                  )
  log.debug("args: %s" % args)
  return args

def testing(argv):
  args = parseConfigArguments(argv)

if __name__ == "__main__":
  testing(sys.argv)
