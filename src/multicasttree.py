# -*- coding: utf-8 -*-
# @author: Debroux Léonard  <leonard.debroux@gmail.com>
# @author: Kevin Jadin      <contact@kjadin.com>

import sys
import networkx as nx
import matplotlib.pyplot as plt
import networkx.algorithms.dag as dag
from operator import itemgetter
from collections import OrderedDict
import random
import logging as log
import nx_pylab
from Queue import PriorityQueue
from utils import Utils
from setup import Setup
import copy
import math


class MulticastTree(nx.DiGraph):
  """ MulticastTree class """
  def __init__(self, NetworkGraph, root):
    super(MulticastTree, self).__init__()

    self.NetworkGraph = NetworkGraph
    self.C            = set() # empty client set
    self.root         = root  # root of the tree
    self.improvements = 0  #amount of improvements made (addition and removal)

    self.weight       = 0  # weight of the tree (to be updated after every tree modification)

    self.C.add(root)
    self.add_node(root)   # add the root

    self.ttl      = Setup.get('tabu_ttl')
    self.tabuList = {}

    self.usePathQueue   = False
    self.pathQueue      = PriorityQueue()
    self.childrenPaths  = {}
    self.parentPaths    = {}

    # linking the right method according to arguments (codegen)
    self.export_step_codegen(Setup.get('steps'))
    self.selectEdge = self.selectEdge_choose(Setup.get('selection_heuristic'))

  def log(self, lvl=log.INFO):
    log.log(lvl, ">>> tree information")
    log.log(lvl, "\tweight: %s"     % self.weight)
    log.log(lvl, "\troot: %s"       % self.root)
    log.log(lvl, "\ttree clients: %s" % self.clients())

  def multicastTreeCopy(self):
    """ returns a complete copy of the tree """
    MCTcopy = MulticastTree(self.NetworkGraph, self.root)

    MCTcopy.graph = copy.deepcopy(self.graph)
    MCTcopy.node  = copy.deepcopy(self.node)
    MCTcopy.adj   = copy.deepcopy(self.adj)
    MCTcopy.pred  = copy.deepcopy(self.pred)
    MCTcopy.succ  = MCTcopy.adj
    MCTcopy.edge  = MCTcopy.adj

    MCTcopy.C = copy.deepcopy(self.C)
    MCTcopy.improvements = self.improvements

    MCTcopy.weight = self.weight

    MCTcopy.tabuList = copy.deepcopy(self.tabuList)

    MCTcopy.usePathQueue     = self.usePathQueue
    MCTcopy.pathQueue        = PriorityQueue()
    MCTcopy.pathQueue.queue  = copy.deepcopy(self.pathQueue.queue)
    MCTcopy.childrenPaths = copy.deepcopy(self.childrenPaths)
    MCTcopy.parentPaths   = copy.deepcopy(self.parentPaths)

    return MCTcopy

  def export_step_codegen(self, method):
    """ codegen the right exporting method for self.export_step() """
    fname = "export_step"
    if(method == Setup.PLOT):
      def inner(self, outfile):
        self.export_plot()
    elif(method == Setup.FILE):
      def inner(self, outfile):
        self.export_file(outfile)
    else:
      def inner(self, outfile):
        pass
    inner.__doc__  = "docstring for "+fname
    inner.__name__ = fname
    setattr(self.__class__, inner.__name__, inner)

  def export_file(self, outfile):
    """
    @param outfile : string for filename with supported extension {pdf, png}
    """
    import pylab
    pylab.figure(figsize=(50,50))

    self.draw()
    pylab.savefig(outfile)

  def export_plot(self):
    # new window
    plt.figure()
    self.draw()
    plt.show(block=False)
    # clean plot
    plt.clf()

  def draw(self):
    """ draw the tree on top of the graph """
    # draw the graph except the current tree
    graphOnlyEdges = list(set(self.NetworkGraph.edges()) - set(self.edges()))
    graphOnlyNodes = list(set(self.NetworkGraph.nodes()) - set(self.nodes()))

    ax = plt.axes()
    ax.axes.get_xaxis().set_visible(False)
    ax.axes.get_yaxis().set_visible(False)

    nx.draw_networkx(self.NetworkGraph, self.NetworkGraph.layout, ax=ax, edgelist=graphOnlyEdges, nodelist=graphOnlyNodes, font_color='white', node_color='grey', node_shape='s') #node_shape='so^>v<dph8'

    # draw the tree
    nodeSize = 500
    # draw steiner nodes
    nx.draw_networkx_nodes(self, self.NetworkGraph.layout, node_color='black', node_size=nodeSize)
    # draw the root
    nx.draw_networkx_nodes(self, self.NetworkGraph.layout, nodelist=[self.root], node_color='purple', node_size=nodeSize)
    # draw the clients
    clientsWithoutRoot = set(self.C) - set([self.root])
    nx.draw_networkx_nodes(self, self.NetworkGraph.layout, nodelist=clientsWithoutRoot, node_color='blue', node_size=nodeSize)
    # draw the edges
    edgeLabels=dict([((u,v,),d['weight']) for u,v,d in self.NetworkGraph.edges(data=True)])
    nx_pylab.draw_networkx_edges(self, self.NetworkGraph.layout, width=2.0, arrow=True, edge_color='red')
    nx.draw_networkx_edge_labels(self, self.NetworkGraph.layout, edge_labels=edgeLabels, label_pos=0.5, font_color='grey')

  def export(self, outfile):
    nx.draw_graphviz(self)
    nx.write_dot(self, outfile)

  def selectEdge_choose(self, heuristic):
    """ returns the right selectEdge heuristic according to given argument """
    if(heuristic == Setup.MOST_EXPENSIVE):
      return self.selectEdge_mostExpensive
    elif(heuristic == Setup.MOST_EXPENSIVE_PATH):
      if(Setup.get('improve_maxtime') > 0):
        self.usePathQueue = True
      return self.selectEdge_mostExpensivePath
    elif(heuristic == Setup.AVERAGED_MOST_EXPENSIVE_PATH):
      if(Setup.get('improve_maxtime') > 0):
        self.usePathQueue = True
      return self.selectEdge_averagedMostExpensivePath
    else: # use random selection heuristic
      return self.selectEdge_random

  def add_edges(self, path):
    """
    add edges with attributes fetched from the NetworkGraph
    @param: path: a path is a list of nodes [n1, n2, n3, n4, ..]
    @raise: Exception if the edge is non-existent in the NetworkGraph
    """
    NG = self.NetworkGraph
    GraphEdges = NG.edges()
    log.debug('GraphEdges: %s' % GraphEdges)

    for i in range(len(path) - 1):
      n1 = path[i]
      n2 = path[i+1]

      edgeAttributes = NG[n1][n2]
      # build and add the edge to the tree edges set
      edgeUnique = (n1, n2) if n1<n2 else (n2, n1)
      log.debug('have to add edge: (%s,%s)' % (n1, n2))
      if not edgeUnique in GraphEdges:
        raise Exception("tree is corrupted")

      self.add_edge(n1, n2, edgeAttributes)
      self.weight += self[n1][n2]['weight']

  def removeEdge(self):
    """ removes an edge from the tree
        Uses selectEdge() """
    # select an edge to remove
    edge = self.selectEdge()
    if edge:
      log.debug('selected edge: %s', edge)
      self.weight -= edge[2]['weight']
      self.remove_edge(edge[0], edge[1])
      return edge
    else:
      return None

  def clients(self):
    """ returns the clients set """
    return self.C

  def predecessor(self, node):
    """ In a tree, each node has at most one predecessor
        Redefine networkx predecessors method to reflect this fact
        @returns parent node or None if given node was the root """
    pred = self.predecessors(node)
    if pred:
      return pred[0]
    else:
      return None


