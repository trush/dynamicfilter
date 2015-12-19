# Code adapted from tutorial at http://www.bogotobogo.com/python/python_matplotlib.php

# run with python2.7 plotScript_aggregate.py test_results/csv_aggregate_file_name.csv

# only works with aggregate csv file with one eddy and random 
# plots estimated selectivities over task number for all three predicates

import numpy as np
import matplotlib.pyplot as plt
import datetime as DT
import pylab
import sys

# the csv file name is the first (and only) argument passed from the command line
filename = sys.argv[1]

# read in data from csv file, skips first row, delimits by comma
data = np.loadtxt(filename, skiprows=1, delimiter=',', dtype={'names': ('eddy num tasks', 
	'eddy correct percentage', 'random num tasks', 'random correct percentage'),
    'formats': (np.int, np.float, np.int, np.float)})

# get the columns of the csv file as separate lists
eddyTasks = [value0 for (value0, value1, value2, value3) in data]
eddyPercent = [value1 for (value0, value1, value2, value3) in data]
randomTasks = [value2 for (value0, value1, value2, value3) in data]
randomPercent = [value3 for (value0, value1, value2, value3) in data]

# set up graph
fig = plt.figure()
ax = fig.add_subplot(111)
ax.grid()

# plot the data
plt.plot(range(len(eddyTasks)),eddyTasks, label="predicate branch 0")
plt.plot(m,s2, label="predicate branch 1")
plt.plot(m,s3, label="predicate branch 2")

# Now add the legend with some customizations.
legend = ax.legend(loc='upper center', shadow=True)

# The frame is matplotlib.patches.Rectangle instance surrounding the legend.
frame = legend.get_frame()
frame.set_facecolor('0.90')

# Set the font size
for label in legend.get_texts():
    label.set_fontsize('large')

# Set the legend line width
for label in legend.get_lines():
    label.set_linewidth(1.5)  

# Label the axes
plt.xlabel('Tasks Completed')
plt.ylabel('Selectivity')

# Title the graph
plt.title('Random: Computed Task Selectivity vs. Number of Tasks Completed')

# Save the figure with a file name that includes a time stamp
now = DT.datetime.now()
plt.savefig('test_results/figure' + str(now.date())+ "_" + str(now.time())[:-7] + '.png')



