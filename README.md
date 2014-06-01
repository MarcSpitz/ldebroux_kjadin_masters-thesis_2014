Masters-thesis
==============

Title
-----
Local search for Multicast in Software-Defined Networks

Authors
-------
Debroux Léonard, Jadin Kevin


Executables
===========

Python
------
*   src/addition_removal_time.py
*   src/build_network.py
*   src/comparison.py
*   src/datasets.py
*   src/impact.py
*   src/impact_example.py
*   src/ksp.py
*   src/setupparser.py

Bash
----
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

Matlab script
-------------
*   src/lognormal.m


Files
=====

evaluation/
-----------
*   datasets/
    *   **/**/*.ds : datasets that were used for the experiments
*   results/
    *   **/*.cfg : configuration files for the experiments
    *   **/*.txt : raw data from the tests
    *   **/setup*.csv : generated from the .cfg files, summarizes the used setups
    *   comparison/**/*.csv : results of the comparison experiments
*   add_rem, compare, impact: scripts for testing

src/
----
Source code and testing scripts


topologies/
-----------
*   *.gml : gml representation of the topologies
*   *.sp : shortest paths between all nodes in the graph
*   *.topo: configuration files linking a topology to its .gml and .sp


