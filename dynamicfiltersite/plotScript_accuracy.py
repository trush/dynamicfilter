# Code adapted from tutorial at http://www.bogotobogo.com/python/python_matplotlib.php

# run with python2.7 plotScript_accuracy.py test_results/csv_aggregate_file.csv

# plots accuracy percentage vs. number of runs

# BIG TODO: need to change the way we are loading in the data
#			Because now our tests.py file only runs the chosen eddy versions, the
#			number of columns changes depending on how many eddy versions we run.
#			But right now, we are always reading from 6 columns.

import numpy as np
import matplotlib.pyplot as plt
import datetime as DT
import pylab
import sys

filename = sys.argv[1]
now = DT.datetime.now()

# load data from csv file, skip 2 rows, delimit by commas
data = np.loadtxt(filename, skiprows=2, delimiter=',', dtype={'names': ('eddy num tasks',
	'eddy correct percent', 'eddy 2 num tasks', 'eddy 2 correct percentage', 
	'random num tasks', 'random correct percent'), 'formats': (np.int, np.float, 
	np.int, np.float, np.int, np.float)})

# list of number of tasks for eddy in each simulation
s0 = [value0 for (value0, value1, value2, value3, value4, value5) in data]

# list of percentage accuracies for eddy in each simulation
s1 = [value1 for (value0, value1, value2, value3, value4, value5) in data]

# list of number of tasks for eddy2 in each simulation
s2 = [value2 for (value0, value1, value2, value3, value4, value5) in data]

# list of percentage accuracies for eddy2 in each simulation
s3 = [value3 for (value0, value1, value2, value3, value4, value5) in data]

# list of number of tasks for random in each simulation
s4 = [value4 for (value0, value1, value2, value3, value4, value5) in data]

# list of percentage accuracies for random in each simulation
s5 = [value5 for (value0, value1, value2, value3, value4, value5) in data]

print "Eddy average accuracy: " + str(np.average(s1))
print "Eddy2 average accuracy: " + str(np.average(s3))
print "Random average accuracy: " + str(np.average(s5))

fig = plt.figure()

# plots histogram of eddy accuracy

plt.hist(s1)

plt.xlabel('Accuracy Percentage')
plt.ylabel('Number of Runs')
plt.title('Tasks to Complete all Questions (Eddy1)')
plt.savefig('test_results/eddy1_histogram' + str(now.date())+ "_" + str(now.time())[:-7] + '.png')

#-----------------------
fig = plt.figure()

# plots histogram of eddy2 accuracy

plt.hist(s3)

plt.xlabel('Accuracy Percentage')
plt.ylabel('Number of Runs')
plt.title('Tasks to Complete all Questions (Eddy2)')
plt.savefig('test_results/eddy2_histogram' + str(now.date())+ "_" + str(now.time())[:-7] + '.png')

#-----------------------
fig = plt.figure()

# plots histogram of random accuracy

plt.hist(s5)

plt.xlabel('Accuracy Percentage')
plt.ylabel('Number of Runs')
plt.title('Tasks to Complete all Questions (Random)')
plt.savefig('test_results/random_histogram' + str(now.date())+ "_" + str(now.time())[:-7] + '.png')

