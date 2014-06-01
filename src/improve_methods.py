# -*- coding: utf-8 -*-
# @author: Debroux Léonard  <leonard.debroux@gmail.com>
# @author: Kevin Jadin      <contact@kjadin.com>

from setup import Setup
import logging as log
from time import clock
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
    """ The number of local search rounds are arbitrary """
    for i in range(nb):
      log.info('improvement iteration %s', i)
      T.improveTreeOnce()
    T.updateTabu()
    return T

  @staticmethod
  def improveTreeAllowedFailures(T, failures=0):
    """ The search will make local search improves as long are they improve
        There is a counter of unsuccessful improve rounds,
        When this counter reaches the argument failures, the local search stops
    """
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
    """ Simulated annealing for some time
        The temperature may be re-evaluated based on the chosen temperature_schedule
        The probability to degrade is evaluate in multicasttree
    """
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