#  █████╗ ██████╗ ██████╗ ██╗████████╗██╗ ██████╗ ███╗   ██╗
# ██╔══██╗██╔══██╗██╔══██╗██║╚══██╔══╝██║██╔═══██╗████╗  ██║
# ███████║██║  ██║██║  ██║██║   ██║   ██║██║   ██║██╔██╗ ██║
# ██╔══██║██║  ██║██║  ██║██║   ██║   ██║██║   ██║██║╚██╗██║
# ██║  ██║██████╔╝██████╔╝██║   ██║   ██║╚██████╔╝██║ ╚████║
# ╚═╝  ╚═╝╚═════╝ ╚═════╝ ╚═╝   ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═══╝

  def addClient(self, c):
    """ Subscribe a client to the multicast group
        Adds the client to the tree and adds the needed edges
    """
    log.debug('adding client %s' % c)
    if not c in self.nodes():
      pim_mode = Setup.get('pim_mode')
      log.debug('PIM mode: %s' % pim_mode)

      if pim_mode:
        cleanedClosestPath = self.shortestPathToSource(c)
      else:
        cleanedClosestPath = self.shortestPathToTree(c)

      log.debug('cleanedClosestPath: %s' % cleanedClosestPath)

      if self.usePathQueue:
        self.addToPathQueue(cleanedClosestPath)

      self.add_edges(cleanedClosestPath)
    
    else:
      log.debug('client %s already in clients set' % c)
    
    # add the client to the clients set
    self.C.add(c)

  def shortestPathToSource(self, client):
    """ Use when simulated the behaviour of PIM-SSM
    """
    NG = self.NetworkGraph
    # take the shortest path from the root to the client as connection path
    closestPath = NG.ShortestPaths[self.root][client][0]
    # the path must be cleaned because of edges that might have a weight of 0.
    # Consider the following example :
    # T:  n1 -0-> n2, the path n2-n1-n3 has the same weight as n1-n3. 
    # We could end up choosing the first path and thus create a loop
    cleanedClosestPath = self.cleanPath(closestPath, self.nodes(), [client])
    return cleanedClosestPath

  def shortestPathToTree(self, client):
    """ Returns the shortest path from the client to add to the tree
    """
    NG = self.NetworkGraph
    ShortestPathsLength = NG.ShortestPathsLength[client]
    log.debug('distances to nodes: "%s"' % ShortestPathsLength)
    PathsLengthToTree = {k: v[0] for k, v in ShortestPathsLength.items() if k in self.nodes()}
    log.debug('PathsLengthToTree: %s' % PathsLengthToTree)   
    SortedPathsLengthToTree = OrderedDict(sorted(PathsLengthToTree.items(), key=itemgetter(1))) 
    log.debug('SortedPathsLengthToTree: %s' % SortedPathsLengthToTree)
    closestParent, parentLength = SortedPathsLengthToTree.popitem(last=False)
    log.debug('closestParent: %s' % closestParent)

    closestPath = NG.ShortestPaths[closestParent][client][0]
    # the path must be cleaned because of edges that might have a weight of 0.
    # Consider the following example :
    # T:  n1 -0-> n2, the path n2-n1-n3 has the same weight as n1-n3. 
    # We could end up choosing the first path and thus create a loop
    cleanedClosestPath = self.cleanPath(closestPath, self.nodes(), [client])
    return cleanedClosestPath


