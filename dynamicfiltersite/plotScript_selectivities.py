# Code adapted from tutorial at http://www.bogotobogo.com/python/python_matplotlib.php

import numpy as np
import matplotlib.pyplot as plt
import datetime as DT
import pylab
import sys

filename = sys.argv[1]

# load data from csv file, skip 2 rows, delimit by commas
data = np.loadtxt(filename, skiprows=2, delimiter=',', dtype={'names': ('task number', 'selectivity 1', 'selectivity 2', 'selectivity 3'),
          'formats': (np.int, np.float, np.float, np.float)})

m = [value0 for (value0, value1, value2, value3) in data]
s1 = [value1 for (value0, value1, value2, value3) in data]
s2 = [value2 for (value0, value1, value2, value3) in data]
s3 = [value3 for (value0, value1, value2, value3) in data]

fig = plt.figure()
ax = fig.add_subplot(111)
ax.grid()

plt.plot(m,s1, label="predicate branch 0")
plt.plot(m,s2, label="predicate branch 1")
plt.plot(m,s3, label="predicate branch 2")

# Now add the legend with some customizations.
legend = ax.legend(loc='upper center', shadow=True)

# The frame is matplotlib.patches.Rectangle instance surrounding the legend.
frame = legend.get_frame()
frame.set_facecolor('0.90')

# Set the fontsize
for label in legend.get_texts():
    label.set_fontsize('large')

for label in legend.get_lines():
    label.set_linewidth(1.5)  # the legend line width

plt.xlabel('Tasks Completed')
plt.ylabel('Selectivity')
plt.title('Computed Task Selectivity vs. Number of Tasks Completed')
now = DT.datetime.now()
plt.savefig('test_results/figure' + str(now.date())+ "_" + str(now.time())[:-7] + '.png')



