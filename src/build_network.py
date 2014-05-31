#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Debroux Léonard  <leonard.debroux@gmail.com>
# @author: Jadin   Kevin    <contact@kjadin.com>

# uncomment for achieving profiling on the full execution
# -m cProfile -o stats -s time
import sys
import argparse
import networkx as nx
from multicasttree import MulticastTree
from networkgraph import NetworkGraph
from utils import Utils
from setup import Setup
import logging as log
import random
import time
import sys

""" This script launches a typical construction of a multicast tree
    according to an action sequence """

def configure_parser():
  """ configures the parser """
  parser = argparse.ArgumentParser()
  parser.add_argument("topology", 
                      type=str,
                      help="the topology file (gml format)",
                      default="")
  parser.add_argument("-sp", "--shortest-paths-file", 
                      type=str,
                      help="Shortest paths filename. Created dynamically if non existing.",
                      default=None)
  parser.add_argument("-a", "--attribute", 
                      type=str,
                      help="attribute on which the weight should be computed. This information should be present in the underlying graph file.",
                      choices=[Setup.NONE, Setup.WEIGHT, Setup.GEO, Setup.BANDWIDTH],
                      default=Setup.WEIGHT)
  parser.add_argument('-r', '--root',
                      type=int,
                      help="root node of the tree",
                      default=0)
  parser.add_argument('-as', '--action-sequence',
                      # nargs='+',
                      type=str,
                      help="specifies an action sequence a X, r Y, ar Z1 Z2",
                      default="")
  parser.add_argument("--client-ordering", 
                      type=str,
                      help="order in which to add the clients set",
                      choices=Setup.getChoices('client_ordering'),
                      default=Setup.getDefault('client_ordering'))
  parser.add_argument("--heuristic", 
                      type=str,
                      help="heuristic to follow for the selectEdge() method",
                      choices=Setup.getChoices('selection_heuristic'),
                      default=Setup.getDefault('selection_heuristic'))
  parser.add_argument('-ttl', '--tabu-ttl',
                      type=int,
                      help="size of the tabu list to use for selected edges",
                      default=Setup.getDefault('tabu_ttl'))
  parser.add_argument('--intensify-only',
                      help="choose whether to intensify or allow degradation",
                      action="store_true")
  parser.add_argument('-pim','--pim-mode',
                      help="emulate the PIM behaviour for building trees: based on a shortest paths from receivers to sources. Improvement steps are not processed and discarded if this mode is used.",
                      action="store_true")
  parser.add_argument("-ss", "--search-strategy", 
                      type=str,
                      help="search strategy to follow when reconnecting connected components. First improve stops as soon as finding an improving solution",
                      choices=Setup.getChoices('search_strategy'),
                      default=Setup.getDefault('search_strategy'))
  parser.add_argument('-ip', '--improve-period',
                      type=int,
                      help="period (every X client additions) after which to do an improve step",
                      default=Setup.getDefault('improve_period'))
  parser.add_argument('-it', '--improve-maxtime',
                      type=int,
                      help="allowed time for each improve step (in milliseconds)",
                      default=Setup.getDefault('improve_maxtime'))
  parser.add_argument('-rssb', '--reconnection-search-space-breadth',
                      type=int,
                      help="breadth of search space to consider when reconnecting",
                      default=Setup.getDefault('improve_search_space'))
  parser.add_argument('-ts', '--temperature-schedule',
                      type=str,
                      help="defines the temperature schedule to use",
                      choices=Setup.getChoices('temperature_schedule'),
                      default=Setup.getDefault('temperature_schedule'))
  parser.add_argument('-k', '--k-shortest-paths',
                      type=int,
                      help="maximum number of shortest paths to consider per shortest paths computation. k = 1 amounts to applying simple dijkstra. This value should be lower or equal to 'PATHS' value.",
                      default=Setup.getDefault('k_shortest_paths'))
  parser.add_argument('-p', '--max-paths',
                      type=int,
                      help="maximum number of paths to select for removal in each improvement step",
                      default=Setup.getDefault('max_paths'))
  parser.add_argument("--steps", 
                      type=str,
                      help="if and where to show computation steps for the improveTree() method. For demonstration/debugging purposes.",
                      choices=Setup.getChoices('steps'),
                      default=Setup.getDefault('steps'))
  parser.add_argument("--stats", 
                      type=str,
                      help="dump client additions statistics into this file",
                      default=Setup.getDefault('statistics_dump_file'))
  parser.add_argument("-v", "--verbosity",
                      help="verbose output",
                      action="count")
  return parser

def main(argv):

  parser = configure_parser()
  args = parser.parse_args()

  Utils.configure_logger(args.verbosity)

  # reset setup once so that the static dictionary is set
  Setup.reset_setup()
  
  topology            = args.topology
  weight_attribute    = args.attribute
  shortest_paths_file = args.shortest_paths_file
  root                = args.root
  action_sequence     = args.action_sequence

  setupDict = dict(
    client_ordering      = args.client_ordering,
    selection_heuristic  = args.heuristic,
    tabu_ttl             = args.tabu_ttl,
    intensify_only       = args.intensify_only,
    pim_mode             = args.pim_mode,
    search_strategy      = args.search_strategy,
    improve_period       = args.improve_period,
    improve_maxtime      = args.improve_maxtime,
    improve_search_space = sys.maxint if args.reconnection_search_space_breadth == 0 else args.reconnection_search_space_breadth,
    temperature_schedule = args.temperature_schedule,
    k_shortest_paths     = args.k_shortest_paths,
    max_paths            = args.max_paths,
    steps                = args.steps,
    statistics_dump_file = args.stats,
  )
  log.info("setupDict: %s" % setupDict)

  """ check arguments validity """

  if not shortest_paths_file:
    parser.error("missing SHORTEST_PATHS_FILE argument")
  # configure the static setup according to arguments
  Setup.configure(setupDict)

  """ log the arguments """
  log.info('%20s = %s' % ('topology file', topology))
  log.info('%20s = %s' % ('weight attribute', weight_attribute))
  log.info('%20s = %s' % ('shortest_paths_file', shortest_paths_file))
  log.info('%20s = %s' % ('root', root))
  log.info('%20s = %s' % ('action sequence', action_sequence))
  Setup.log()

  # load topology
  NG = NetworkGraph(  topology,
                      weight_attribute,
                      shortest_paths_file
                    )

  events = Utils.generateActionTuples(action_sequence, set(NG.nodes()))

  events = Utils.addTicks(events)

  log.debug("events: %s" % events)

  # check clients set node inclusion
  # commented as should not be necessary anymore, done in the generateActionTuples method call
  # if not set(clientlist).issubset(set(NG.nodes())):
  #   raise Exception("given clients list is not a subset of topology nodes")

  # build the multicast tree
  T = NG.buildMCTree(root, events)
  
  log.info('tree building over')
  # log.info("time for buildMCTree(): %f ms" % ((stopBuildMCTree-startBuildMCTree)*1000.0))
  
  log.info('tree clients: %s' % T.clients())

  j = '-'.join(map(str, events))

  # uncomment to write an image representation of the graph+tree
  # finalTreeName = 'root-%s_clients-%s.pdf' % ( root, j[:20] )
  finalTreeName = "root-%s_sequence-%s.pdf" % (root, "".join(action_sequence.split()))
  T.export_file(finalTreeName)

  if (setupDict.get('steps') == Setup.PLOT):
    # ask for user input such that program does not exit directly
    _ = raw_input('Exit?')


if __name__ == "__main__":
  main(sys.argv)