# ██████╗ ███████╗███╗   ███╗ ██████╗ ██╗   ██╗ █████╗ ██╗     
# ██╔══██╗██╔════╝████╗ ████║██╔═══██╗██║   ██║██╔══██╗██║     
# ██████╔╝█████╗  ██╔████╔██║██║   ██║██║   ██║███████║██║     
# ██╔══██╗██╔══╝  ██║╚██╔╝██║██║   ██║╚██╗ ██╔╝██╔══██║██║     
# ██║  ██║███████╗██║ ╚═╝ ██║╚██████╔╝ ╚████╔╝ ██║  ██║███████╗
# ╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝ ╚═════╝   ╚═══╝  ╚═╝  ╚═╝╚══════╝

  def removeClient(self, c):
    """ removes given client c from the clients set of self 
    """
    if c == self.root:
      log.error('root cannot be removed from the client set')
    elif c in self.C:
      deg = self.degree(c)
      self.C.remove(c)
      if deg == 1:
        # Upon a removal, the tree is only modified when the degree of the node is one
        (node, removedEdges) = self.ascendingClean(c, list())
        # here, the path is removed already
        self.removeWeightFor(removedEdges)

        if self.usePathQueue:
          # The modifications of the tree cause the pathQueue to change
          pathTuple = self.parentPaths[c]
          if node == self.root:
            # the clean goes up to the root, it means that pathTuple goes from root to c, just remove it
            if pathTuple[1][0] != self.root: # root should be the first node of pathTuple
              print ''
              print 'paths', self.pathQueue.queue
              print 'edges', self.edges()
              print 'node', node
              print 'client removed', c
              raise Exception("Upon removal, cleaning was made up to root and the path is bad")
            self.removeTupleFromPathQueue(pathTuple, tryMerge=False)
          elif self.degree(node) == 1:
            # node is a client
            if node in self.parentPaths:
              self.removeTupleFromPathQueue(pathTuple)
            else: 
              # node has no parent path (means that a path should be split)
              self.splitPathAroundNode(node, pathTuple, removeBotPath=True)

          elif self.degree(node) == 2:
            if node in self.parentPaths:
              # removed path and try merge on node
              self.removeTupleFromPathQueue(pathTuple, tryMerge=True)
            else:
              # node was previously of degree 3, and is in the middle of path. 
              # it thus has only one child path
              if len(self.childrenPaths[node]) != 1:
                raise Exception("bug: childrenPath[node] should have a length of one")
              childPathTuple = self.childrenPaths[node][0]
              if childPathTuple == pathTuple:
                # remove path, no need to try to merge
                self.removeTupleFromPathQueue(pathTuple, tryMerge=False)
              else:
                self.splitPathAroundNode(node, pathTuple, removeBotPath=True)
                self.mergePaths(node)
                # split path on node, rm botPath and try merge on node
              
          else: # degree(node) >= 3
            if not pathTuple[1][0] == node:
              # if node is within pathTuple, pathTuple must be split
              self.splitPathAroundNode(node, pathTuple, removeBotPath=True)
            else:
              self.removeTupleFromPathQueue(pathTuple, tryMerge=False)

        log.debug("removed edges upon removal of %s: %s" % (c, removedEdges))
      elif deg == 2:
        log.debug("client %s of deg == 2 to remove", c)
        self.mergePaths(c)
      else: # deg >= 3
        log.debug("client %s of deg >=3 to remove", c)
    else:
      log.error("%s is not in the clients set", c)


# ██╗███╗   ███╗██████╗ ██████╗  ██████╗ ██╗   ██╗███████╗
# ██║████╗ ████║██╔══██╗██╔══██╗██╔═══██╗██║   ██║██╔════╝
# ██║██╔████╔██║██████╔╝██████╔╝██║   ██║██║   ██║█████╗  
# ██║██║╚██╔╝██║██╔═══╝ ██╔══██╗██║   ██║╚██╗ ██╔╝██╔══╝  
# ██║██║ ╚═╝ ██║██║     ██║  ██║╚██████╔╝ ╚████╔╝ ███████╗
# ╚═╝╚═╝     ╚═╝╚═╝     ╚═╝  ╚═╝ ╚═════╝   ╚═══╝  ╚══════╝

  def improveTreeOnce(self, nb, temperature):
    """ performs one round of improvement on the tree

    # procedure: 3 steps for each round of improvement
    # 1) select and remove one edge
    # 2) clean the tree by launching cleanTree on the two nodes linked by the removed edge
    # 3) add a new path -> O(n^2) search for the shortest path to link the two components
    """
    folder = "images/"

    if self.improvements < 10:
      temp = "00" + str(self.improvements)
    elif self.improvements < 100:
      temp = "0" + str(self.improvements)
    else:
      temp = str(self.improvements)
    self.export_step(folder+"%s_step0_before_improve.png" % (temp))
    
    # remove an edge from the graph
    removed = self.removeEdge()

    if removed:
      parent, child, edgeAttributes = removed
      self.export_step(folder+"%s_step1_(%s-%s)_edge_removed.png" % (temp, parent, child))
      
      # from this point, the DiGraph is made of at least two connected components
      subRoot, removedEdges = self.cleanTree(parent, child)
      self.export_step(folder+"%s_step2_(%s-%s)_cleaned_tree.png" % (temp, parent, child))

      newPathInstalled, degrading = self.reconnectCC(subRoot, removedEdges, temperature)
      self.export_step(folder+"%s_step3_(%s-%s)_reconnected_components.png" % (temp, parent, child))
      
      self.improvements += 1
      return (newPathInstalled, degrading)
    else:
      log.debug('no edge found to remove')
      return (False, False) # no new path has been installed

    if not self.number_of_nodes() == self.number_of_edges()+1:
      print 'ERROR nodes:', self.number_of_nodes(), 'edges:', self.number_of_edges(), ': should not be reached'
      print 'edges', self.edges()
      print 'paths', self.pathQueue.queue
      raise Exception('the multicast tree is does not represent a tree after an improveOnce call')


