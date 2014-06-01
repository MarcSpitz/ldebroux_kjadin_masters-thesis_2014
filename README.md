# Local search for Multicast in Software-Defined Networks #

Thesis submitted for the Master's Degree in Computer Science and Engineering

Repository location: <http://thesis.kjadin.com>

Université Catholique de Louvain: <http://uclouvain.be>

École Polytechnique de Louvain: <http://uclouvain.be/epl>

## Authors ##
*   Debroux Léonard <leonard.debroux@gmail.com>
*   Jadin Kevin <contact@kjadin.com>

## Abstract ##
Software-defined networking (SDN) provides additional knowledge compared to classical networks. 
This knowledge can be exploited in centralised algorithms as opposed to the commonly used distributed algorithms such as in PIM.
The problem of implementing multicast in SDN has already been studied in the literature. 
However, the optimality of multicast trees is often not the main focus of the researches.

In this thesis, we show that the SDN approach allows for easily building efficient trees, and we provide a method to further improve them.
The problem of computing optimal distribution trees in the context of multicast is known to be NP-complete, we therefore propose a configurable local search algorithm to compute competitive trees along with a Python implementation.

Furthermore, we assess that our algorithm is computationally efficient. It is consequently applicable in a real environment since it needs little time to yield good solutions. 

## Executables ##

### Python
*   src/addition_removal_time.py
*   src/build_network.py
*   src/comparison.py
*   src/datasets.py
*   src/impact.py
*   src/impact_example.py
*   src/ksp.py
*   src/setupparser.py

### Bash
*   evaluation/add_rem
*   evaluation/impact
*   evaluation/compare (need to give a folder containing .cfg files)
  *   0-sota
  *   1-ipit
  *   2-ttl
  *   3-schedule
  *   4-strategy
  *   5-intensify
  *   6-maxpath
  *   7-rssb
  *   8-unfair

### Matlab script
*   src/lognormal.m

## Files ##

### evaluation/
*   datasets/
    *   **/*.ds : datasets that were used for the experiments
*   results/
    *   **/*.cfg : configuration files for the experiments
    *   **/*.txt : raw data from the tests
    *   **/setup*.csv : generated from the .cfg files, summarizes the used setups
    *   comparison/**/*.csv : results of the comparison experiments
*   add_rem, compare, impact: scripts for testing

### src/
Source code and testing scripts


### topologies/
*   *.gml : gml representation of the topologies
*   *.sp : shortest paths (generated automatically upon an execution)
*   *.topo: configuration files linking a topology to its .gml and .sp


