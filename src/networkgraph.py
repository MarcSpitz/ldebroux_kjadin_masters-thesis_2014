# -*- coding: utf-8 -*-
# @author: Debroux Léonard  <leonard.debroux@gmail.com>
# @author: Kevin Jadin      <contact@kjadin.com>

# references : visualisation tool : http://gephi.org/
#              http://networkx.lanl.gov/examples/drawing/index.html

import sys, os
import networkx as nx
import matplotlib.pyplot as plt
from multicasttree import MulticastTree
from improve_methods import ImproveMethods
import logging as log
import random
import ksp
import haversine
from utils import Utils
from setup import Setup

# @todo remove
# from guppy import hpy; h=hpy()

# for saving/loading the shortest paths to/from a file
import cPickle as pickle

class NetworkGraph(nx.Graph):
  """ NetworkGraph class """
  
  def __init__(self, _filename, _weight_attribute, _shortest_paths_filename):
    super(NetworkGraph, self).__init__(nx.read_gml(_filename))
    
    self.filename  = _filename
    self.add_weight_attribute(_weight_attribute)

    if os.path.isfile(_shortest_paths_filename):
      """ shortest paths file exists """
      log.info("loading shortest paths structures from file: %s" % _shortest_paths_filename)
      self.load_shortest_paths(_shortest_paths_filename)
    else: 
      """ shortest paths structures must be recomputed """
      log.info("recomputing shortest paths structures")
      sP, sPL, sPC = ksp.get_shortest_paths(self, Setup.get('k_shortest_paths'))
      self.ShortestPaths       = sP
      self.ShortestPathsLength = sPL
      self.ShortestPathsCount  = sPC
      log.info("saving shortest paths structures to file: %s" % _shortest_paths_filename)
      self.save_shortest_paths(_shortest_paths_filename)

    log.debug('ShortestPaths      : %s' % self.ShortestPaths)
    log.debug('ShortestPathsLength: %s' % self.ShortestPathsLength)
    log.debug('ShortestPathsCount : %s' % self.ShortestPathsCount)

    self.layout = nx.spring_layout(self, k=0.3, iterations=50)


  def save_shortest_paths(self, filename):
    """ Exports the shortest paths by exporting the memory to a file """
    # pack the 3 data structures
    struct = [self.ShortestPaths, self.ShortestPathsLength, self.ShortestPathsCount]
    with file(filename,  'wb') as outfile:
      pickle.dump(struct, outfile)

  def load_shortest_paths(self, filename):
    """ Importing the shortest paths. The file give should be a dump of the memory """
    with file(filename,  'rb') as infile:
      struct  = pickle.load(infile)

    sP, sPL, sPC = struct # unpack the data structures

    self.ShortestPaths        = sP
    self.ShortestPathsLength  = sPL
    self.ShortestPathsCount   = sPC

  def add_weight_attribute(self, type = None):
    """ Adds the weighs to the edges of the network graph based on the weight attribute
        Can be either GEO, WEIGHT, BANDWIDTH or NONE
        In the case of GEO, the weight are extrapolated based on the position of the nodes
        In the case of WEIGHT and BANDWIDTH, the edges in the gml should have the corresponding attribute
        If set to NONE, all edges have a weight of 1
    """
    
    NG = self

    Nodes = NG.nodes(data=True)
    if type == "GEO":
      log.debug("using %s attribute" % type)
      # when geographic location attribute is present
      longitude_attribute_str = "Longitude"
      latitude_attribute_str  = "Latitude"

      # default value when the computation of the distance fails
      # a failure occurs when the coordinates are wrong or not present
      default_distance = 60
      log.info("setting %s as default distance" % default_distance)

      def map_geo(e):
        n1, n2 = e
        N1 = NG.node[n1]
        N2 = NG.node[n2]
        log.debug("N1: %s" % N1)
        log.debug("N2: %s" % N2)
        try:
          origin      = (N1[latitude_attribute_str], N1[longitude_attribute_str])
          destination = (N2[latitude_attribute_str], N2[longitude_attribute_str])
          # take the distance in km
          dist = haversine.distance(origin, destination)
        except Exception, e:
          log.warning("no location information available for one node")
          log.debug(str(e))
          dist = default_distance

        if dist < 1.0:
          # a distance of 1 is the minimum value, the weight of a link in a network must be strictly positive
          dist = 1

        log.debug("dist: %s km" % dist)
        return int(dist)
      weights = {e:map_geo(e) for e in NG.edges()}

    elif type == "BANDWIDTH":
      # when bandwidth attribute is present
      # edge attribute
      log.debug("using %s attribute" % type)
      raise Exception("TODO: bandwidth derivation")
      pass

    elif type == "WEIGHT":
      # edge attribute
      log.debug("using %s attribute" % type)
      attribute_str = "weight"
      weights = {(n1, n2):d[attribute_str] for (n1, n2, d) in NG.edges(data=True)}

    else: # "NONE"
      log.debug("no attribute present")
      # when no attribute is present
      # overwrite weights attribute
      log.debug("overwriting weight attribute")
      overwrite_value = 1
      log.debug("overwriting edge weights to %d" % overwrite_value)
      weights = {e:overwrite_value for e in NG.edges()}
    nx.set_edge_attributes(NG, 'weight', weights)

  def draw(self):
    nx.draw(self, self.layout)

    plt.show()
    # clean plot
    plt.clf()

  def export(self, outfile):
    nx.draw_graphviz(self)
    nx.write_dot(self, outfile)

  def getEdgePathWeight(self, path):
    """ Compute the weight of a path expressed as [edge1, edge2, ..., edgeN], where edges are couples of nodes """
    totWeight = 0
    for e in path:
      n1, n2 = e
      totWeight += self[n1][n2]['weight']
    return totWeight

  def getNodePathWeight(self, path, fullWeight = False):
    """ Compute the weight of a path expressed as a list of nodes: [n1, n2, ..., nN] """
    totWeight = 0
    for i in range(len(path)-1):
      n1 = path[i]
      n2 = path[i+1]
      totWeight += self[n1][n2]['weight']
    selectionHeuristic = Setup.get('selection_heuristic')
    if (selectionHeuristic == Setup.AVERAGED_MOST_EXPENSIVE_PATH) and (not fullWeight):
      totWeight = totWeight/len(path)-1
    return totWeight

  def buildMCTree(self, root, events):
    """ Creates the multicast tree based on the given events.
        Depending on the client_ordering heuristic that is used, the list of event may be changed
        Regularily checks that the tree is a valid multicast tree for the current clients
    """
    log.debug('building multicast tree')
    log.debug('set of events: %s' % events)
    
    # should start with empty tree
    T = MulticastTree(self, root)

    # Variables for the heuristics
    eventsList    = list(events)
    closestClient   = None
    # nodes will be added in the order from by the following list,
    # which is defined according to the chosen client ordering method
    chosenOrdering  = list()

    client_ordering = Setup.get('client_ordering')

    pim_mode = Setup.get('pim_mode')

    if client_ordering == Setup.CLOSEST_TREE:
      # TODO: this function is not in use anymore
      # Chooses the client that is the closest to the tree and adds it.
      # Will be useful to tests random client arrival versus known client set
      # ---------------------------------------------------------------------
      clients = Utils.compute_final_clients_set(eventsList)
      while clients:
        log.debug("eventsList: %s" % clients)
        cost = float("inf")
        for c in clients:
          for t in T.nodes():
            cTemp = self.ShortestPathsLength[t][c][0]
            if cTemp < cost:
              cost = cTemp
              closestClient = c

        chosenOrdering.append(closestClient)
        clients.remove(closestClient)
      chosenOrderingTuple = []

      for c in chosenOrdering:
        chosenOrderingTuple.append(('a', c))
      chosenOrdering = chosenOrderingTuple[:]
      improvePeriod, improveTime = Setup.get('improve_period'), Setup.get('improve_maxtime')
      chosenOrdering = Utils.addImproveSteps(chosenOrdering, improvePeriod, improveTime)
    
    elif client_ordering == Setup.RANDOM:
        # first shuffle the list
        chosenOrdering = eventsList[:]
        random.shuffle(chosenOrdering)
        log.info("shuffled list: %s" % chosenOrdering)

    else: # add clients in the given order
        chosenOrdering = eventsList

    i = 1

    for (action, arg) in chosenOrdering:
      discardTime = False # flag for reseting the event processing time when a node was already in the tree or hasn't been removed.
      Utils.STATISTICS.startEvent(arg, T.number_of_nodes(), T.edges(), T.weight, len(T.C))
      if action == 'a':
        log.debug('tree nodes before adding the client: "%s"' % T.nodes())
        log.debug('tree edges before adding the client: "%s"' % T.edges(data=True))
        if arg in T.nodes():
          discardTime = True
        T.addClient(arg)
        T.validate()
      elif action == 'r':
        T.removeClient(arg)
        if arg in T.nodes():
          discardTime = True
        T.validate()      
      elif action == 't':
        pass # treater later
      elif action == 'i':
        pass # treated later
      else:
        raise Exception("unrecognised action")

      Utils.STATISTICS.endEvent(action, arg, T.number_of_nodes(), T.edges(), T.weight, len(T.C), discardTime)

      if action == 'i':
        if (not pim_mode) and arg > 0:
          Utils.STATISTICS.startImprove(T.edges(), T.weight)
          T = ImproveMethods.improveTree(T, arg)
          T.validate()
          newWeight = T.weight
          Utils.STATISTICS.endImprove(T.edges(), T.weight)
        else:
          log.debug("action (%s, %s) discarded because of PIM mode" % (action, arg))

      i += 1

    T.validate()
    return T