# ███████╗██████╗  ██████╗ ███████╗    ███████╗███████╗██╗     ███████╗ ██████╗████████╗██╗ ██████╗ ███╗   ██╗
# ██╔════╝██╔══██╗██╔════╝ ██╔════╝    ██╔════╝██╔════╝██║     ██╔════╝██╔════╝╚══██╔══╝██║██╔═══██╗████╗  ██║
# █████╗  ██║  ██║██║  ███╗█████╗      ███████╗█████╗  ██║     █████╗  ██║        ██║   ██║██║   ██║██╔██╗ ██║
# ██╔══╝  ██║  ██║██║   ██║██╔══╝      ╚════██║██╔══╝  ██║     ██╔══╝  ██║        ██║   ██║██║   ██║██║╚██╗██║
# ███████╗██████╔╝╚██████╔╝███████╗    ███████║███████╗███████╗███████╗╚██████╗   ██║   ██║╚██████╔╝██║ ╚████║ 
# ╚══════╝╚═════╝  ╚═════╝ ╚══════╝    ╚══════╝╚══════╝╚══════╝╚══════╝ ╚═════╝   ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═══╝
                                                                                   
  def selectEdge_random(self):
    """ randomly selects and returns an edge to remove from the tree """
    edges = self.edges(data=True)
    found = False
    selectedEdge = None

    while not found and edges:
      selectedEdge = random.choice(edges)
      n1, n2, attr = selectedEdge
      if (n1, n2) in self.tabuList:
        edges.remove(selectedEdge)
      else: 
        found = True
    return selectedEdge

  def selectEdge_mostExpensive(self):
    """ selects and returns the most expensive edge in the tree """
    edges = self.edges(data=True)
    selectedEdge = None
    weight = -1;
    # equalWeights use to be fair in the case of several paths having the same cost and being the most expensive
    equalWeights = 2.0
    for e in edges:
      n1, n2, attr = e
      if not (n1, n2) in self.tabuList:
        if attr['weight'] > weight:
          selectedEdge = e
          weight = attr['weight']
          equalWeights = 2.0
        elif attr['weight'] == weight:
          if random.random() < 1/equalWeights:
            selectedEdge = e
            equalWeights += 1
    return selectedEdge

  def selectEdge_mostExpensivePath(self):
    """ selects and returns the most expensive edge in the tree """
    if self.usePathQueue:
      mostExpPath = self.popFirstValidPath(Setup.get('max_paths'))
      if mostExpPath:
        n1 = mostExpPath[0]
        n2 = mostExpPath[1]
        return (n1, n2, self.NetworkGraph[n1][n2])
      else:
        return None

  def selectEdge_averagedMostExpensivePath(self):
    if self.usePathQueue:
      mostExpPath = self.popFirstValidPath(Setup.get('max_paths'))
      if mostExpPath:
        n1 = mostExpPath[0]
        n2 = mostExpPath[1]
        return (n1, n2, self.NetworkGraph[n1][n2])
      else:
        return None

  def popFirstValidPath(self, maxPaths = 3):
    """ pops the first valid path found in the pathQueue (which can contain invalid/non-split paths).
        pops them in order and returns the first valid path. 
    """
    returnPathTuple = None
    toRestore       = []
    validPaths      = []

    valid = False
    while self.pathQueue.queue and len(validPaths) < maxPaths:
      valid     = True

      pathTuple = self.pathQueue.queue[0]
      # check if given path is valid : no coloured node or node with degree > 2
      _, path   = pathTuple
      for n in path[1:-1]:
        if (n in self.C) or (self.degree(n) > 2):
          valid = False
          self.splitPathAroundNode(n, pathTuple)
          break # breaks the for loop

      if valid:
        # check if one of the edges of the path is in the tabu
        for i in range(len(path) - 1):
          n1 = path[i]
          n2 = path[i+1]
          if ((n1, n2) in self.tabuList) or ((n2, n1) in self.tabuList):
            valid = False
            poppedPathTuple = self.pathQueue.get() # when a path is in the tabu, pop it
            if not poppedPathTuple == pathTuple:
              raise Exception("PathQueue is corrupted")
            toRestore.append(poppedPathTuple)
            break
        if valid:
          # add the valid path to the list of valid paths (one will be selected later on)
          poppedPathTuple = self.pathQueue.get() 
          # the current considered path will be added to validPaths
          # it must be removed from the priority queue so that another may be selected
          if not poppedPathTuple == pathTuple:
            raise Exception("PathQueue is corrupted")
          validPaths.append(poppedPathTuple)

    for p in toRestore:
      # restore all the paths that were removed because in the tabu
      self.pathQueue.put(p)

    if validPaths:
      chosenPathTuple = random.choice(validPaths)
      for p in validPaths:
        # restore all the paths that were removed because chosen in validPaths
        self.pathQueue.put(p)
      self.removeTupleFromPathQueue(chosenPathTuple)
      return chosenPathTuple[1]

    else:
      return None


