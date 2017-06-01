# Code adapted from tutorial at http://www.bogotobogo.com/python/python_matplotlib.php

# run with python plotScript_tasks_uncertainty.py num_task_vs_uncertainty.csv

import numpy as np
import matplotlib.pyplot as plt
import datetime as DT
import pylab
import sys
import math

# the csv file name is the first (and only) argument passed from the command line
filename = sys.argv[1]

# read in data from csv file, skips first row, delimits by comma
data = np.loadtxt(filename, skiprows=2, delimiter=',')

# get data for each algorithm
randAlg = data[:6]
ticketAlg = data[6:12]
queueAlg = data[12:18]

randAlg_mean = [np.mean(run) for run in randAlg]
ticketAlg_mean = [np.mean(run) for run in ticketAlg]
queueAlg_mean = [np.mean(run) for run in queueAlg]

randAlg_stderr = [np.std(run)/math.sqrt(len(run)) for run in randAlg]
ticketAlg_stderr = [np.std(run)/math.sqrt(len(run)) for run in ticketAlg]
queueAlg_stderr = [np.std(run)/math.sqrt(len(run)) for run in queueAlg]

uncertainty = [0.15,0.2,0.25,0.3,0.35,0.4]

# set up graphs

# for Number of Tasks
fig = plt.figure()
ax = fig.add_subplot(111)
ax.axis([0.10,0.45,180,340])
ax.grid()
plt.errorbar(uncertainty,randAlg_mean,yerr=randAlg_stderr,markersize=3,label="Random")
plt.errorbar(uncertainty,ticketAlg_mean,yerr=ticketAlg_stderr,markersize=3,label="Ticket")
plt.errorbar(uncertainty,queueAlg_mean,yerr=queueAlg_stderr,markersize=3,label="Queue")

# Now add the legend with some customizations.
legend = ax.legend(loc=0)

# The frame is matplotlib.patches.Rectangle instance surrounding the legend.
frame = legend.get_frame()
frame.set_facecolor('0.90')

# Set the font size
for label in legend.get_texts():
    label.set_fontsize('small')

# Set the legend line width
for label in legend.get_lines():
    label.set_linewidth(1.5)  

# Label the axes
plt.ylabel('Tasks Completed')
plt.xlabel('Uncertainty')

# Title the graph
plt.title('Tasks Completed vs Uncertainty')

# Save the figure with a file name that includes a time stamp
now = DT.datetime.now()
plt.savefig('tasks_uncertainty' + str(now.date())+ "_" + str(now.time())[:-7] + '.png')



