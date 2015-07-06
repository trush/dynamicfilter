# Code adapted from tutorial at http://www.bogotobogo.com/python/python_matplotlib.php

import numpy as np
import matplotlib.pyplot as plt
import datetime as DT
import pylab
import sys

filename = sys.argv[1]
now = DT.datetime.now()
data = np.loadtxt(filename, skiprows=1, delimiter=',', dtype={'names': ('eddy num tasks', 'eddy correct percent', 'random num tasks', 'random correct percent'),
          'formats': (np.int, np.float, np.int, np.float)})

s0 = [value0 for (value0, value1, value2, value3) in data]
s2 = [value0 for (value2, value1, value2, value3) in data]

fig = plt.figure()
ax = fig.add_subplot(111)
ax.grid()

plt.hist(s0)

plt.xlabel('Tasks Completed')
plt.ylabel('Number of Runs')
plt.title('Tasks to Complete all Questions (Eddy)')
plt.savefig('test_results/eddy_histogram' + str(now.date())+ "_" + str(now.time())[:-7] + '.png')

plt.clf()
plt.cla()

fig = plt.figure()
ax = fig.add_subplot(111)
ax.grid()

plt.hist(s2)

plt.xlabel('Tasks Completed')
plt.ylabel('Number of Runs')
plt.title('Tasks to Complete all Questions (Random)')
plt.savefig('test_results/random_histogram' + str(now.date())+ "_" + str(now.time())[:-7] + '.png')