#  ██████╗██╗     ███████╗ █████╗ ███╗   ██╗██╗███╗   ██╗ ██████╗ 
# ██╔════╝██║     ██╔════╝██╔══██╗████╗  ██║██║████╗  ██║██╔════╝ 
# ██║     ██║     █████╗  ███████║██╔██╗ ██║██║██╔██╗ ██║██║  ███╗
# ██║     ██║     ██╔══╝  ██╔══██║██║╚██╗██║██║██║╚██╗██║██║   ██║
# ╚██████╗███████╗███████╗██║  ██║██║ ╚████║██║██║ ╚████║╚██████╔╝
#  ╚═════╝╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝╚═╝  ╚═══╝ ╚═════╝ 

  def cleanTree(self, parent, child):
    """ cleans the tree, by launching
        ascending clean from given parent node
        descending clean from given child node
        @returns: one node from the child connected component (or None)
        as well as the list of edges that have been removed
    """
    asc   = self.ascendingClean(parent, list())
    desc  = self.descendingClean(child, list())

    self.removeWeightFor(asc[1])
    self.removeWeightFor(desc[1])

    removedEdge   = (parent, child)
    removedEdges  = asc[1]
    removedEdges.reverse()
    removedEdges.append(removedEdge)
    removedEdges  = removedEdges + desc[1]

    return (desc[0], removedEdges)

  def removeWeightFor(self, path):
    """ decrements self's weight by the cumulative weight of the given path 
    """
    for e in path:
      self.weight -= self.NetworkGraph[e[0]][e[1]]['weight']

  def ascendingClean(self, current, removedEdges):
    """ launches an ascendingClean procedure:
        @returns: one node from the tree (the first undeleted node, or None) 
    """
    log.debug('clients: %s' % self.C)
    log.debug('current: %s' % current)
    if (current in self.C) or (self.degree(current) >= 2):
      log.debug('current kept: %s' % current)
      return (current, removedEdges)
    else:
      log.debug('predecessors: %s' % self.predecessors(current))
      parent      = self.predecessors(current)[0] #only one element in the list if any
      self.remove_node(current)
      removedEdge = (parent, current)
      removedEdges.append(removedEdge)
      log.debug('current removed: %s and parent is: %s' % (current, parent))
      return self.ascendingClean(parent, removedEdges)

  def descendingClean(self, current, removedEdges):
    """ launches an descendingClean procedure:
        @returns: one node from the tree (the first undeleted node, or None) 
    """
    if (current in self.C) or (self.degree(current) >= 2):
      return (current, removedEdges)
    else:
      child = self.successors(current)[0]
      self.remove_node(current)
      removedEdge = (current, child)
      removedEdges.append(removedEdge)
      return self.descendingClean(child, removedEdges)

  def cleanPath(self, path, sT, dT):
    """ cleans a path from the edges it contains that already are in the tree (in one direction or the other).
        Needed to avoid creating loops in the tree upon reconnection
        @param: path: the path to clean
    """
    cleanedPath = []
    firstInST = 0
    for i in reversed(range(len(path))):
      if path[i] in sT:
        cleanedPath.append(path[i])
        firstInST = i
        break
    for i in range(firstInST+1, len(path)):
      if not path[i] in dT:
        cleanedPath.append(path[i])
      else:
        cleanedPath.append(path[i])
        break

    return cleanedPath


# ██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗███╗   ██╗███████╗ ██████╗████████╗██╗ ██████╗ ███╗   ██╗ 
# ██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║████╗  ██║██╔════╝██╔════╝╚══██╔══╝██║██╔═══██╗████╗  ██║  
# ██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║██╔██╗ ██║█████╗  ██║        ██║   ██║██║   ██║██╔██╗ ██║ 
# ██╔══██╗██╔══╝  ██║     ██║   ██║██║╚██╗██║██║╚██╗██║██╔══╝  ██║        ██║   ██║██║   ██║██║╚██╗██║  
# ██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║██║ ╚████║███████╗╚██████╗   ██║   ██║╚██████╔╝██║ ╚████║  
# ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═══╝╚══════╝ ╚═════╝   ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═══╝

  def reconnectCC(self, subRoot, removedEdges, temperature, onlyBest=False):
    """ aims at reconnecting the two connected components after an edge removal
        potentially inverts edge directions
        @returns: False when he reconnection path is the same as the previously removed one 
    """
    # select a path (at least one edge) to add (may be the same one)
    newPathInstalled = True
    log.debug('subRoot: %s' % subRoot)

    # desc = set of nodes from the subtree
    desc = dag.descendants(self, subRoot).union(set([subRoot]))
    # sourceTree = set of nodes from the source tree
    sourceTree  = set(self.nodes()) - desc
    
    bestPath, degrading = self.selectReconnectionPath(sourceTree, desc, removedEdges, temperature)

    if not bestPath:
      log.debug("no improving path could be found for reconnecting the two components, restoring the previously removed edges..")
      bestPath = self.edgePathToNodePath(removedEdges)
      newPathInstalled = False

    log.debug('descendants : %s' % desc)
    log.debug('sourceTree  : %s' % sourceTree)
    log.debug('bestPath    : %s' % bestPath)
    log.debug('removedEdges: %s' % self.edgePathToNodePath(removedEdges))

    if not bestPath[-1] == subRoot:
      # attempt to reroot
      self.reRoot(bestPath[-1], subRoot)

    if self.usePathQueue:
      self.addToPathQueue(bestPath)

    self.addPathToTabu(bestPath)
    self.add_edges(bestPath)

    return (newPathInstalled, degrading)

  def selectReconnectionPath(self, sourceTreeNodes, descTreeNodes, removedEdges, temperature):
    """ selects reconnection path between the two components 
        considers pairs of nodes from the two given sets source/descTreeNodes
        applies the search_strategy parameter 
        allows to degrade with probability derived from given temperature only if intensify_only parameter is set to False """
    
    removedPath = self.edgePathToNodePath(removedEdges)
    toImprove   = self.NetworkGraph.getEdgePathWeight(removedEdges)
    log.debug("cost to improve : toImprove = %s" % toImprove)

    intensify   = Setup.get('intensify_only')
    nbNodesInST = min([Setup.get('improve_search_space'), len(sourceTreeNodes)]) 

    sourceTreeNodesList = list(sourceTreeNodes)
    descTreeNodesList   = list(descTreeNodes)

    sourceTreeNodesList = random.sample(sourceTreeNodesList, nbNodesInST)
    
    degrading = False # we intensify if possible

    improvingPath         = None
    improvingPathCost     = sys.maxint
    lessDegradingPath     = None
    lessDegradingPathCost = sys.maxint

    search_strategy = Setup.get('search_strategy')

    for stn in sourceTreeNodesList:
      for dtn in descTreeNodesList:
        log.debug("considered reconnection : (%s, %s)" % (stn, dtn))

        sPW = self.NetworkGraph.ShortestPathsLength[stn][dtn][0]

        if sPW < toImprove and sPW < improvingPathCost:  
          improvingPath = (stn, dtn)
          improvingPathCost = sPW

        # sPW >= toImprove
        # if intensify = True, no need to check for a lessDegradingPath
        elif (not intensify) and (sPW < lessDegradingPathCost):
          sP = self.NetworkGraph.ShortestPaths[stn][dtn][0]
          if (sP != removedPath):
            lessDegradingPath = sP
            lessDegradingPathCost = sPW

      if (search_strategy == Setup.FIRST_IMPROVEMENT) and improvingPath:
        break

    if improvingPath:
      (stn, dtn) = improvingPath
      sP = self.NetworkGraph.ShortestPaths[stn][dtn][0]
      cleanedImpPath = self.cleanPath(sP, sourceTreeNodes, descTreeNodes)
      return (cleanedImpPath, degrading)

    elif not intensify and lessDegradingPath:
      cleanedPath = self.cleanPath(lessDegradingPath, sourceTreeNodes, descTreeNodes)
      if cleanedPath != removedPath:
        cPWeight = self.NetworkGraph.getNodePathWeight(cleanedPath)
        if cPWeight < toImprove:
          degrading = False # because the path is improving, although useless, for readability
          return (cleanedPath, degrading)
        else: # cPWeight >= toImprove
          degrading = self.evaluateSAProbability(toImprove, cPWeight, temperature)
        if degrading:
          return (cleanedPath, degrading)

    return (None, degrading)

  def nodePathToEdgePath(self, nodePath):
    """ converts a path expressed as [n1, n2, n3] to the tuple representation [(n1, n2), (n2, n3), (n3, n3)] 
    """
    returnedList = []
    for i in range(len(nodePath) - 1):
      n1 = nodePath[i]
      n2 = nodePath[i+1]
      returnedList.append((n1, n2,))
    return returnedList

  def edgePathToNodePath(self, edgePath):
    """ converts a path expressed as tuple representation [(n1, n2), (n2, n3), (n3, n3)] 
        to a list of nodes representation: [n1, n2, n3] 
    """
    n1, n2    = edgePath[0]
    nodePath  = [n1, n2]
    for e in edgePath[1:]:
      n1, n2 = e
      if not n1 == nodePath[-1]:
        raise Exception("EdgePath is not correct")
      nodePath.append(n2)
    return nodePath


