# Code adapted from tutorial at http://www.bogotobogo.com/python/python_matplotlib.php

import numpy as np
import matplotlib.pyplot as plt
import datetime as DT
import pylab
import sys

filename = sys.argv[1]

data= np.loadtxt(filename, delimiter=',', 
         dtype={'names': ('Tasks Completed', 'Selectivity'),'formats': ('i4', 'i4')} )

x = [key for (key, value) in data]
y = [value for (key, value) in data]

fig = plt.figure()
ax = fig.add_subplot(111)
ax.grid()

fig.autofmt_xdate()

plt.plot(x,y,'b--o--')
plt.xlabel('Tasks Completed')
plt.ylabel('Selectivity')
plt.title('Computed Task Selectivity vs. Number of Tasks Completed')
plt.savefig("testGraph.png")