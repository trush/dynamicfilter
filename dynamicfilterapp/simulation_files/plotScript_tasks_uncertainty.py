# Code adapted from tutorial at http://www.bogotobogo.com/python/python_matplotlib.php

# run with python plotScript_tasks_uncertainty.py num_task_vs_uncertainty.csv

import numpy as np
import matplotlib.pyplot as plt
import datetime as DT
import pylab
import sys
import math
from plotScript import multi_line_graph_gen

def main():
    # the csv file name is the first (and only) argument passed from the command line
    filename = sys.argv[1]

    # read in data from csv file, skips first row, delimits by comma
    data = np.loadtxt(filename, skiprows=2, delimiter=',')

    # get data for each algorithm
    randAlg = data[:6]
    ticketAlg = data[6:12]
    queueAlg = data[12:18]

    randAlg_mean = [np.mean(run) for run in randAlg]
    ticketAlg_mean = [np.mean(run) for run in ticketAlg]
    queueAlg_mean = [np.mean(run) for run in queueAlg]

    randAlg_stderr = [np.std(run)/math.sqrt(len(run)) for run in randAlg]
    ticketAlg_stderr = [np.std(run)/math.sqrt(len(run)) for run in ticketAlg]
    queueAlg_stderr = [np.std(run)/math.sqrt(len(run)) for run in queueAlg]

    uncertainty = [0.15,0.2,0.25,0.3,0.35,0.4]

    # set up graphs
    xlist = [uncertainty, uncertainty, uncertainty]
    ylist = [randAlg_mean, ticketAlg_mean, queueAlg_mean]
    slist = [randAlg_stderr, ticketAlg_stderr, queueAlg_stderr]
    legends = ["R","T","Q"]

    now = DT.datetime.now()

    dest = 'tasks_uncertainty' + str(now.date())+ "_" + str(now.time())[:-7] + '.png'
    labels = ('Tasks Completed','Uncertainty')
    title = 'Tasks Completed vs Uncertainty'

    multi_line_graph_gen(xlist, ylist, legends, dest, labels = labels, title = title, stderrL = slist)

if __name__ == "__main__":
    main()