# ████████╗ █████╗ ██████╗ ██╗   ██╗
# ╚══██╔══╝██╔══██╗██╔══██╗██║   ██║
#    ██║   ███████║██████╔╝██║   ██║
#    ██║   ██╔══██║██╔══██╗██║   ██║
#    ██║   ██║  ██║██████╔╝╚██████╔╝
#    ╚═╝   ╚═╝  ╚═╝╚═════╝  ╚═════╝ 

  def addPathToTabu(self, path):
    """ adds given path to the tabu list with initial ttl value 
    """
    for i in range(len(path) - 1):
      n1  = path[i]
      n2  = path[i+1]
      e   = (n1, n2)
      self.tabuList[e] = self.ttl+1

  def updateTabu(self):
    """ updates the tabu list: decrements all values by 1 and remove keys when such values reach 0 
    """
    for e in self.tabuList.copy():
      if(self.tabuList[e] == 1):
        del self.tabuList[e]
      else:
        self.tabuList[e] = self.tabuList[e] - 1

  def emptyTabu(self):
    """ empty the tabu list 
    """
    self.tabuList = {}


# ██████╗ ███████╗██████╗  ██████╗  ██████╗ ████████╗
# ██╔══██╗██╔════╝██╔══██╗██╔═══██╗██╔═══██╗╚══██╔══╝
# ██████╔╝█████╗  ██████╔╝██║   ██║██║   ██║   ██║   
# ██╔══██╗██╔══╝  ██╔══██╗██║   ██║██║   ██║   ██║   
# ██║  ██║███████╗██║  ██║╚██████╔╝╚██████╔╝   ██║   
# ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝ ╚═════╝  ╚═════╝    ╚═╝  

  def reRoot(self, newRoot, oldRoot):
    """ launches a reroot procedure from given oldRoot to given newRoot 
    """
    # when rerooting, some paths may be inverted, and thus, must change in the path priority queue
    # if oldRoot is a black node and is now of degree 2, two paths must be merged into one

    # Has to be done first, before inverting the edges in the tree.
    if self.usePathQueue:
      newRootInsideAPath = not newRoot in self.parentPaths
      if newRootInsideAPath:
        # need to do a split before inverting the paths up to the oldRoot
        self.splitPathContainingNewRoot(newRoot, oldRoot)

      # invert paths from newRoot to oldRoot
      if not newRoot in self.parentPaths:
        raise Exception("reRoot failed")

      self.invertPathsFromNewRootToOldRoot(newRoot, oldRoot)

      # attempt to connect paths together at oldRoot
      self.mergePaths(oldRoot)

    n1      = newRoot
    parents = self.predecessors(n1)
    while parents:
      # parents of tree nodes can have at most 1 element
      n2      = parents[0]
      parents = self.predecessors(n2)
      e       = self[n2][n1]
      self.remove_edge(n2, n1)      

      self.add_edge(n1, n2, e)
      n1 = n2


