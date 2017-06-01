# run with python plotScript_routed_items.py unique_item_syn_routed_tasks.csv escrow_syn_routed_tasks.csv

import math
import numpy as np
import matplotlib.pyplot as plt
import datetime as DT
import pylab
import sys
from collections import defaultdict

unique = sys.argv[1]
window = sys.argv[2]

qx = np.loadtxt(unique, usecols=(0,), delimiter=',')
qy = np.loadtxt(unique, usecols=(1,), delimiter=',')

wx = np.loadtxt(window, usecols=(0,), delimiter=',')
wy = np.loadtxt(window, usecols=(1,), delimiter=',')

fig = plt.figure()
ax = fig.add_subplot(111)
ax.axis([-1,100,-1,100])
ax.grid()

ax.plot(qx, qy, c='b', label="queue eddy")
ax.plot(wx, wy, c='r', label="sliding window")

legend = ax.legend(loc=0)

plt.ylabel('Syn Question 1')
plt.xlabel('Syn Question 0')
plt.title('Number of Routed First Items (Cost Switch at 200 Tasks)')
#plt.show()
plt.savefig('graphs/routed_items_cost_switch.png')