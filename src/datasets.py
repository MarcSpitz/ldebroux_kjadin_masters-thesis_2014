#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Debroux Léonard  <leonard.debroux@gmail.com>
# @author: Kevin Jadin      <contact@kjadin.com>

import sys
import argparse
import logging as log

import networkx as nx

from utils import Utils 

def probabilityFloat ( string ):
  value = float( string )
  if value < 0 or value > 1:
    raise argparse.ArgumentTypeError('has to be a float value between 0.0 and 1.0')
  return value

def positiveFloat ( string ):
  value = float( string )
  if value <= 0.0:
    raise argparse.ArgumentTypeError('has to be a strictly positive float')
  return value

def positiveInt ( string ):
  value = int( string )
  if value <= 0:
    raise argparse.ArgumentTypeError('has to be a strictly positive integer')
  return value

def configure_parser():

  parser = argparse.ArgumentParser()

  # parser.add_argument('-d', '--datasets',
  #                     nargs='+',
  #                     type=str,
  #                     help="TODO",
  #                     default=[])

  parser.add_argument("topology", 
                      type=str,
                      help="the GML topology file",
                      default="")

  parser.add_argument('-r', '--root',
                      type=int,
                      help="root node of the tree",
                      default=None)
  parser.add_argument("-o", "--output", 
                      type=str,
                      help="Filename for saving shortest paths structures",
                      default=None)
  parser.add_argument("-p", "--join-probability", 
                      type=probabilityFloat,
                      help="TODO",
                      default=None)
  parser.add_argument('-m', '--mean-time',
                      type=positiveFloat,
                      help="TODO",
                      default=None)
  parser.add_argument('-t', '--ticks',
                      type=positiveInt,
                      help="TODO",
                      default=None)

  parser.add_argument("-v", "--verbosity",
                      help="verbose output",
                      action="count",
                      default=0)
  return parser

def readDataset(filename):
  tuples = list()
  with open(filename, 'r') as f:
    for line in f:
      if line and line[0] != '#':
        line = line[:-1]
        a, b = line.split()
        tuples.append((a,int(b),))

  return tuples

def writeTuples(filename, tuples):
  with open(filename, 'w') as f:
    for tup in tuples:
      f.write('%s %s\n' % tup)

def main(argv):

  parser = configure_parser()
  args = parser.parse_args()

  Utils.configure_logger(args.verbosity)

  topology          = args.topology
  root              = args.root
  output            = args.output
  join_probability  = args.join_probability
  mean_time         = args.mean_time
  ticks             = args.ticks

  argsDict = vars(args)
  
  for k,v in argsDict.iteritems():
    if v == None:
      parser.error('missing argument %s' % k)

  datasetInfos = []
  datasetInfos.append(('# given arguments', '#',))
  for k,v in argsDict.iteritems():
    log.info('%20s = %s' % (k, v))
    # appending all parameters to a list as comment
    datasetInfos.append(('# %s' % k, v,))

  # kept for reference
  # log.info("topology          = {topology}\n\
  #           output            = {output}\n\
  #           join_probability  = {join_probability}\n\
  #           mean_time         = {mean_time}\n\
  #           ticks             = {ticks}\n".format(argsDict))

  G     = nx.read_gml(topology)
  nodes = G.nodes()

  eventsDict = Utils.generateEventDict(join_probability, mean_time, ticks, nodes, root)

  avgEventsPerTick = sum([len(eventsDict[key]) for key in eventsDict.keys()])/float(len(eventsDict.keys()))
  log.info('average events per tick: %s' % avgEventsPerTick)

  datasetInfos.append(('# average events per tick', avgEventsPerTick,))
  
  actionTuples = []
  for key in sorted(eventsDict.keys()):
    actionTuples.extend(eventsDict[key])
    actionTuples.append(('t', key))
  
  log.debug("actionTuples: %s" % actionTuples)

  finalClientSet = Utils.compute_final_clients_set(actionTuples)
  log.debug("finalClientSet: %s" % finalClientSet)
  datasetInfos.append(('# final client set size', len(finalClientSet),))

  toWriteTuples = datasetInfos[:]
  toWriteTuples.append(('# scenario start', '#',))
  toWriteTuples.extend(actionTuples)
  log.debug("toWriteTuples: %s" % toWriteTuples)  

  # output file
  log.info("outputting to %s" % output)
  writeTuples(output, toWriteTuples)



if __name__ == "__main__":
  main(sys.argv)
