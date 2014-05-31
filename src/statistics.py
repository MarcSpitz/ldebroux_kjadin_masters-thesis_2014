# -*- coding: utf-8 -*-
# @author: Debroux Léonard  <leonard.debroux@gmail.com>
# @author: Kevin Jadin      <contact@kjadin.com>

import resource
import logging as log

class Statistics():

  def __init__(self):

    self.tickCosts      = []
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
    if index in dictionary:
      dictionary[index].append(value)
    else:
      dictionary[index] = [value]

  def startEvent(self, client, nodes=-1, edges=[], cost=-1, clients=-1):
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
    elif eventProcessingTime < 50: # todo: horrible garde parce que python compte pas bien le temps 
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
    self.edgesBeforeImprove = edges
    self.weightBeforeImprove = weight

  def endImprove(self, edges, weight):
    self.stateOfImprove.append((self.edgesBeforeImprove, edges, self.weightBeforeImprove, weight))

  def nbImproveTry(self, improveTry):
    self.improveTry.append(improveTry)

  def updateCumulatedCost(self, cost):
    self.tickCosts.append(cost)

  def getTime(self):
    # return clock()*1000 # todo: that's what we said we used in the thesis
    return self.cpu_time()*1000

  def cpu_time(self):
    return resource.getrusage(resource.RUSAGE_SELF)[0]

  ''' 
  TODO: comment
  '''
  def getTickCosts(self):
    return self.tickCosts

  ''' 
  TODO: comment
  '''
  def getImproveTry(self):
    return self.improveTry

  ''' 
  TODO: comment
  '''
  def getStateOfImprove(self):
    return self.stateOfImprove

  ''' 
  TODO: comment
  '''
  def getAdditionTimes(self):
    return self.additionTimes

  ''' 
  TODO: comment
  '''
  def getRemovalTimes(self):
    return self.removalTimes

  def reset(self):
    self.tickCosts      = []
    self.improveTry     = []
    self.stateOfImprove = [] #should contain tuples : (edgesBeforeImprove, edgesAfterImprove, weightBeforeImprove, weightAfterImprove)
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
