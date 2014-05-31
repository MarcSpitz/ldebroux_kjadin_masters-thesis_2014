# -*- coding: utf-8 -*-
# @author: Debroux Léonard  <leonard.debroux@gmail.com>
# @author: Kevin Jadin      <contact@kjadin.com>

import random
import logging as log
from statistics import Statistics
import warnings
import sys
import math
from setup import Setup

import datetime

def deprecated(func):
    """This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emmitted
    when the function is used."""
    def newFunc(*args, **kwargs):
        warnings.warn("Call to deprecated function %s." % func.__name__,
                      category=DeprecationWarning)
        return func(*args, **kwargs)
    newFunc.__name__ = func.__name__
    newFunc.__doc__ = func.__doc__
    newFunc.__dict__.update(func.__dict__)
    return newFunc

class Utils:

  STATISTICS = Statistics()

  @staticmethod
  def run_setup(NG, root, events):
    """ runs the setup. returns a tuple : (T, avgCost).
    T is the final tree computed """

    T = NG.buildMCTree(root, events)

    tickCosts = T.weight  # if no tick among the events, avgCost becomes the tree weight,
                          # just as if a fictious tick event was added the the events sequence
    try:
      tickCosts = Utils.STATISTICS.getTickCosts()
      improveTry = Utils.STATISTICS.getImproveTry()
      stateOfImprove = Utils.STATISTICS.getStateOfImprove()
      additionTimes = Utils.STATISTICS.getAdditionTimes()
      removalTimes = Utils.STATISTICS.getRemovalTimes()
    except ZeroDivisionError, e:
      # there was no tick event in the events sequence, computing the avgCost is not possible
      pass
    
    Utils.STATISTICS.reset()
    return T, tickCosts, improveTry, stateOfImprove, additionTimes, removalTimes

  @staticmethod
  def configure_logger(verbosity):
    if verbosity >= 2:
      log.basicConfig(format="%(levelname)s: %(message)s", level=log.DEBUG)
      log.info('verbosity level set to DEBUG')
    elif verbosity == 1:
      log.basicConfig(format="%(levelname)s: %(message)s", level=log.INFO)
      log.info('verbosity level set to INFO')
    else:
      log.basicConfig(format="%(levelname)s: %(message)s")

  @staticmethod
  def randomly_select_from(N, available):
    selected = random.sample(available, N)
    return selected

  @staticmethod
  def fill_client_list(clients, NG):
    clientlist = list()
    for c in clients:
      if c >= 0:
        log.debug("selected: %s" % c)
        clientlist.append(c)
      else:
        # need to perform -c random additions in the clients list
        available = [n for n in NG.nodes() if n not in clientlist]
        selected   = Utils.randomly_select_from(-c, available)
        log.debug("randomly selected: %s" % selected)
        clientlist = clientlist + selected
    return clientlist

  @staticmethod
  def generateActionTuples(actionsLine, topology):
    """
    Takes a string composed of successive actions of the form:
      {action} n1 [n2 [n3]..]
      where each token is separated be a space
    Adds a tick event after each event
    Returns a list of tokens of the form ({action}, ni) 
      where each negative occurrence of ni has been transformed 
      by a randomised selection of nodes, with a tick event between each event
    """
    actions = []      # to store the successive actions
    clients = set()   # set of clients to maintain during the execution
    tokens  = actionsLine.split()
    tokens.reverse()  # to use pop()

    currentAction = None
    while tokens: # while the list is not empty
      nextToken = tokens[-1] # peak the next-to-be-read token

      if nextToken == 'ar':
        currentAction = tokens.pop()
        adds = int(tokens.pop())
        removals = int(tokens.pop())
        arTuple = Utils.gen_client_list(adds, removals, list(topology), list(clients))
        actions = actions + arTuple
        clients = set(Utils.compute_final_clients_set(actions))
        currentAction = None # only two integer after 'ar'
        continue

      if (not currentAction) or (nextToken == "a") or (nextToken == "r") or (nextToken == "i"):
        currentAction = tokens.pop()
      node = int(tokens.pop())

      print "considering", currentAction, node
      print "clients", clients

      if node < 0:
        # determine selectionSet
        # (set among which to randomly select nodes in case the node value is negative)
        if currentAction == "a": # addition
          selectionSet  = topology - clients
          selectionSet.remove(0)
          selected      = Utils.randomly_select_from(-node, selectionSet)
          clients      |= set(selected)
          print clients
        elif currentAction == "r": # removal
          selectionSet  = clients
          selected      = Utils.randomly_select_from(-node, selectionSet)
          clients      -= set(selected)
        else:
          raise Exception("%s action cannot be used with a negative value" % currentAction)
        # add action tuples
        actions.extend([(currentAction, n,) for n in selected])

      else: # node >= 0
        tup = (currentAction, node,)
        # simply add/remove the node
        if    (currentAction == "a"):
          if (node not in clients):
            if (node in topology):
              clients.add(node)
              actions.append(tup)
            else:
              raise Exception("node %s is not in the given topology" % node)
          else:
            print "ignoring action tuple (%s,%s) because node is already in the clients set at this point of execution" % tup
        elif  (currentAction == "r"):
          if (node in clients):
            clients.remove(node)
            actions.append(tup)
          else:
            print "ignoring action tuple (%s,%s) because node is not present in the clients set at this point of execution" % tup
        elif  (currentAction == "i"):
          actions.append(tup)
          currentAction = None # force reconsideration of a new action for the next tuple
        else:
          # tup action tuple is invalid
          raise Exception("action tuple (%s,%s) is invalid" % tup)

    return actions


  @staticmethod
  def addTicks(actionTuples):
    log.debug('adding one tick event after each already existing "a" or "r" event')
    # method 1, systematic
    # ticks = [('t', i) for i in range(len(actionTuples))]
    # # merge the two lists together, putting one element of each list
    # withTicks = list(sum(zip(actionTuples, ticks), ())[:-1])
    withTicks = []
    tick = 1
    for (e, a) in actionTuples:
      withTicks.append( (e, a) )
      if (e == 'a') or (e == 'r'):
        withTicks.append( ('t', tick) )
        tick += 1
    return withTicks

  @staticmethod
  def addImproveSteps(actionTuples, ip, it):
    result = actionTuples[:]
    t = ('i', it)
    idx = -1
    while idx < len(result) - 1:
      # print result
      # print idx
      # print len(result)
      idx = idx + ip + 1
      result.insert(idx, t)

    return result

  """
  Remove an element from Python's PriorityQueue (with an intern list).
  This static method is dependent on Python's implementation of the PriorityQueue
  If the element to remove is the first in the list (the lowest element that is to be returned upon a "get"),
  we "get" it such that an update is triggered on the PriorityQueue and it stays valid wrt. its specifications.
  """
  @staticmethod
  def removeFromPriorityQueue(pq, elem):
    # print 'elem', elem
    if not elem == pq.queue[0]:
      pq.queue.remove(elem)
    else:
      pq.get()

  @staticmethod
  def orderAddRemoval(actionTuples):
    """
    Write a function for swapping instead of duplicating some portion of the code
    """
    clients = []
    index = 0
    for (action, e) in actionTuples:
      if action == "a": # client addition          
        if e in clients: # client already in tree
          if not ('r', e) in actionTuples[index:]:
            raise Exception('several additions without available removal')
          nextRemoveIndex = actionTuples[index:].index( ('r', e) ) + index
          actionTuples[index] = actionTuples[nextRemoveIndex]
          actionTuples[nextRemoveIndex] = (action, e)
          clients.remove(e)
        else:
          clients.append(e)
      elif action == "r": # ¢lient removal
        if not e in clients: # trying to remove a client that is not in the tree
          if not ('a', e) in actionTuples[index:]:
            raise Exception('trying to remove a client without available addition')
          nextAddIndex = actionTuples[index:].index( ('a', e) ) + index
          actionTuples[index] = actionTuples[nextAddIndex]
          actionTuples[nextAddIndex] = (action, e)
          clients.append(e)
        else: # client in tree
          clients.remove(e)
      index += 1
    return actionTuples

  @staticmethod
  def smart_shuffle(tuples):
    """
    Takes a list of action tuples (addition/removal) as arguments and shuffles them
    The order in which they should appear is then restored (addition before the removal)
    Discards the ('i', X) improve tuples because shuffling the improve steps has no meaning
    """
    shuffled = [(a, i) for (a, i) in tuples if a != 'i'] #filtering to remove improve steps
    random.shuffle(shuffled)
    shuffled = Utils.orderAddRemoval(shuffled)
    return shuffled

  @staticmethod
  def gen_client_list(adds, removals, nodes, clients):
    # @todo: add the capability to have a root different than 0
    # wether it is done in the specs or in the code
    a = adds
    r = removals
    if 0 in clients:
      clients.remove(0)
    actionTuples = []
    nonclients = list(set(nodes[:]) - set(clients))
    nonclients.remove(0) # 0 is the root of the tree
    s = a + r
    add = True
    while s > 0:
      if add:
        c = random.choice(nonclients)
        actionTuples.append(('a', c))
        clients.append(c)
        nonclients.remove(c)
        a -= 1
      else: 
        c = random.choice(clients)
        clients.remove(c)
        actionTuples.append(('r', c))
        nonclients.append(c)
        r -= 1

      # Evaluate next event
      s = a + r
      if not clients:
        add = True
      elif not nonclients:
        add = False
      elif s != 0:
        probaToAdd = a/float(s)
        ran = random.random()
        if ran < probaToAdd:
          add = True
        else:
          add = False
    return actionTuples

  @staticmethod
  def compute_final_clients_set(actionTuples):
    clients = []
    for (action, c) in actionTuples:
      if action == 'a':
        clients.append(c)
      elif action == 'r':
        clients.remove(c)
    return clients

  @staticmethod
  def mean(l):
    mean = sum(l)/float(len(l))
    return mean

  @staticmethod
  def generateEventDict(proba, lifeTime, ticks, nodes, root):

    # procedure that append an element in a list at index index if that list already exists
    # if index is not a key in the dictionnay d already, then, a list in initialized for that key
    def createOrAppend(d, index, elem):
      if index in d:
        d[index].append(elem)
      else:
        d[index] = [elem]


    mean = lifeTime
    var = (mean/2)**2 # arbitrarily chosen
    mu = math.log((mean**2) / math.sqrt(var + mean**2))
    sig = math.sqrt(math.log(1 + (var / float(mean**2))))

    # print 'mu', mu
    # print 'sig', sig

    eventDict = {} # given as an argument
    # clients = []
    nonClients = nodes[:]

    if not root in nonClients:
      raise Exception('The root must be a node of the topology')
    nonClients.remove(root)
    for i in range(ticks):

      if i in eventDict: # some events already exists for tick i
        for (action, arg) in eventDict[i]: # reinstate the removed clients in the potential client list
          if action != 'r':
            raise Exception("An action other than 'r' in the dictionnary at this stage can not occur")
          nonClients.append(arg)
      else:
        eventDict[i] = []

      random.shuffle(nonClients)
      for nc in nonClients:
        if random.random() <= proba:
          eventDict[i].append(('a', nc))
          nonClients.remove(nc)
          timeToLive = int(round(random.lognormvariate(mu, sig)))
          # print timeToLive
          createOrAppend(eventDict, i + timeToLive, ('r', nc))
        else:
          pass

    print 'clients', len(nodes)-len(nonClients)
    return {key: eventDict[key] for key in eventDict.keys() if key < ticks}

  @staticmethod
  def getTimeString():
    return datetime.datetime.today().strftime('%Y%m%d-%H%M%S')
