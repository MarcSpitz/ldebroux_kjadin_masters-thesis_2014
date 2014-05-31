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
from pylab import boxplot, show, savefig, figure, plot, hist, xlim, gca, subplots, tight_layout
from matplotlib.ticker import MaxNLocator
import numpy

from abstracttest import AbstractTest

class ComparisonTest(AbstractTest):
 
  def positiveRealRoot(self, n, r):
    roots = numpy.roots([1]+[0]*(r-1)+[-n])
    for r in roots:
      if r.imag == 0.0 and r.real >= 0:
        # return the first and only root that is real and positive
        return r.real

  def geometricMean(self, l):
    product = reduce(lambda x, y: x*y, l)
    return self.positiveRealRoot(product, len(l))

  def addListToDict(self, dictionary, index, l):
    if index in dictionary:
      dictionary[index].extend(l)
    else:
      dictionary[index] = l

  def run(self):

    timestr = Utils.getTimeString()
    log.info("test started at: %s" % timestr)

    k = 1 # unused

    custom_setupDicts = self.setupDicts
    dataSets          = self.dataSets
    NGdict            = self.NGdict
    root              = self.root
    tests             = self.tests

    # testname            = self.testname
    config_file         = self.config_file
    shortest_paths_file = self.shortest_paths_file_name
    refColumn           = self.refColumn

    prependstr = "_".join([config_file, shortest_paths_file])
    filename = "%s_comparison.txt" % (prependstr) 
    filename = os.path.join(self.working_directory, filename)
    
    log.info("writing to file %s" % filename)
    f = open(filename,'w')
    
    writeNewline = self.writeNewline # shortcut
    writeNewline(filename, f)

    #         \|__alg0_|__alg1_|_..._|__algn_|
    # dataset0_|_val00_|_val01_|_..._|_val0n_|
    # ...     _|_           ...              |
    # datasetm_|_valm0_|_valm1_|_..._|_valmn_|

    # valij is a percentage
    # initially, the values on the lines are the mean of all the executions for dataset i and alg j
    # lower value is expressed as 100% and all the others are computed based on this reference value

    dataSetCostList = [] # array
    improveTriesPerSetup = {}
    maxImprove = 0
    minImprove = sys.maxint

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

        if log.getLogger(__name__).isEnabledFor(log.INFO): # logs only printed if asked for
          self.print_logs()
        indexCostList = [] # cell in the array, costs for one dataset, for one setup.
        for idx in range(tests):
          log.debug('test %s' % idx)
          
          # TODO: test_custom asks for a dataSet that is a list of tuples, may need to change
          
          # ticks are already in the actionTuples
          _, tickCosts, improveTry, _, _, _ = Utils.run_setup(NGdict[k], root, events)

          self.writeDataHeader(f, dataSetIndex, setupIndex, idx)
          writeNewline('tickcosts: %s' % tickCosts, f)
          writeNewline('improvetry: %s' % improveTry, f)

          self.addListToDict(improveTriesPerSetup, setupIndex, improveTry)

          if improveTry and min(improveTry) < minImprove:
            minImprove = min(improveTry)
          if improveTry and max(improveTry) > maxImprove:
            maxImprove = max(improveTry)
          
          # avgCost = sum(tickCosts)/float(len(tickCosts))
          avgCost = numpy.mean(tickCosts)

          indexCostList.append(avgCost) 

        m = numpy.mean(indexCostList)
        s = numpy.std(indexCostList)
        log.debug('mean: %s, std: %s' % (m, s))
        # print 'min: ', min(indexCostList), ', mean: ', m, ', std: ', numpy.std(indexCostList), ', max: ', max(indexCostList)
        # indexCostList those are the costs that will contribute to one cell
        setupCostList.append(m) # this is the content of one cell

      # setupCostList contains means of the $tests$ avgCost
      log.debug("setupCostList: %s" % setupCostList)

      # format setupCostList with percentages
      if refColumn > -1 and refColumn < len(setupCostList):
        minSetupCost = setupCostList[refColumn]
      else:
        minSetupCost = float(min(setupCostList))

      for i in range(len(setupCostList)):
        percentage = setupCostList[i]/minSetupCost # *100 to have 100% = 100 and not 100% = 1
        # setupCostList[i] = round(percentage, 4)
        setupCostList[i] = percentage

      # setupCostList contains percentages

      dataSetCostList.append(setupCostList)

    setupResults = []
    for i in range(len(custom_setupDicts)): # go through the columns of the array
      column = []
      for j in range(len(dataSets)): # go through the lines
        column.append(dataSetCostList[j][i])
      # geoMean = round(self.geometricMean(column), 4)
      geoMean = self.geometricMean(column)
      setupResults.append(geoMean)

    # intermediary plot
    log.info("dataSetCostList")
    for line in dataSetCostList:
      log.info(line)
    
    log.info('Geometric Mean: %s' % setupResults)  

    # output a csv to be used later on
    prependstr = "_".join([config_file, shortest_paths_file])
    filename = "%s_comparison.csv" % (prependstr)
    filename = os.path.join(self.working_directory, filename)

    log.info("writing to file %s" % filename)

    setupsHeader = ["setup%s" % i for i in range(len(custom_setupDicts))]
    header = setupsHeader

    delimiter_str = ','
    ofile  = open(filename, "wb")
    writer = csv.writer(ofile,
                        delimiter=delimiter_str,
                        # quotechar='"',
                        # quoting=csv.QUOTE_ALL
                        )
    writer.writerow(header)
    lines = dataSetCostList
    significant_figures = 3

    i = 1
    for row in lines:
      rowRounded = [round(v, significant_figures) for v in row]
      towrite = rowRounded
      i = i+1
      writer.writerow(towrite)

    geoMeansRounded = [round(v, significant_figures) for v in setupResults]
    writer.writerow(geoMeansRounded)


    def exportHist(l, step, filename):

      c = self.colors

      fig, ax1 = subplots()
      # print l
      r = (minImprove, maxImprove)
      # bw = (maxImprove - minImprove)/step
      # if bw == 0:
      #   bw = 1
      # print 'range', r 
      ax1.hist(l, step, range=r, normed=False, histtype='bar', facecolor=c['blue'])
      # hist(l, bins = range(minImprove,maxImprove+bw,bw), normed=False, histtype='bar', facecolor=(0.5, 0.8, 0.6))
      
      ax1.set_xlim(r) # @todo: pourquoi ce n'est fait qu'une fois?
      #alors qu'ax1 est redefini!

      ax1.set_xlabel('Rounds')
      ax1.set_ylabel('Nb values')
      
      # ax1.set_autoscalex_on(False) # prevents from scaling
      tight_layout()

      savefig('%s_0.eps' % filename)

      fig, ax1 = subplots()
      # print l
      # r = (minImprove, maxImprove)
      # bw = (maxImprove - minImprove)/step
      # if bw == 0:
      #   bw = 1
      # print 'range', r 


      # @todo: pourquoi ne pas mettre range=r ici???
      ax1.hist(l, step/2.0, normed=False, histtype='bar', facecolor=c['blue'])
      # hist(l, bins = range(minImprove,maxImprove+bw,bw), normed=False, histtype='bar', facecolor=(0.5, 0.8, 0.6))
      # ax1.set_xlim(r)
      ax1.set_xlabel('Rounds')
      ax1.set_ylabel('Nb values')

      # ax1.set_autoscalex_on(False) # prevents from scaling
      tight_layout()

      savefig('%s_1.eps' % filename)

    for setup in improveTriesPerSetup.keys():
      # print 'setup', setup
      l = improveTriesPerSetup[setup]
      if l:
        prependstr = "_".join([config_file, shortest_paths_file])
        filename = "%s_comparison_setup_%s" % (prependstr, setup)
        filename = os.path.join(self.working_directory, filename)
        
        exportHist(l, 30, filename)


    # def exportHist(l, step, filename):
      
    #   # print l
    #   r = (minImprove, maxImprove)
    #   # bw = (maxImprove - minImprove)/step
    #   # if bw == 0:
    #   #   bw = 1
    #   # print 'range', r 
    #   hist(l, step, range=r, normed=True, histtype='step')# or 'bar', facecolor='#3366FF')
    #   # hist(l, bins = range(minImprove,maxImprove+bw,bw), normed=False, histtype='bar', facecolor=(0.5, 0.8, 0.6))
    #   xlim(r)
      
    # figure()
    # goodSetups = []
    # for setup in improveTriesPerSetup.keys():
    #   # print 'setup', setup
    #   l = improveTriesPerSetup[setup]
    #   if l:
    #     goodSetups.append(l)
    #     # filename = "%s_%s_%s_comparison_setup_%s.eps" % (config_file, timestr, shortest_paths_file, setup)
    #     # filename = os.path.join(self.working_directory, filename)
    #     # exportHist(l, 30, filename)
    # filename = "%s_%s_%s_comparison_setup_.eps" % (config_file, timestr, shortest_paths_file)
    # filename = os.path.join(self.working_directory, filename)
    # exportHist(goodSetups, 20, filename)
    # savefig(filename)




    # """
    # See:
    # http://matplotlib.org/examples/pylab_examples/boxplot_demo.html
    # http://stackoverflow.com/questions/16592222/matplotlib-group-boxplots
    # """
    # figure()
    # bplt = boxplot(setupCosts)
    # savefig("TestStability_%s_%s_%s_%s.png" % (testname, adds, finalNbClients, iSize))


def main(argv):
  comparison = ComparisonTest()

  comparison.run()

if __name__ == "__main__":
  main(sys.argv)
  