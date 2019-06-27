# Code adapted from tutorial at http://www.bogotobogo.com/python/python_matplotlib.php

# run with python plotScript_single_cost_hist.py single_pair_cost.csv

import numpy as np
import matplotlib.pyplot as plt
import datetime as DT
import pylab
import sys
from plotScript import hist_gen

def main():
    filename = sys.argv[1]
    data = list(np.loadtxt(filename, delimiter=','))
    dest = filename[:-4]
    hist_gen(data, dest + '_single_cost.png', labels=('Cost', 'Frequency'), title='Histogram of Single IP Pair costs', smoothness = True)

if __name__ == "__main__":
    main()
