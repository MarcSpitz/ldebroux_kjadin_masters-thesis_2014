#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Debroux Léonard  <leonard.debroux@gmail.com>
# @author: Jadin   Kevin    <contact@kjadin.com>

import sys, os
from utils import Utils
from setup import Setup
import logging as log
import csv

from pylab import boxplot, show, savefig, figure, tight_layout
from matplotlib import gridspec
from matplotlib import rc


""" Similar to impact.py, the data to plot are in impactDict """

def configGraphFont():
  font = {'family' : 'monospace',
          'size'   : 18}
  rc('font', **font)

configGraphFont()

impactDict = {
  0:[0,0,0,0],
  2.5:[4.2],
  2.8:[4.8],
  5:[6.8,7,7.2],
  5.2:[6,7,7.7],
  5.5:[7.1,6.2]
}

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
ax1.set_xlim(left=bins[0])

ax2.yaxis.tick_left() 

bp = ax2.boxplot(impacts, positions=locations, widths=bucketWidth/2.5, patch_artist=True)
ax2.set_ylabel('Impacted nodes [%]')
ax2.yaxis.set_label_position("left")

c = {
      'green' :'lightgreen',
      # 'red'   :'#fd522b',
      'orange'   :'#FF6633',
      'red'   :'#ef4141',
      'gray'  :'#777777',
      'black' :'#000000',
      # 'blue'  :'#3366FF',
      'blue'  :'#2edbd9',
      'yellow':'#fce94f',
      'lightorange':'#fcaf3e'
    }

for box in bp['boxes']:
  # change outline
  box.set( linewidth=0)
  # # change fill color
  box.set( facecolor = c['orange'] )

# change color and linewidth of the whiskers
for whisker in bp['whiskers']:
    whisker.set(color=c['gray'], linewidth=2)

# change color and linewidth of the caps
for cap in bp['caps']:
    cap.set(color=c['black'], linewidth=2)

# change color and linewidth of the medians
for median in bp['medians']:
    median.set(color=c['black'], linewidth=5)

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

filename = "impact_example.eps"
log.info("writing to file %s" % filename)

tight_layout()
savefig(filename)
show()
