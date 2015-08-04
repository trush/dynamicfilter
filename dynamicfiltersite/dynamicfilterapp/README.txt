About the Simulations
=====================
Specify simulation parameters in SimulationTest.test_controller in tests.py. Refer to that documentation for further instructions and an explanation of what we are simulating. 

Use the Django test framework to call test_controller as follows:
python manage.py test dynamicfilterapp.tests.SimulationTest.test_sample_data_simulation_controller

Simulation Notes
================
These are notes on the simulations we have run, including many of now-deprecated versions of our algorithm. We summarize insights gained, but for older versions do not necessarily provide all the information to reproduce the simulation (partly because these use now-overwritten code). Each set of simulations has a directory with generated csv results files. The "aggregate" files have information about all the simulations done with one set of parameters, while files with algorithm names ("eddy", "eddy2", or "random") each contain information about one simulation with one algorithm. A few of the simulations have "percentdone" files, which simply record the percent of predicates complete after each worker task is entered (these are aggregate, rather than individual, files). There are also readme files, which may note the predicates used or the significance of numbers recorded in the csv files.

Set 1
=====
