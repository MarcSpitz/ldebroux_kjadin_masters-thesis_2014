# -*- coding: utf-8 -*-
# @author: Debroux Léonard  <leonard.debroux@gmail.com>
# @author: Kevin Jadin      <contact@kjadin.com>

from setup import Setup
import logging as log
from time import clock
import random
import copy
from utils import Utils

class ImproveMethods:

  """
  General improvement method, behaviour defined according to arguments
  TODO
  """
  @staticmethod
  def improveTree(T, improveTime):
    # return ImproveMethods.improveNSwaps(T)
    # return ImproveMethods.improveTreeAllowedFailures(T, 20)
    return ImproveMethods.improveSA(T, improveTime)

  @staticmethod
  def improveNSwaps(T, nb=1):
    for i in range(nb):
      log.info('improvement iteration %s', i)
      T.improveTreeOnce()
    T.updateTabu()
    return T

  @staticmethod
  def improveTreeAllowedFailures(T, failures=0):
    if False:
      swapping = False
    else:
      swapping = True
    failedSwapsLeft = failures
    while swapping and (failedSwapsLeft > 0):
      swapping, degrading = T.improveTreeOnce()
      # the improve was not successful, we try again for failedSwapsLeft times.
      if ((not swapping) or degrading) and (failedSwapsLeft > 0):
        swapping = True
        failedSwapsLeft -= 1

    T.updateTabu()
    return T

  @staticmethod
  def improveSA(T, maxTime):
    t = clock()
    currentTime = clock()
    elapsedTime = (currentTime - t)*1000
    bestTree = T.multicastTreeCopy()
    bestCost = T.weight
    nbImproveTry = 0
    T.emptyTabu()
    temperature = Setup.TEMPERATURE

    while elapsedTime < maxTime:
      nbImproveTry += 1

      if Setup.get('temperature_schedule') == Setup.LINEAR:
        temperature = (maxTime - elapsedTime)/10.0
      newPathInstalled, degrading = T.improveTreeOnce(nbImproveTry, temperature)
      T.updateTabu()

      if T.weight < bestCost:
        # keep the best tree seen so far
        bestTree = T.multicastTreeCopy()
        bestCost = T.weight

      currentTime = clock()
      elapsedTime = (currentTime - t)*1000

    Utils.STATISTICS.nbImproveTry(nbImproveTry)

    return bestTree