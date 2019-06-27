# run with python plotScript_routed_items.py RUN_NAME_multi_routing.csv
import math
import numpy as np
import matplotlib.pyplot as plt
import datetime as DT
import pylab
import sys
from collections import defaultdict
import plotScript

def main():
    fileToLoad = sys.argv[1]
    rawOut = plotScript.generic_csv_read(fileToLoad)
    questions = rawOut[0]
    arrayData = rawOut[1:]
    title = fileToLoad + 'Items Routed Average'
    dest = fileToLoad[:-3] + 'png'
    labels = ('Predicate','# of Items Routed')
    plotScript.multi_bar_graph_gen(arrayData, questions, dest, labels = labels, title = title)

if __name__ == "__main__":
    main()
