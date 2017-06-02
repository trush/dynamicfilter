This is the README for the plotScript files and other directories in this directory.

DIRECTORIES:
#OLD
graphs - contains a bunch of visualization images
hotels - contains stats and real data on hotels
restaurants - contains stats and real data on restaurants

PLOTSCRIPTS:
note - some of these files use seaborn. Be sure to install seaborn with:
sudo pip install seaborn

_accuracy_uncertainty
———————————
This plots the number of incorrect items vs. the uncertainty level
#TODO THIS ONE

_alg_hist
———————————
This plots a histogram of the number of tasks inside given input files of multiple simulations
Currently meant to take in 5 different testing outputs #TODO fix this?
Plots 5 different algorithms on the same graph for comparison
Takes in data run from RUN_TASKS_COUNT.
Should give a more nuanced comparison between algorithms using number of tasks before completion as a metric


_percent_done
———————————
This plots the percent of ip_pairs done over the number of tasks for given input files
Currently set to take two different files in, Compare between two different versions of the algorithm
Can't currently find the Data that should exist to be passed into this function


_queue_size_sim
———————————
This one doesn't appear to exist?
#TODO remove this section?
Plots the number of tasks vs. the queue size for synthetic data

_routed_items
———————————
Displays the number of items routed first to one of two predicates for given input files
Compares two different algorithms against one another
Can't find where the data comes from yet

_tasks_queuesize
———————————
Plots the number of tasks vs. the queue size of the queue eddy
Takes in one file with very specific parameters
First element of each line should be the queue size followed by a list of task counts
Will plot the average task counts vs the queue size
This data currently can't be auto generated, and must be pieced together from several runs of RUN_TASKS_COUNT
#TODO talk about the value of this graph, and if we want to be able to auto generate data of this type or not


_tasks_uncertainty
———————————
Plots the number of tasks vs. the uncertainty level
Hardcoded to accept only one file, but the file is the result of multiple testing runs
Looks to compare how well different algorithms hold up under increasing uncertainty
