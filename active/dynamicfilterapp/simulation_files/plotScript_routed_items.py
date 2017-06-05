# run with python plotScript_routed_items.py unique_item_syn_routed_tasks.csv escrow_syn_routed_tasks.csv

import math
import numpy as np
import matplotlib.pyplot as plt
import datetime as DT
import pylab
import sys
from collections import defaultdict
from plotScript import multi_line_graph_gen

def main():
    unique = sys.argv[1]
    window = sys.argv[2]

    qx = np.loadtxt(unique, usecols=(0,), delimiter=',')
    qy = np.loadtxt(unique, usecols=(1,), delimiter=',')

    wx = np.loadtxt(window, usecols=(0,), delimiter=',')
    wy = np.loadtxt(window, usecols=(1,), delimiter=',')


    xl = [qx,wx]
    yl = [qy, wy]
    leg = ['queue eddy','sliding window']
    dest = 'graphs/routed_items_cost_switch.png'
    labels = ('Syn Question 0','Syn Question 1')
    title = 'Number of Routed First Items (Cost Switch at 200 Tasks)'
    multi_line_graph_gen(xl, yl, leg, dest, labels = labels, title = title)

if __name__ == "__main__":
    main()
