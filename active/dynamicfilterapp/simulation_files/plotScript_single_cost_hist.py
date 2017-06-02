# Code adapted from tutorial at http://www.bogotobogo.com/python/python_matplotlib.php

# run with python plotScript_single_cost_hist.py single_pair_cost.csv

import numpy as np
import matplotlib.pyplot as plt
import datetime as DT
import pylab
import sys

def single_cost_gen(filename, dest):
    costs = list(np.loadtxt(filename, delimiter=','))
    #print costs

    fig = plt.figure()
    ax = fig.add_subplot(111)

    # the histogram of the data
    n, bins, patches = ax.hist(costs, 1000, normed=1, facecolor='green')

    bincenters = 0.5*(bins[1:]+bins[:-1])

    ax.set_xlabel('Cost')
    ax.set_ylabel('Frequency')
    ax.set_title('Histogram of Single IP Pair costs')
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 0.3)
    ax.grid(True)

    #plt.show()
    now = DT.datetime.now()
    plt.savefig(dest + '_single_cost.png')
