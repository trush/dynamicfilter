# Code adapted from tutorial at http://www.bogotobogo.com/python/python_matplotlib.php

# run with python2.7 plotScript_tasks.py test_results/csv_file_name.csv

# only works on an aggregate file with eddy, eddy2, and random

# TODO: needs to adapt because our aggregate file will not always have those three
# eddy versions. Could have more or less.

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

# prints average and accuracies of each algorithm
print "Eddy average: " + str(np.average(s0))
print "Eddy2 average: " + str(np.average(s2))
print "Random average: " + str(np.average(s4))

fig = plt.figure()

# plots histogram of number of tasks of each eddy simulation

plt.hist(s0)

plt.xlabel('Tasks Completed')
plt.ylabel('Number of Runs')
plt.title('Tasks to Complete all Questions (Eddy)')
plt.savefig('test_results/eddy_histogram' + str(now.date())+ "_" + str(now.time())[:-7] + '.png')

plt.clf()
plt.cla()
#-----------------------
fig = plt.figure()

# plots histogram of number of tasks of each eddy2 simulation

plt.hist(s2)

plt.xlabel('Tasks Completed')
plt.ylabel('Number of Runs')
plt.title('Tasks to Complete all Questions (Eddy 2)')
plt.savefig('test_results/eddy2_histogram' + str(now.date())+ "_" + str(now.time())[:-7] + '.png')

plt.clf()
plt.cla()
#-----------------------
fig = plt.figure()

# plots histogram of number of tasks of each random simulation

plt.hist(s4)

plt.xlabel('Tasks Completed')
plt.ylabel('Number of Runs')
plt.title('Tasks to Complete all Questions (Random)')
plt.savefig('test_results/random_histogram' + str(now.date())+ "_" + str(now.time())[:-7] + '.png')

