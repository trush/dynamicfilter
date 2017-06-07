# run with python plotScript_routed_items.py unique_item_syn_routed_tasks.csv escrow_syn_routed_tasks.csv

import math
import numpy as np
import matplotlib.pyplot as plt
import datetime as DT
import pylab
import sys
from collections import defaultdict
from plotScript import multi_line_graph_gen, generic_csv_read

def main():
    xL, yL = [],[]
    for i in range(1,len(sys.argv)):
        loadedData = generic_csv_read(sys.argv[i])

        xL.append(loadedData[1])
        yL.append(loadedData[2])
    qs = loadedData[0]


    dest = 'test.png'
    labels = (qs[0],qs[1])
    title = 'Comparative item routing'
    multi_line_graph_gen(xL, yL, sys.argv[1:], dest, labels = labels, title = title, square = True)

if __name__ == "__main__":
    main()