# ██████╗  █████╗ ████████╗██╗  ██╗ ██████╗ ██╗   ██╗███████╗██╗   ██╗███████╗
# ██╔══██╗██╔══██╗╚══██╔══╝██║  ██║██╔═══██╗██║   ██║██╔════╝██║   ██║██╔════╝
# ██████╔╝███████║   ██║   ███████║██║   ██║██║   ██║█████╗  ██║   ██║█████╗  
# ██╔═══╝ ██╔══██║   ██║   ██╔══██║██║▄▄ ██║██║   ██║██╔══╝  ██║   ██║██╔══╝  
# ██║     ██║  ██║   ██║   ██║  ██║╚██████╔╝╚██████╔╝███████╗╚██████╔╝███████╗
# ╚═╝     ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝ ╚══▀▀═╝  ╚═════╝ ╚══════╝ ╚═════╝ ╚══════╝

  def invertPathsFromNewRootToOldRoot(self, newRoot, oldRoot):
    """ rerooting case when a rerooting needs to be done from oldRoot to newRoot.
        Invert all the paths from oldRoot to newRoot 
    """
    currentRoot = newRoot
    toInvert    = []

    while currentRoot != oldRoot:
      # parentPath is the path to invert
      if not currentRoot in self.parentPaths:
        # it means that currentRoot has a childPath that leads to the previous currentRoot, 
        # but is not in a path, that path has to be split
        self.splitPathContainingNewRoot(currentRoot, oldRoot)

      parentPathTuple = self.parentPaths[currentRoot]
      toInvert.append(parentPathTuple)

      # update the currentRoot to the last element of the parentPath
      currentRoot = parentPathTuple[1][0]

    # inversion must be done after climbing the tree
    # top-down inversion to avoid messing with the parentPaths data structure
    toInvert.reverse()
    for t in toInvert:
      self.invertPath(t)

  def splitPathContainingNewRoot(self, newRoot, oldRoot):
    """ transform the case when newRoot is inside a path into the simpler case when 
        there is a path starting and ending at newRoot
        newRoot is the node where the split is to be done 
    """
    borderNodeFound = False
    pathContainingNewRoot = None
    n1 = newRoot

    while not borderNodeFound:
      parents = self.predecessors(n1)

      if parents: # n1 has a predecessor (is not a root)
        parent = parents[0]
        if parent in self.childrenPaths: # the node parent has children paths
          for p in self.childrenPaths[parent]:
            if newRoot in p[1]: # if new root is in one of the children paths of parent
              borderNodeFound = True
              pathContainingNewRoot = p
              break
        n1 = parent
      else:
        # parents is empty, n1 should be oldRoot
        if n1 == oldRoot:
          raise Exception("Error in path splitting while rerooting, no path seems to contain newRoot")
        else:
          raise Exception("Error in path splitting while rerooting, a root different from oldRoot has been reached")
    self.splitPathAroundNode(newRoot, pathContainingNewRoot)

  def addToPathQueue(self, path):
    """ pre:  the path should be in the right way, that is, the first node 
              of the path is the one that is part of the tree component containing the root
        The path should not have already been added to the tree
        Called whenever a path is added to the tree 
    """
    pathWeight  = self.NetworkGraph.getNodePathWeight(path)
    pathTuple   = (-pathWeight, path)

    self.addTupleToPathQueue(pathTuple)

  def addTupleToPathQueue(self, pathTuple):
    """ adds a tuple to the path queue 
        each tuple contains a path and its weight (negated)
    """
    n1 = pathTuple[1][0]  # first node of the path
    n2 = pathTuple[1][-1] # last node of the path

    if n1 == n2:
      print ''
      print 'edges', self.edges()
      print 'paths', self.pathQueue.queue
      print pathTuple
      raise Exception("Bad path, begins and ends with the same node. Shouldn't happen n1 == n2 %s", n1)

    self.pathQueue.put(pathTuple)
    self.addChildPath(pathTuple, n1)
    self.addParentPath(pathTuple, n2)
    
  def addChildPath(self, pathTuple, node):
    if not node in self.childrenPaths:
      self.childrenPaths[node] = [pathTuple]
    else:
      self.childrenPaths[node].append(pathTuple)

  def addParentPath(self, pathTuple, node):
    self.parentPaths[node] = pathTuple

  def removeChildPath(self, pathTuple, node):
    self.childrenPaths[node].remove(pathTuple)
    if not self.childrenPaths[node]: # if the list becomes empty, remove the key
      del self.childrenPaths[node]

  def removeParentPath(self, pathTuple, node):
    if not pathTuple == self.parentPaths[node]:
      raise Exception('removeParentPath failed')
    del self.parentPaths[node]

  def removeTupleFromPathQueue(self, pathTuple, tryMerge = True):
    n1 = pathTuple[1][0] # first node of the path
    n2 = pathTuple[1][-1] # last node of the path

    Utils.removeFromPriorityQueue(self.pathQueue, pathTuple)
    self.removeChildPath(pathTuple, n1)
    self.removeParentPath(pathTuple, n2)

    # try to merge
    if tryMerge:
      self.mergePaths(n1)
      self.mergePaths(n2)

  def replacePaths(self, toRemove, toAdd):
    for p in toRemove:
      self.removeTupleFromPathQueue(p, False)
    for p in toAdd:
      self.addTupleToPathQueue(p)

  def mergePaths(self, node):
    """ attempts to merge the paths around the given node """
    if (not node in self.C):
      if (node in self.parentPaths) and (node in self.childrenPaths):
        childrenTuples  = self.childrenPaths[node]
        parentTuple     = self.parentPaths[node]
        if (len(childrenTuples) == 1) and (parentTuple):
          childTuple = childrenTuples[0] # there is only one childTuple

          newPath   = parentTuple[1][:]
          newPath.extend(childTuple[1][1:])
          newWeight = parentTuple[0]+childTuple[0]
          newTuple  = (newWeight, newPath)

          self.replacePaths([childTuple, parentTuple], [newTuple])

  def splitPathAroundNode(self, node, pathTuple, removeBotPath=False):
    """ splits the path contained in pathTuple in two paths around node
        The three data structures pathQueue, parentPaths and childrenPaths are updated """
    weight, path = pathTuple
    if not node in path:
      raise Exception('A path cannot be split around a node if the node is not in the path')

    nodeIndex = path.index(node)

    topPath   = path[:(nodeIndex+1)]
    botPath   = path[nodeIndex:]
    topWeight = -self.NetworkGraph.getNodePathWeight(topPath)
    botWeight = weight - topWeight
    topTuple  = (topWeight, topPath)
    botTuple  = (botWeight, botPath)

    if removeBotPath:
      self.replacePaths([pathTuple], [topTuple])
    else:
      self.replacePaths([pathTuple], [topTuple, botTuple])

  def invertPath(self, pathTuple):
    """ for given pathTuple (weight, path), invert all of its edges 
        (childrenPaths and parentPaths data structures are updated in 
        subsequent calls to add/removeTupleFrom/ToPathQueue) """
    pWeight, path     = pathTuple
    oldRoot, newRoot  = path[0], path[-1]
    
    reversedPath = path[:]
    reversedPath.reverse()

    newPathTuple = (pWeight, reversedPath)
    self.replacePaths([pathTuple], [newPathTuple])


