#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Debroux Léonard  <leonard.debroux@gmail.com>
# @author: Jadin   Kevin    <contact@kjadin.com>

import sys, os
from utils import Utils
from setup import Setup
import logging as log
import csv

from pylab import savefig, figure, hist, xlim, subplots, tight_layout
import numpy

from abstracttest import AbstractTest

class ComparisonTest(AbstractTest):
  """ Comparison test
      Compares several algorithm configurations on several datasets
      Outputs a comparison table csv and a plot of the number of rounds of local search for each configuration
    
      Comparison table format:
                      \|__alg0_|__alg1_|_..._|__algn_|
              dataset0_|_val00_|_val01_|_..._|_val0n_|
              ...     _|_           ...              |
              datasetm_|_valm0_|_valm1_|_..._|_valmn_|

        valij are percentages
        initially, the values on the lines are the mean of all the executions for dataset i and alg j
        lower value is expressed as 100% and all the others are computed based on this reference value

  """
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

    k = 1

    custom_setupDicts = self.setupDicts
    dataSets          = self.dataSets
    NGdict            = self.NGdict
    root              = self.root
    tests             = self.tests

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
                
        Setup.reset_setup() # start from default
        Setup.configure(s)
        
        events = self.addImproveToDataSet(dataSet) # improves will be added to dataSet while keeping dataSet intact

        if log.getLogger(__name__).isEnabledFor(log.INFO): # logs only printed if asked for
          self.print_logs()
        
        # indexCostList those are the costs that will contribute to one cell
        indexCostList = [] # cell in the array, costs for one dataset, for one setup.
        for idx in range(tests):
          log.debug('test %s' % idx)
                    
          T, tickCosts, improveTry, _, _, _ = Utils.run_setup(NGdict[k], root, events)

          self.writeDataHeader(f, dataSetIndex, setupIndex, idx)
          writeNewline('tickcosts: %s' % tickCosts, f)
          writeNewline('improvetry: %s' % improveTry, f)

          self.addListToDict(improveTriesPerSetup, setupIndex, improveTry)

          if improveTry and min(improveTry) < minImprove:
            minImprove = min(improveTry)
          if improveTry and max(improveTry) > maxImprove:
            maxImprove = max(improveTry)
          
          avgCost = numpy.mean(tickCosts)
          indexCostList.append(avgCost) 

          # export the Tree as .json format
          jsonFileName = "%s_setup-%s_index-%s.json" % (prependstr, setupIndex, idx) 
          jsonFileName = os.path.join(self.working_directory, jsonFileName)
          T.export_json(jsonFileName, avgCost)

        m = numpy.mean(indexCostList)
        s = numpy.std(indexCostList)
        log.debug('mean: %s, std: %s' % (m, s))

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
        setupCostList[i] = percentage

      # setupCostList contains percentages
      dataSetCostList.append(setupCostList)

    f.close()

    setupResults = []
    for i in range(len(custom_setupDicts)): # go through the columns of the array
      column = []
      for j in range(len(dataSets)): # go through the lines
        column.append(dataSetCostList[j][i])

      geoMean = self.geometricMean(column)
      setupResults.append(geoMean)

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
      
      r = (minImprove, maxImprove)
      ax1.hist(l, step, range=r, normed=False, histtype='bar', facecolor=c['blue'])      
      ax1.set_xlim(r) # set_xlim only for this plot
      ax1.set_xlabel('Rounds')
      ax1.set_ylabel('Nb values')
      
      tight_layout()
      savefig('%s_0.eps' % filename)

      fig, ax1 = subplots()
      ax1.hist(l, step/2.0, normed=False, histtype='bar', facecolor=c['blue'])
      ax1.set_xlabel('Rounds')
      ax1.set_ylabel('Nb values')

      tight_layout()
      savefig('%s_1.eps' % filename)

    for setup in improveTriesPerSetup.keys():
      l = improveTriesPerSetup[setup]
      if l:
        prependstr = "_".join([config_file, shortest_paths_file])
        filename = "%s_comparison_setup_%s" % (prependstr, setup)
        filename = os.path.join(self.working_directory, filename)
        
        exportHist(l, 30, filename)

def main(argv):
  comparison = ComparisonTest()
  comparison.run()

if __name__ == "__main__":
  main(sys.argv)
  