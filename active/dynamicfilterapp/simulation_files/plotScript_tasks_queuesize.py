# Code adapted from tutorial at http://www.bogotobogo.com/python/python_matplotlib.php

# run with python plotScript_tasks_queuesize.py queuesize_vs_numtasks.csv
# plots the number of tasks vs the queuesize of the queue algorithm

import math
import numpy as np
import matplotlib.pyplot as plt
#import datetime as DT
import pylab
import sys

# the csv file name is the first (and only) argument passed from the command line
filename = sys.argv[1]

# read in data from csv file, skips first row, delimits by comma
data = np.loadtxt(filename, skiprows=2, delimiter=',')

queue_size = []
num_tasks = []

for line in data:
	queue_size.append(line[0])
	num_tasks.append(list(line[1:]))

mean = []
stderr = []
for run in num_tasks:
	mean.append(np.mean(run))
	stderr.append(np.std(run)/math.sqrt(len(run)))

# Make the graph
fig = plt.figure()
ax = fig.add_subplot(111)
#ax.axis([0,21,125,170])
ax.grid()
ax.errorbar(queue_size,mean,yerr=stderr,marker='o',markersize=5)

# Label the axes
plt.ylabel('Tasks Completed')
plt.xlabel('Queue Size')

# Title the graph
plt.title('Tasks Completed vs. Queue Size (Questions:[0,7])')

#plot curve of best fit
#plt.plot(queue_size, np.poly1d(np.polyfit(queue_size, num_tasks, 1))(queue_size))
plt.show()
#plt.savefig('tasks_queuesize[0,7].png')
