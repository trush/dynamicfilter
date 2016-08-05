# run with python plotScript_percent_done.py unique_percent_done.csv queue_percent_done.csv

import math
import numpy as np
import matplotlib.pyplot as plt
import datetime as DT
import pylab
import sys
from collections import defaultdict

# the csv file names
unique = sys.argv[1]
queue = sys.argv[2]

# read in data from csv file, skips first row, delimits by comma
unique_tasks_completed = np.loadtxt(unique, usecols=(0,), delimiter=',')
unique_percent_done = np.loadtxt(unique, usecols=(1,), delimiter=',')

queue_tasks_completed = np.loadtxt(queue, usecols=(0,), delimiter=',')
queue_percent_done = np.loadtxt(queue, usecols=(1,), delimiter=',')

fig = plt.figure()
ax = fig.add_subplot(111)

unique_d = defaultdict(list)
for i in range(len(unique_tasks_completed)):
	unique_d[unique_tasks_completed[i]] = unique_d[unique_tasks_completed[i]] + [unique_percent_done[i]]

queue_d = defaultdict(list)
for i in range(len(queue_tasks_completed)):
	queue_d[queue_tasks_completed[i]] = queue_d[queue_tasks_completed[i]] + [queue_percent_done[i]]

ux = np.unique(unique_tasks_completed)
qx = np.unique(queue_tasks_completed)

# take averages of runs
unique_av = [np.mean(unique_d[element]) for element in ux]
queue_av = [np.mean(queue_d[element]) for element in qx]

ax.plot(ux, unique_av, c='b', label='unique')
ax.plot(qx, queue_av, c='r', label='queue')

legend = ax.legend(loc='upper left')
ax.set_ylim(0, 1)
plt.ylabel('Percent Done')
plt.xlabel('Tasks Completed')
plt.title('Percent Done vs. Tasks Completed Questions:[0,2,9]')
#plt.show()
plt.savefig('graphs/queues_percent_done_0_2_9.png')