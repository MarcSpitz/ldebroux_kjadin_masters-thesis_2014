# -*- coding: utf-8 -*-
# @author: Debroux Léonard  <leonard.debroux@gmail.com>
# @author: Kevin Jadin      <contact@kjadin.com>

import sys
import logging as log

class Setup:

  RANDOM               = "RANDOM"
  MOST_EXPENSIVE       = "MOST_EXPENSIVE"
  MOST_EXPENSIVE_PATH  = "MOST_EXPENSIVE_PATH"
  AVERAGED_MOST_EXPENSIVE_PATH  = "AVERAGED_MOST_EXPENSIVE_PATH"

  WEIGHT    = "WEIGHT"
  GEO       = "GEO"
  BANDWIDTH = "BANDWIDTH"
  NONE      = "NONE"
  
  ORDERED        = "ORDERED"
  RANDOM         = "RANDOM"
  CLOSEST_TREE   = "CLOSEST_TREE"

  FIRST_IMPROVEMENT = "FIRST_IMPROVEMENT"
  BEST_IMPROVEMENT  = "BEST_IMPROVEMENT"

  CONSTANT = "CONSTANT"
  LINEAR   = "LINEAR"

  OFF     = "OFF"
  PLOT    = "PLOT"
  FILE    = "FILE"

  # used to store the temperature value to use in case the CONSTANT schedule is selected
  TEMPERATURE = 10

  PARAMETERS_DEFINITION = dict(
                selection_heuristic   = dict(
                                          default=  MOST_EXPENSIVE, 
                                          choices= [RANDOM,
                                                    MOST_EXPENSIVE,
                                                    MOST_EXPENSIVE_PATH,
                                                    AVERAGED_MOST_EXPENSIVE_PATH]
                                        ),
                client_ordering       = dict(
                                          default=  ORDERED, 
                                          choices= [ORDERED,
                                                    RANDOM,
                                                    CLOSEST_TREE]
                                        ),
                tabu_ttl              = dict(
                                          default=  50
                                        ),
                intensify_only        = dict(
                                          default=  False
                                        ),
                pim_mode              = dict(
                                          default=  False
                                        ),
                search_strategy       = dict(
                                          default=  BEST_IMPROVEMENT, 
                                          choices= [FIRST_IMPROVEMENT,
                                                    BEST_IMPROVEMENT]
                                        ),
                improve_period        = dict(
                                          default=  1
                                        ),
                improve_maxtime       = dict(
                                          default=  25
                                        ),
                improve_search_space  = dict(
                                          default=  sys.maxint
                                        ),
                temperature_schedule  = dict(
                                          default=  LINEAR, 
                                          choices= [LINEAR,
                                                    CONSTANT]
                                        ),
                k_shortest_paths      = dict(
                                          default=  1
                                        ),
                max_paths             = dict(
                                          default=  1
                                        ),
                steps                 = dict(
                                          default=  OFF, 
                                          choices= [OFF,
                                                    PLOT,
                                                    FILE]
                                        ),
                statistics_dump_file  = dict(
                                          default=  None
                                        ),
                )

  PARAMETERS = {}

  @staticmethod
  def default_setup():
    return {key:definition['default'] for key, definition in Setup.PARAMETERS_DEFINITION.iteritems()}

  @staticmethod
  def get(paramName):
    return Setup.PARAMETERS[paramName]

  @staticmethod
  def getChoices(paramName):
    if not paramName in Setup.PARAMETERS_DEFINITION:
      raise Exception('%s unrecognised parameter' % paramName)
    paramDefinition = Setup.PARAMETERS_DEFINITION[paramName]
    if not 'choices' in paramDefinition:
      raise Exception('%s parameter is not an enumeration' % paramName)
  
  @staticmethod
  def getDefault(paramName):
    if not paramName in Setup.PARAMETERS_DEFINITION:
      raise Exception('%s unrecognised parameter' % paramName)
    paramDefinition = Setup.PARAMETERS_DEFINITION[paramName]
    return paramDefinition['default']

  @staticmethod
  def merge(setup1, setup2):
    """ keys present in both setup1 and setup2 take value from setup2
        doesn't check if keys are valid 
    """
    return dict(setup1.items() + setup2.items())

  @staticmethod
  def configure(d):
    """ merges the given setup dictionary d with the current setup 
    """
    for k, v in d.iteritems():
      if not k in Setup.PARAMETERS_DEFINITION:
        raise Exception('%s unrecognised parameter' % k)
      Setup.PARAMETERS[k] = v

  @staticmethod
  def reset_setup():
    for (k, v) in Setup.default_setup().iteritems():
      Setup.PARAMETERS[k] = v

  @staticmethod
  def log():
    for (k, v) in Setup.PARAMETERS.iteritems():
      log.debug("%20s = %s" % (k, v))

  @staticmethod
  def autocast(parameter, value):
    typ = type(Setup.getDefault(parameter))
    try:
      return typ(value)
    except ValueError:
      pass
