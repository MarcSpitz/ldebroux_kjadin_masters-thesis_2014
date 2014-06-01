#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Debroux Léonard  <leonard.debroux@gmail.com>
# @author: Kevin Jadin      <contact@kjadin.com>

import networkx as nx

# reference: http://en.wikipedia.org/wiki/Yen%27s_algorithm 
# pseudocode

# function YenKSP(Graph, source, sink, K):
#    // Determine the shortest path from the source to the sink.
#    A[0] = Dijkstra(Graph, source, sink);
#    // Initialize the heap to store the potential kth shortest path.
#    B = [];
   
#    for k from 1 to K:
#        // The spur node ranges from the first node to the next to last node in the shortest path.
#        for i from 0 to size(A[k − 1]) − 1:
           
#            // Spur node is retrieved from the previous k-shortest path, k − 1.
#            spurNode = A[k-1].node(i);
#            // The sequence of nodes from the source to the spur node of the previous k-shortest path.
#            rootPath = A[k-1].nodes(0, i);
           
#            for each path p in A:
#                if rootPath == p.nodes(0, i):
#                    // Remove the links that are part of the previous shortest paths which share the same root path.
#                    remove p.edge(i, i + 1) from Graph;
           
#            // Calculate the spur path from the spur node to the sink.
#            spurPath = Dijkstra(Graph, spurNode, sink);
           
#            // Entire path is made up of the root path and spur path.
#            totalPath = rootPath + spurPath;
#            // Add the potential k-shortest path to the heap.
#            B.append(totalPath);
           
#            // Add back the edges that were removed from the graph.
#            restore edges to Graph;
                   
#        // Sort the potential k-shortest paths by cost.
#        B.sort();
#        // Add the lowest cost path becomes the k-shortest path.
#        A[k] = B[0];
#        B.pop();
   
#    return A;

def k_shortest_path(G, src, dst, K = 1):
  if K < 1:
    raise Exception("K must be higher than 1")

  dijkstra = nx.single_source_dijkstra

  # returns a single list of nodes from the source to the destination
  fullcost, fullpath = dijkstra(G, source = src, target = dst, weight = 'weight')

  cost = fullcost[dst]
  path = list(fullpath[dst])

  A = [(cost, path)]
  B = list()
  removed_edges = list()

  for k in range(K-1):
    Ak = A[k]
    Ak_cost, Ak_path = Ak
    for i in range(len(Ak_path)-1):
      spurNode = Ak_path[i]
      rootPath = Ak_path[:i+1]
      #recompute rootPath_cost based on the node list
      rootPath_cost = cost_from_path(G, rootPath)

      for p_cost, p_path in A:
        if rootPath == p_path[:i+1]:
          # if rootPath is identical for both paths
          # remove the links that are part of the previous shortest paths which share the same rootPath
          nextNode = p_path[i+1]         
          if G.has_edge(spurNode, nextNode):
            d = G.edge[spurNode][nextNode]
            removed_edges.append( (spurNode, nextNode, d) )
            G.remove_edge(spurNode, nextNode)
          else:
            # the edge has already been removed from the graph
            pass


      # Modifies the graph in place to remove the adjacent edges to the root path (except for the spurNode)
      rootPathAdjacentEdges = G.edges(rootPath[:-1], data=True)
      G.remove_edges_from(rootPathAdjacentEdges)
      spurPath_cost, spurPath_path = dijkstra(G, source = spurNode, target = dst, weight='weight')
      G.add_edges_from(rootPathAdjacentEdges)

      if not dst in spurPath_path.keys():
        # dijkstra was not successful
        pass
      else:
        spurPath_cost   = spurPath_cost[dst]
        spurPath_path   = list(spurPath_path[dst])
        totalPath_path  = rootPath + spurPath_path[1:]
        totalPath_cost  = rootPath_cost + spurPath_cost
        B.append((totalPath_cost, totalPath_path))    
      G.add_edges_from(removed_edges)
      removed_edges = list()

    if len(B) > 0:
      B.sort(key=lambda tup: tup[0]) # in-place sorting according to path costs
      best = B[0]
      A.append(best) # add the best path as k's best path
      del B[0]
    else:
      # B is empty, nothing to consider
      break
  return A

# reads graph edges' weight information to compute and return path cost
def cost_from_path(G, path):
  path_length = len(path)
  cost = 0
  attribute_str = 'weight'

  for i in range(path_length-1):
    n1    = path[i]
    n2    = path[i+1]
    cost  += G[n1][n2][attribute_str]
  return cost

def get_shortest_paths(G, K):

  shortestPath        = dict()
  shortestPathLength  = dict()
  # The structure below (shortestPathCount) is redundant with the others, but can be used for convenience
  shortestPathCount   = dict()

  nodes   = G.nodes()
  length  = len(nodes)

  # the loop is such that paths are not computed in both directions
  # this cannot be done if the edges of the graph are directed
  for i in range(length):
    n1 = nodes[i]
    shortestPath[n1]        = dict()
    shortestPathLength[n1]  = dict()
    shortestPathCount[n1]   = dict()
    
    for j in range(i+1):
      n2    = nodes[j]
      paths = k_shortest_path(G, n1, n2, K)
      pathsToN2       = list()
      pathsToN2Length = list()
      pathsToN1       = list()
      pathsToN1Length = list()
      for p in paths:
        l = p[1]
        pathsToN2.append(l)
        pathsToN2Length.append(p[0])
        r = l[:]
        r.reverse()
        pathsToN1.append(r)
        pathsToN1Length.append(p[0])

      shortestPath[n1][n2]        = pathsToN2
      shortestPathLength[n1][n2]  = pathsToN2Length
      shortestPathCount[n1][n2]   = len(pathsToN2)

      shortestPath[n2][n1]        = pathsToN1
      shortestPathLength[n2][n1]  = pathsToN1Length
      shortestPathCount[n2][n1]   = len(pathsToN1)    

  return(shortestPath, shortestPathLength, shortestPathCount)


def testing(argv):
  # full mesh graph
  G = nx.complete_graph(4)
  # rewrite weights
  weights = {e:1 for e in G.edges()}
  nx.set_edge_attributes(G, 'weight', weights)
  sp = k_shortest_path(G, 0, 1, K=7)

  sP, sPL, sPC = get_shortest_paths(G, 7)
  log.info('shortest paths: %s', sP)
  log.info('shortest paths length: %s', sPL)
  log.info('shortest paths count: %s', sPC)


if __name__ == "__main__":
  import sys
  testing(sys.argv)
