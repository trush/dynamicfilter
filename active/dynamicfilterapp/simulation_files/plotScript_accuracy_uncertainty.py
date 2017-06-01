# Code adapted from tutorial at http://www.bogotobogo.com/python/python_matplotlib.php

# run with python plotScript_accuracy_uncertainty.py accuracy_vs_uncertainty.csv
# plots the accuracy vs. uncertainty of each algorithm

import math
import numpy as np
import matplotlib.pyplot as plt
import datetime as DT
import pylab
import sys

# the csv file name is the first (and only) argument passed from the command line
filename = sys.argv[1]

# read in data from csv file, skips first row, delimits by comma
data = np.loadtxt(filename, skiprows=2, delimiter=',')

randAlg = data[:7]
ticketAlg = data[7:14]
queueAlg = data[14:21]

randAlg_mean = [np.mean(run) for run in randAlg]
ticketAlg_mean = [np.mean(run) for run in ticketAlg]
queueAlg_mean = [np.mean(run) for run in queueAlg]

randAlg_stderr = [np.std(run)/math.sqrt(len(run)) for run in randAlg]
ticketAlg_stderr = [np.std(run)/math.sqrt(len(run)) for run in ticketAlg]
queueAlg_stderr = [np.std(run)/math.sqrt(len(run)) for run in queueAlg]

uncertainty = [0.1,0.15,0.2,0.25,0.3,0.35,0.4]

# Make the graph
fig = plt.figure()
ax = fig.add_subplot(111)
ax.axis([0.05,0.45,2,6])
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
plt.ylabel('Number of Missing or Incorrect Items')
plt.xlabel('Uncertainty')

# Title the graph
plt.title('Accuracy vs. Uncertainty')

# plt.show()
# Save the figure with a file name that includes a time stamp
now = DT.datetime.now()
plt.savefig('accuracy_uncertainty' + str(now.date())+ "_" + str(now.time())[:-7] + '.png')