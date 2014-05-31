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
from pylab import boxplot, show, savefig, figure, plot, gca, tight_layout, xticks
from matplotlib.ticker import MaxNLocator
import numpy, math
from matplotlib import gridspec


from abstracttest import AbstractTest

class ImpactTest(AbstractTest):

  def impactedNodes(self, edgeList1, edgeList2):
    """ Returns the set of impacted nodes from edgeList1 to edgeList2 """
    edgeSet1 = set(edgeList1)
    edgeSet2 = set(edgeList2)

    union           = edgeSet1 | edgeSet2
    intersection    = edgeSet1 & edgeSet2

    impactedEdges   = union - intersection
    
    impactedNodes   = set()
    for e in impactedEdges:
      (n1, n2) = e
      impactedNodes.add(n1)
      impactedNodes.add(n2)

    return impactedNodes

  def addValueToDictOfList(self, dictionary, key, value):
    if key in dictionary:
      dictionary[key].append(value)
    else:
      dictionary[key] = [value]  

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
    shortest_paths_file = self.shortest_paths_file_name

    impactDict = {}
    nodesInGraph = len(NGdict[k].nodes())

    prependstr = "_".join([config_file, shortest_paths_file])
    filename = "%s_impact.txt" % (prependstr)
    log.info("writing to file %s" % filename)
        
    filename = os.path.join(self.working_directory, filename)
    f = open(filename,'w')
    
    writeNewline = self.writeNewline # shortcut
    writeNewline(filename, f)

    log.debug("nodesInGraph %s" % nodesInGraph)

    for dataSet in dataSets:
      dataSetIndex = dataSets.index(dataSet)
      setupCostList = [] # line in the array, costs for one dataset and all setups
      for s in custom_setupDicts:
        setupIndex = custom_setupDicts.index(s)
        self.log_progression(dataSetIndex+1, len(dataSets), setupIndex+1, len(custom_setupDicts), self.testname)
        
        i = 0 # should be removed because completly useless
        
        Setup.reset_setup() # start from default
        Setup.configure(s)
        
        events = self.addImproveToDataSet(dataSet) # improves will be added to dataSet while keeping dataSet intact

        if log.getLogger(__name__).isEnabledFor(log.INFO): # logs only printed if asked for
          self.print_logs()
        indexCostList = [] # cell in the array, costs for one dataset, for one setup.
        for idx in range(tests):
          log.debug('test %s' % idx)
          
          # ticks are already in the actionTuples
          _, _, _, stateOfImprove, _, _ = Utils.run_setup(NGdict[k], root, events)

          self.writeDataHeader(f, dataSetIndex, setupIndex, idx)
          i = 1
          nbOfImprove = len(stateOfImprove)
          for (edgesBefore, edgesAfter, weightBefore, weightAfter) in stateOfImprove:

            def writeImpact(edgesBefore, edgesAfter, weightBefore, weightAfter, improveNb, f):
              writeNewline('improve %s/%s' % (i, nbOfImprove), f)
              writeNewline('edges_before_improve: %s' % edgesBefore, f)
              writeNewline('weight_before_improve: %s' % weightBefore, f)
              writeNewline('edges_after_improve: %s' % edgesAfter, f)
              writeNewline('weight_after_improve: %s' % weightAfter, f)
              writeNewline('', f)

            writeImpact(edgesBefore, edgesAfter, weightBefore, weightAfter, i, f)
            i += 1

            impactedNodesAtStep = self.impactedNodes(edgesBefore, edgesAfter)
            impact = len(impactedNodesAtStep)/float(nodesInGraph)
            improve = (weightBefore - weightAfter) / float(weightBefore)

            self.addValueToDictOfList(impactDict, round(improve*100, 2), round(impact*100, 2))
            

    f.close() 


    keys = sorted(impactDict.keys())

    zeroMeasures = []
    if 0 in keys:
      zeroMeasures = impactDict[0]
      keys.remove(0)

    minKey = min(keys)
    maxKey = max(keys)
    nbBuckets = 8

    # create bins
    bucketWidth = (maxKey-minKey)/float(nbBuckets)
    bins = [minKey]
    x = minKey
    binValue = round(x, 3)
    while binValue < maxKey:
      x += bucketWidth
      binValue = round(x, 3)
      bins.append(binValue)

    #create locations at the middle of the bins
    locations = []
    for x in bins[:-1]:
      loc = x+bucketWidth/2.0
      locations.append(round(loc, 1))

    measures = []
    impacts = []

    for k in keys:
      l = impactDict[k]
      for v in l:
        measures.append(k)
      
    # building the buckets for the boxplot
    binIndex = 1
    bucketImpacts = []
    while keys:
      for k in sorted(keys): # need to sort
        if k <= bins[binIndex]:
          bucketImpacts.extend(impactDict[k])
          keys.remove(k)
        else:
          impacts.append(bucketImpacts)
          bucketImpacts = []
          binIndex += 1
          break
    impacts.append(bucketImpacts)

    # plotting

    fig = figure()

    gs = gridspec.GridSpec(1, 2, width_ratios=[11, 1]) 
    ax1 = fig.add_subplot(gs[0])


    ax1.hist(measures, bins, color='lightgreen')

    ax1.set_xlabel('Tree improvement [%]')
    ax1.set_ylabel('Nb measures')

    ax1.yaxis.set_label_position("right")

    ax2 = ax1.twinx()
    ax1.yaxis.tick_right()
    ax2.yaxis.tick_left() 

    ax1.set_xlim(left=bins[0])

    bp = ax2.boxplot(impacts, positions=locations, widths=bucketWidth/2.5, patch_artist=True)
    ax2.set_ylabel('Impacted nodes [%]')
    ax2.yaxis.set_label_position("left")
    # ax2.set_autoscalex_on(False)

    c = self.colors

    for box in bp['boxes']:
      # change outline color
      box.set( linewidth=0)
      # box.set( color='#000000', linewidth=3)
      # # change fill color
      box.set( facecolor = c['orange'] )

    ## change color and linewidth of the whiskers
    for whisker in bp['whiskers']:
        whisker.set(color=c['gray'], linewidth=2)

    ## change color and linewidth of the caps
    for cap in bp['caps']:
        cap.set(color=c['black'], linewidth=2)

    ## change color and linewidth of the medians
    for median in bp['medians']:
        median.set(color=c['black'], linewidth=5)


    # xticks(numpy.arange(numpy.floor(bins[0]), numpy.ceil(bins[-1]) ))
    for label in ax1.xaxis.get_ticklabels():
      label.set_rotation(60)

    ax3 = fig.add_subplot(gs[1])

    measures = [0]*len(measures)
    if measures and zeroMeasures:
      data = [measures, zeroMeasures]
      colors=[c['green'], c['red']]
      labels=['Used', 'Unused']
    elif not zeroMeasures:
      data = measures
      colors=c['green']
      labels='Used'
    elif not measures:
      data = zeroMeasures
      colors=c['red']
      labels='Unused'
    else:
      raise Exception('I have no data :(')

    lines = ax3.hist(data, 1, normed=0, histtype='bar', stacked=True, color=colors, label=labels)
    ax3.xaxis.set_visible(False)

    ax3.spines['right'].set_visible(False)
    ax3.spines['top'].set_visible(False)
    ax3.spines['bottom'].set_visible(False)

    ax3.xaxis.set_ticks_position('bottom')
    ax3.yaxis.set_ticks_position('left')

    tight_layout()
    
    prependstr = "_".join([config_file, shortest_paths_file])
    filename = "%s_improve.eps" % (prependstr)
    filename = os.path.join(self.working_directory, filename)
    
    log.info("writing to file %s" % filename)
    savefig(filename)
    # show()


    # """
    # See:
    # http://matplotlib.org/examples/pylab_examples/boxplot_demo.html
    # http://stackoverflow.com/questions/16592222/matplotlib-group-boxplots
    # """
    # figure()
    # bplt = boxplot(setupCosts)
    # savefig("TestStability_%s_%s_%s_%s.png" % (testname, adds, finalNbClients, iSize))

def main(argv):
  impact = ImpactTest()

  impact.run()

if __name__ == "__main__":
  main(sys.argv)
  