# ███████╗██╗███╗   ███╗██╗   ██╗██╗      █████╗ ████████╗███████╗██████╗     
# ██╔════╝██║████╗ ████║██║   ██║██║     ██╔══██╗╚══██╔══╝██╔════╝██╔══██╗    
# ███████╗██║██╔████╔██║██║   ██║██║     ███████║   ██║   █████╗  ██║  ██║    
# ╚════██║██║██║╚██╔╝██║██║   ██║██║     ██╔══██║   ██║   ██╔══╝  ██║  ██║    
# ███████║██║██║ ╚═╝ ██║╚██████╔╝███████╗██║  ██║   ██║   ███████╗██████╔╝    
# ╚══════╝╚═╝╚═╝     ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═════╝     
                                                                            
#  █████╗ ███╗   ██╗███╗   ██╗███████╗ █████╗ ██╗     ██╗███╗   ██╗ ██████╗   
# ██╔══██╗████╗  ██║████╗  ██║██╔════╝██╔══██╗██║     ██║████╗  ██║██╔════╝   
# ███████║██╔██╗ ██║██╔██╗ ██║█████╗  ███████║██║     ██║██╔██╗ ██║██║  ███╗  
# ██╔══██║██║╚██╗██║██║╚██╗██║██╔══╝  ██╔══██║██║     ██║██║╚██╗██║██║   ██║  
# ██║  ██║██║ ╚████║██║ ╚████║███████╗██║  ██║███████╗██║██║ ╚████║╚██████╔╝  
# ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝╚══════╝╚═╝╚═╝  ╚═══╝ ╚═════╝ 

  def evaluateSAProbability(self, oldWeight, newWeight, temperature):
    """
    returns True if we want to replace paths according to the temperature and their weights
    If newWeight is higher than oldWeight (this corresponds to a degradation),
      return True with probability exp( -(newWeight-oldWeight) / temperature)
                  else return False
    If newWeight is lower than oldWeight (this corresponds to an improvement),
      return True
    """
    delta = 100*(newWeight - oldWeight)/(float(newWeight))
    if delta > 0:
      # degrading
      temperature = float(temperature) # ensure we don't divide by an integer
      if temperature == 0.0:
        # do not degrade when temperature is zero
        return False

      val = math.exp(-delta/temperature)
      r = random.random()
      if r < val:
        # print when a degradation is accepted
        # from __future__ import print_function
        # sys.stdout.write('|')
        # print '|',
        return True
      else:
        return False
    else:
      # improving
      return True


# ██╗   ██╗ █████╗ ██╗     ██╗██████╗  █████╗ ████████╗██╗ ██████╗ ███╗   ██╗
# ██║   ██║██╔══██╗██║     ██║██╔══██╗██╔══██╗╚══██╔══╝██║██╔═══██╗████╗  ██║
# ██║   ██║███████║██║     ██║██║  ██║███████║   ██║   ██║██║   ██║██╔██╗ ██║
# ╚██╗ ██╔╝██╔══██║██║     ██║██║  ██║██╔══██║   ██║   ██║██║   ██║██║╚██╗██║
#  ╚████╔╝ ██║  ██║███████╗██║██████╔╝██║  ██║   ██║   ██║╚██████╔╝██║ ╚████║
#   ╚═══╝  ╚═╝  ╚═╝╚══════╝╚═╝╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═══╝

  def validate(self):
    """ validates that self is a valid multicast service with respect to the inner clients set """
    treeNodes = dag.descendants(self, self.root)
    treeNodes.add(self.root)

    # the tree rooted at self.root is the only component of the multicasttree 'self'
    assert set(self.nodes()) == treeNodes

    # every client of the multicast group is a node of the multicasttree 'self'
    assert self.C.issubset(treeNodes)

    # there is no loop in the tree
    assert len(self.nodes()) == len(self.edges()) + 1

  def validatePIMTree(self):
    """ validates that self follows the PIM's shortest path-based way of building multicast trees """
    log.debug("ensurePIMTree")
    
    T = self
    NG      = T.NetworkGraph
    clients = T.C
    root    = T.root

    # compute PIM tree edges
    shortestPaths = [NG.ShortestPaths[root][c][0] for c in clients]
    log.debug("shortestPaths %s" % shortestPaths)

    PIMTreeEdgesSet = set()
    
    for nodesPath in shortestPaths:
      edgesPath = T.nodePathToEdgePath(nodesPath)
      PIMTreeEdgesSet |= set(edgesPath)

    log.debug("PIMTreeEdgesSet %s" % PIMTreeEdgesSet)
    
    # this tree edges
    treeEdgesSet = set(T.edges())

    diff = PIMTreeEdgesSet ^ treeEdgesSet

    log.debug("diff %s" % diff)
    if diff:
      raise Exception("the given tree does not follow the PIM mode for tree building!")
