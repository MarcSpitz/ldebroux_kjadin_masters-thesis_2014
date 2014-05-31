# -*- coding: utf-8 -*-
# @author: Debroux Léonard  <leonard.debroux@gmail.com>
# @author: Kevin Jadin      <contact@kjadin.com>

import resource
import logging as log

class Statistics():

  def __init__(self):

    # contains the costs of the tree after each tick in the scenario
    self.tickCosts      = []
    # contains the number of rounds of local search that could be made for each improvement
    self.improveTry     = []
    #should contain tuples : (edgesBeforeImprove, edgesAfterImprove, weightBeforeImprove, weightAfterImprove)
    self.stateOfImprove = [] 

    edgesBeforeImprove  = None
    weightBeforeImprove = -1
    self.currentClient  = None
    self.addingTime     = -1
    self.stateBeforeEvent   = None
    self.stateAfterEvent    = None
    self.stateAfterImprove  = None

    self.clientAddStartTime = -1
    self.currentTime        = -1

    self.additionTimes  = dict()
    self.removalTimes   = dict()

  def addToListDict(self, dictionary, index, value):
    ''' adds value in the list at index in dictionary '''
    if index in dictionary:
      dictionary[index].append(value)
    else:
      dictionary[index] = [value]

  def startEvent(self, client, nodes=-1, edges=[], cost=-1, clients=-1):
    ''' Start of an event, can be of any type '''
    self.clientAddStartTime   = self.getTime()
    self.currentTime          = self.getTime()
    self.currentClient        = client
    self.stateBeforeEvent  = (nodes, edges, cost, clients)

  def endEvent(self, event, arg, nodes=-1, edges=[], cost=-1, clients=-1, discardTime=False):
    ''' discardTime has been added to discard event processing time (sets it to 0) '''
    self.stateAfterEvent = (nodes, edges, cost, clients)

    (nodesBeforeEvent, _, _, _) = self.stateBeforeEvent    
    endEventTime = self.getTime()
    eventProcessingTime = endEventTime - self.clientAddStartTime
    if discardTime:
      eventProcessingTime = 0.0
    if event == 't':
      self.updateCumulatedCost(cost)
    elif eventProcessingTime < 50: # sometimes the evaluation of the time fails to work properly, guard to avoid insane values
      if    event == 'a':
        self.addToListDict(self.additionTimes, nodesBeforeEvent, eventProcessingTime)
      elif  event == 'r':
        self.addToListDict(self.removalTimes, nodesBeforeEvent, eventProcessingTime)
      else:
        pass
    else:
      log.warning("Insane time for %s: %s" % (event, eventProcessingTime))
      pass

  def startImprove(self, edges, weight):
    ''' Improvement starting, edges and weight information are cached '''
    self.edgesBeforeImprove = edges
    self.weightBeforeImprove = weight

  def endImprove(self, edges, weight):
    ''' Improvement over, the cached information is used along with the new one to store the changes made by the improvement'''
    self.stateOfImprove.append((self.edgesBeforeImprove, edges, self.weightBeforeImprove, weight))

  def nbImproveTry(self, improveTry):
    self.improveTry.append(improveTry)

  def updateCumulatedCost(self, cost):
    self.tickCosts.append(cost)


  def getTime(self):
    # return clock()*1000
    return self.cpu_time()*1000

  def cpu_time(self):
    return resource.getrusage(resource.RUSAGE_SELF)[0]


  def getTickCosts(self):
    return self.tickCosts

  def getImproveTry(self):
    return self.improveTry

  def getStateOfImprove(self):
    return self.stateOfImprove

  def getAdditionTimes(self):
    return self.additionTimes

  def getRemovalTimes(self):
    return self.removalTimes

  def reset(self):
    ''' Reset the statitics when another tree is built '''
    self.tickCosts      = []
    self.improveTry     = []
    self.stateOfImprove = [] 
    edgesBeforeImprove  = None
    weightBeforeImprove = -1

    self.currentClient  = None
    self.addingTime     = -1
    self.stateBeforeEvent   = None
    self.stateAfterEvent    = None
    self.stateAfterImprove  = None

    self.clientAddStartTime = -1
    self.currentTime        = -1

    self.additionTimes  = dict()
    self.removalTimes   = dict()
