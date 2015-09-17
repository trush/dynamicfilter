About the Simulations
=====================
Specify simulation parameters in SimulationTest.test_controller in tests.py. Refer to that documentation for further instructions and an explanation of what we are simulating. 

Use the Django test framework to call test_controller as follows:
python manage.py test dynamicfilterapp.tests.SimulationTest.test_controller


Simulation Notes
================
These are notes on the simulations we have run, including many of now-deprecated versions of our algorithm. We summarize insights gained, but for older versions do not necessarily provide all the information to reproduce the simulation (partly because these use now-overwritten code). Each set of simulations has a directory with generated csv results files. The "aggregate" files have information about all the simulations done with one set of parameters, while files with algorithm names ("eddy", "eddy2", or "random") each contain information about one simulation with one algorithm. A few of the simulations have "percentdone" files, which simply record the percent of predicates complete after each worker task is entered (these are aggregate, rather than individual, files). There are also readme files, which may note the predicates used or the significance of numbers recorded in the csv files.


Simulation With Parameters
==========================
This folder contains several runs of our simulation by differing certain parameters. The parameters we used were number of simulations, number of restaurants, confidence levels, worker error, selectivity levels, and predicate difficulties. 

New Eddy (NE) Checks
==================================
The folder contains several runs of simulations with a specific set of parameters. These simulations are used to verify that what we think should happen according to eddy2’s logic is what does happen after running the test. The parameters for the files in the subfolders are formatted exactly as stated above.

New Eddy Checks 1-2 and an explanation of each of them can be found on in the Google Drive folder under Test Results.

Sanity Checks (SC)
==================
This folder contains several runs of simulations with specific sets of parameters. These simulations were used to verify that what we think should happen according to eddy1’s logic is what does happen after running the test. The parameters for the files in the subfolders are formatted exactly as stated above.

Sanity Checks 1-21 and an explanation of each of them can be found on in the file “Unit Testing & Trace-Through Observations” in the Google Drive folder under “Test Results/Data”.

Testing the Original Lottery
============================
This folder contains several runs of simulations to test the original lottery with specific sets of selectivities. In this version of the lottery, each predicate branch was awarded a certain number of tickets based on its selectivity, and then a regular lottery was conducted to pick the branch. Each subfolder name consists of three decimal numbers. Each indicate the selectivity of each predicate branch. Each subfolder then contains the aggregate file and histograms illustrating the results.

Testing Weighted Lottery with Memory
====================================
This folder contains several runs of simulations to test a different version of the lottery. In this version, we double the number of tickets for the most selective branch, and we also remember the previously used branch so that the new branch must exceed the past branch’s selectivity by a certain amount in order to be used. Once again, each subfolder contains three decimals, each describing the selectivity of each predicate branch. Each subfolder contains the aggregate file and histograms to illustrate the results.

Testing Weighted Lottery without Memory
=======================================
This folder contains several runs of simulations to test a different version of the lottery. In this version, we double the number of tickets for the most selective branch, and then conduct the lottery. Similarly, each subfolder consists of three decimal numbers, each indicating the selectivities of the predicate branches. Each subfolder then contains the aggregate file and histograms to illustrate the results.

Varying Parameters
==================
This folder contains several subfolders, each titled with what parameters is being changed and tested. Please refer to the file “Simulation Test Results” in the Google Drive folder “Test Results/Data” to see additional details on the parameters.


MTurk Data
==========
This folder contains multiple runs of our simulation with data from Mechanical Turk workers. We submitted a batch of HITs to MTurk (20 restaurants, 10 predicates, 30 votes each = 6000 HITs done). Each sub-folder is named with several numbers, which correspond to an index in the array of predicates that we used. We simulated workers’ votes by sampling from the MTurk data with replacement. 

0,1,2
=====
0: Does this restaurant have a parking lot? (Selectivity: 62.67%)
1: Does this restaurant have a drive-through? (Selectivity: 89.83%)
2: Does this restaurant have drinks for those under 21? (Selectivity: 15.83%)

0,1,4,5
=======
0: Does this restaurant have a parking lot? (Selectivity: 62.67%)
1: Does this restaurant have a drive-through? (Selectivity: 89.83%)
4: Does this restaurant serve Chinese food? (Selectivity: 85.17%)
5: Is this restaurant open until midnight? (Selectivity: 88.5%)

1,4,5
=====
1: Does this restaurant have a drive-through? (Selectivity: 89.83%)
4: Does this restaurant serve Chinese food? (Selectivity: 85.17%)
5: Is this restaurant open until midnight? (Selectivity: 88.5%)

1,5,9
=====
1: Does this restaurant have a drive-through? (Selectivity: 89.83%)
5: Is this restaurant open until midnight? (Selectivity: 88.5%)
9: Does this restaurant have a romantic atmosphere? (Selectivity: 55.33%)

2,3,7
=====
This folder contains simulations with all the ambiguous questions of our predicate set.

2: Does this restaurant have drinks for those under 21? (Selectivity: 15.83%)
3: Does this restaurant have more than 20 items on its menu? (Selectivity: 15.67%)
7: Does this restaurant serve breakfast? (Selectivity: 68.17%)

2,3,8
=====
2: Does this restaurant have drinks for those under 21? (Selectivity: 15.83%)
3: Does this restaurant have more than 20 items on its menu? (Selectivity: 15.67%)
8: Does this restaurant have its own website? (Selectivity: 6.33%)

2,6,8
=====
2: Does this restaurant have drinks for those under 21? (Selectivity: 15.83%)
6: Would a typical meal at this restaurant cost more than $30? (Selectivity: 69.83%)
8: Does this restaurant have its own website? (Selectivity: 6.33%)

3,6,9
=====
This folder contains simulations with subjective questions (6,9). But we needed to run it with Question #3 in order to have three questions just like all the other simulations. This allows us to compare the effect of subjectivity on the number of HITs with other simulations.

3: Does this restaurant have more than 20 items on its menu? (Selectivity: 15.67%)
6: Would a typical meal at this restaurant cost more than $30? (Selectivity: 69.83%)
9: Does this restaurant have a romantic atmosphere? (Selectivity: 55.33%)

4,5,8
=====
This folder contains simulations with straightforward questions (all have extreme selectivities).

4: Does this restaurant serve Chinese food? (Selectivity: 85.17%)
5: Is this restaurant open until midnight? (Selectivity: 88.5%)
8: Does this restaurant have its own website? (Selectivity: 6.33%)
