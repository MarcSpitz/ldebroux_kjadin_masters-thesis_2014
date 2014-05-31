#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Debroux Léonard  <leonard.debroux@gmail.com>
# @author: Jadin   Kevin    <contact@kjadin.com>

import sys, os, random
import subprocess
from utils import Utils
from setup import Setup
import logging as log
import csv

from networkgraph import NetworkGraph
from pylab import boxplot, show, savefig, figure, plot, subplots, gca, tight_layout
from matplotlib.ticker import MaxNLocator
from matplotlib import cm
import numpy

from abstracttest import AbstractTest

class AdditionRemovalTimeTest(AbstractTest):

  def run(self):

    timestr = Utils.getTimeString()
    log.info("test started at: %s" % timestr)
    
    k = 1 # unused

    additionTimesList = [] # list of dicts
    removalTimesList  = []

    custom_setupDicts = self.setupDicts
    dataSets          = self.dataSets
    NGdict            = self.NGdict
    root              = self.root
    tests             = self.tests

    # testname            = self.testname
    config_file         = self.config_file
    shortest_paths_file = self.shortest_paths_file

    prependstr = "_".join([config_file, shortest_paths_file])
    filename_add = "%s_addition.txt" % (prependstr)
    filename_rem = "%s_removal.txt" % (prependstr)
        
    filename_add = os.path.join(self.working_directory, filename_add)
    filename_rem = os.path.join(self.working_directory, filename_rem)
    
    log.info("exporting to files %s and %s" % (filename_add, filename_rem))

    f_add = open(filename_add,'w')
    f_rem = open(filename_rem,'w')
    
    writeNewline = self.writeNewline # shortcut
    writeNewline(filename_add, f_add)
    writeNewline(filename_rem, f_rem)

    for dataSet in dataSets:
      dataSetIndex = dataSets.index(dataSet)
      setupCostList = [] # line in the array, costs for one dataset and all setups
      for s in custom_setupDicts:
        setupIndex = custom_setupDicts.index(s)
        self.log_progression(dataSetIndex+1, len(dataSets), setupIndex+1, len(custom_setupDicts), self.testname)
        
        i=0 # should be removed because completly useless
        
        Setup.reset_setup() # start from default
        Setup.configure(s)
        
        events = self.addImproveToDataSet(dataSet) # improves will be added to dataSet while keeping dataSet intact
        # TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO
        # TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO
        # TODO list needs to be modified so that the improves are added to it
        # TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO
        # TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO
        if log.getLogger(__name__).isEnabledFor(log.INFO): # logs only printed if asked for
          self.print_logs()
        indexCostList = [] # cell in the array, costs for one dataset, for one setup.
        for idx in range(tests):
          log.debug('test %s' % idx)
          
          # TODO: test_custom asks for a dataSet that is a list of tuples, may need to change
          
          # ticks are already in the actionTuples
          _, _, _, _,additionTimes, removalTimes = Utils.run_setup(NGdict[k], root, events)

          self.writeDataHeader(f_add, dataSetIndex, setupIndex, idx)
          writeNewline('%s' % additionTimes, f_add)
          
          self.writeDataHeader(f_rem, dataSetIndex, setupIndex, idx)
          writeNewline('%s' % removalTimes, f_rem)

          # dump dictionaries to file
          
          additionTimesList.append(additionTimes)
          removalTimesList.append(removalTimes)

    f_add.close()
    f_rem.close()


    # merge dictionaries
    mergedAdditionTimesDict = dict()
    mergedRemovalTimesDict  = dict()

    def addListToDict(dictionary, index, l):
      if index in dictionary:
        dictionary[index].extend(l)
      else:
        dictionary[index] = l

    def mergeList(mergedDict, dictList):
      for dictionary in dictList:
        for (k, l) in dictionary.iteritems():
          addListToDict(mergedDict, k, l)

    mergeList(mergedAdditionTimesDict, additionTimesList)
    mergeList(mergedRemovalTimesDict, removalTimesList)

    def infoTimes(timesDict):
      return {i:(min(timesDict[i]), (sum(timesDict[i])/float(len(timesDict[i]))), max(timesDict[i])) for i in timesDict.keys()}

    # final avg 
    infoAdditionTimes = infoTimes(mergedAdditionTimesDict)
    infoRemovalTimes = infoTimes(mergedRemovalTimesDict)
    log.debug("infoAdditionTimes %s" % infoAdditionTimes)
    log.debug("infoRemovalTimes  %s" % infoRemovalTimes)

    # TODO: only take into account time that are large enough (do not consider times that are super low because the node was in the tree already)


    import itertools
    # def get_range(dictionary, begin, end):
    #   return dict(itertools.islice(dictionary.iteritems(), begin, end))

    def get_range(dictionary, begin, end):
      return dict((k, v) for k, v in dictionary.iteritems() if begin <= k < end)

    def mean(l):
      if not l:
        # print 'zero'
        return 0
      return sum(l)/float(len(l))

    def plotDict(infoDict):
      keys = sorted(infoDict.keys())
      xMin = keys[0]
      xMax = keys[-1]+1
      # print keys
      # print 'min', xMin
      # print 'max', xMax
      nbSteps = 10
      stepSize = (xMax - xMin)/float(nbSteps)
      nbData = []
      nbNul = []
      meanData = []
      index = []
      for s in range(nbSteps):
        # kInStep = [k in keys if k >= xMin+s*stepSize and k < xMin+(s+1)*stepSize]
        # todo:check limit values, the last key is not taken
        data = []
        # for k in range(xMin+s*stepSize, xMin+(s+1)*stepSize):
        #   if k in keys:
        #     for v in infoDict[k]:
        rbegin = xMin+s*stepSize
        rend = xMin+(s+1)*stepSize
        # print 'r.begin', rbegin
        # print 'r.end', rend
        r = get_range(infoDict, rbegin, rend)
        # print 'r', r
        for k, v in r.iteritems():
          for t in v:
            # print (t)
            if t > 0.1: # to prevent wrong estmation of the time by python
              nbData.append(k)
              data.append(t)
            else:
              nbNul.append(k)
        # print 'data', data
        m = mean(data)
        # if m == 0:
        #   print r
        meanData.append(m)
        # TODO: not well centered
        xIndex = (rend + rbegin)/2.0
        index.append(xIndex)

      # print 'nbData', nbData
      # print 'nbNul', nbNul
      # print 'meanData', meanData
      # print 'index', index

      # import numpy as np
      # from pylab import hist
      # mu = 100 # mean of distribution
      # sigma = 15 # standard deviation of distribution
      # x = mu + sigma * np.random.randn(10000)

      # num_bins = 50

      # hist(x, num_bins, normed=1, facecolor='green', alpha=0.5)
      # show()

      c = self.colors

      fig, ax1 = subplots()
      ax1.set_xlabel('Nodes in the tree')

      data = None
      colors = None
      labels = None
      if nbData and nbNul:
        data = [nbData, nbNul]
        colors=[c['green'], c['red']]
        labels=['Used', 'Unused']
      elif not nbNul:
        data = nbData
        colors=c['green']
        labels='Used'
      elif not nbData:
        data = nbNul
        colors=c['red']
        labels='Unused'
      else:
        raise Exception('I have no data :(')

      ax1.hist(data, nbSteps, normed=0, histtype='bar', stacked=True, color=colors, label=labels)
      # ax1.hist([nbData, nbNul], nbSteps, normed=0, histtype='bar', stacked=True, facecolor=cm.summer(0))
      # ax1.hist(nbData, nbSteps, normed=0, alpha=0.1)
      ax1.set_ylabel('Nb measures')

      locations = {
        'best'         : 0, #(only implemented for axis legends)
        'upper right'  : 1,
        'upper left'   : 2,
        'lower left'   : 3,
        'lower right'  : 4,
        'right'        : 5,
        'center left'  : 6,
        'center right' : 7,
        'lower center' : 8,
        'upper center' : 9,
        'center'       : 10
      }


      lg = ax1.legend(loc=locations['lower right'], prop={'size':16})#,  title='Data', frameon=True)

      # lg.draw_frame(False)
      lg.get_frame().set_edgecolor('white')

      ax2 = ax1.twinx()
      ax2.plot(index, meanData, 'k', marker='o', markersize=10, linewidth=3, color=c['black'])
      ax2.set_ylabel('Time [ms]')

      gca().xaxis.set_major_locator(MaxNLocator(prune='lower'))

      tight_layout()

      # hist here

      # plotLists = dict(min=list(), mean=list(), max=list())
      # for key in keys:
      #   minVal, meanVal, maxVal = infoDict[key]
      #   plotLists['min'].append(minVal)
      #   plotLists['mean'].append(meanVal)
      #   plotLists['max'].append(maxVal)
      # plot(keys, plotLists['min'], 'b', keys, plotLists['mean'], 'g', keys, plotLists['max'], 'r')

    # print 'add times', infoAdditionTimes
    plotDict(infoAdditionTimes)
    prependstr = "_".join([config_file, shortest_paths_file])
    filename = "%s_addition.eps" % (prependstr)
    filename = os.path.join(self.working_directory, filename)
    
    log.info("writing to file %s" % filename)
    savefig(filename)

    figure()

    # print 'rem times', infoRemovalTimes
    plotDict(infoRemovalTimes)
    prependstr = "_".join([config_file, shortest_paths_file])
    filename = "%s_removal.eps" % (prependstr)
    filename = os.path.join(self.working_directory, filename)
    
    log.info("writing to file %s" % filename)
    savefig(filename)


    # """
    # See:
    # http://matplotlib.org/examples/pylab_examples/boxplot_demo.html
    # http://stackoverflow.com/questions/16592222/matplotlib-group-boxplots
    # """
    # figure()
    # bplt = boxplot(setupCosts)
    # savefig("TestStability_%s_%s_%s_%s.png" % (testname, adds, finalNbClients, iSize))

def main(argv):
  artt = AdditionRemovalTimeTest()

  artt.run()

if __name__ == "__main__":
  main(sys.argv)
  
