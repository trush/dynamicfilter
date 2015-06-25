# Code adapted from tutorial at http://www.bogotobogo.com/python/python_matplotlib.php

import numpy as np
import matplotlib.pyplot as plt
import datetime as DT
import pylab
import sys

filename = sys.argv[1]

data= np.loadtxt(filename, delimiter=',', dtype={'names': ('task', 'selectivity'),
          'formats': (np.float, np.float)})

x = [key for (key, value) in data]
y = [value for (key, value) in data]

fig = plt.figure()
ax = fig.add_subplot(111)
ax.grid()

plt.plot(x,y)
plt.xlabel('Tasks Completed')
plt.ylabel('Selectivity')
plt.title('Computed Task Selectivity vs. Number of Tasks Completed')
plt.savefig("testGraph1.png")



