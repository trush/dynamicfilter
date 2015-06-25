# Code adapted from tutorial at http://www.bogotobogo.com/python/python_matplotlib.php

import numpy as np
import matplotlib.pyplot as plt
import datetime as DT
import pylab
import sys
print "what"
filename = sys.argv[1]

data= np.loadtxt(filename, delimiter=',', dtype={'names': ('task', 'selectivity'),
          'formats': (np.float, np.float)})

print "!!!"
for item in data:
	print item

x = [key for (key, value) in data]
y = [value for (key, value) in data]

fig = plt.figure()
ax = fig.add_subplot(111)
ax.grid()

plt.plot(x,y)
plt.xlabel('Tasks Completed')
print "yo faceeeeeee"
plt.ylabel('Selectivity')
plt.title('Computed Task Selectivity vs. Number of Tasks Completed')
plt.savefig("testGraph.png")