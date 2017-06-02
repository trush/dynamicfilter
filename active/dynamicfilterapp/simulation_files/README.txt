This is the README for the plotScript files and other directories in this directory.

DIRECTORIES:
#NEW
output - the current default path location for new CVSs and PNGs
#OLD
graphs - contains a bunch of visualization images
hotels - contains stats and real data on hotels
restaurants - contains stats and real data on restaurants

PLOTSCRIPTS:
note - some of these files use seaborn. Be sure to install seaborn with:
sudo pip install seaborn

note - many of these files break if the input csv ends with a dangling comma,
please strip your last commas if you're getting a str->float conversion error

TAGS:
  #LEGACY         - oldschool, unchanged
  #MULTIPLE       - currently takes in multiple files
  #NEW            - newschool, uses for format
  #AUTORUN        - is capable of being used for autogenerating graphs (doesn't mean that it currently does)
  #SPECIAL_TOPIC  - of questionable value (at least for automation)


#LEGACY
#MULTIPLE
_accuracy_uncertainty
———————————
This plots the number of incorrect items vs. the uncertainty level
currently takes in a rather complicated hand crafted file.
Requires multiple runs of many algorithms with different sets of predicates
Only really makes sense for synthetic data
#TODO talk about how this should be automated
#TODO create a custom method just for this test


#NEW
#AUTORUN
_alg_tasks_hist
———————————
Takes in the data from many runs of the same simulation.
Plots the distribution of the number of tasks it took to complete a run.
Takes in data run from RUN_TASKS_COUNT. Now can Auto-Run from the test_simulations file.


#LEGACY
#MULTIPLE
_alg_tasks_hist_multiple
———————————
This plots a histogram of the number of tasks inside given input files of multiple simulations
Currently meant to take in 5 different testing outputs #TODO fix this?
Plots 5 different algorithms on the same graph for comparison
Takes in data run from RUN_TASKS_COUNT.
Should give a more nuanced comparison between algorithms using number of tasks before completion as a metric


#LEGACY
#MULTIPLE
_percent_done
———————————
This plots the percent of ip_pairs done over the number of tasks for given input files
Currently set to take two different files in, Compare between two different versions of the algorithm
Can't currently find the Data that should exist to be passed into this function #TODO find the data


#LEGACY
#MULTIPLE
_routed_items
———————————
Displays the number of items routed first to one of two predicates for given input files
Compares two different algorithms against one another
Asks for two distinct files one for each algorithm
Can't find where the data comes from yet


#LEGACY
#SPECIAL_TOPIC
_tasks_queuesize
———————————
Plots the number of tasks vs. the queue size of the queue eddy
Takes in one file with very specific parameters
First element of each line should be the queue size followed by a list of task counts
Will plot the average task counts vs the queue size
This data currently can't be auto generated, and must be pieced together from several runs of RUN_TASKS_COUNT
#TODO talk about the value of this graph, and if we want to be able to auto generate data of this type or not


#LEGACY
_tasks_uncertainty
———————————
Plots the number of tasks vs. the uncertainty level
Hardcoded to accept only one file, but the file is the result of multiple testing runs
Looks to compare how well different algorithms hold up under increasing uncertainty
#TODO make single use? split into multiple and single?

#NEW
#AUTORUN
_single_cost_hist
———————————
looks at a single ItemPredicate Pair over multiple runs.
plots a Histogram of the costs.
Takes in Data from RUN_SINGLE_PAIR. Can AutoRun.
Currently I have no idea which IP pair it picks, or why it picks that one.
