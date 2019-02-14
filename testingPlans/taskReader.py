import math
import numpy as np
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import seaborn as sns
import datetime as DT
import pylab
import sys
from collections import defaultdict, Counter
import os.path
from os import makedirs
import csv
Suppress = False

## A simple function that modifies destination file names to avoid overwriting
# by appending numbers
# @param dest the preposed file name (.png or .csv only)
# @returns the resolved filename
def dest_resolver(dest):
    """
    given a filename (ending in .png) returns a version which wont overide data
    """
    if dest[-4:] != '.png' and dest[-4:] != '.csv':
        print dest
        raise ValueError('Invalid File Extention')
    if os.path.isfile(dest):
        num = 1
        name = dest [:-4] + str(num) + dest[-4:]
        while os.path.isfile(name):
            num += 1
            name = dest [:-4] + str(num) + dest[-4:]
        return name
    else:
        return dest

def split_bar_graph_gen(dataL, xL, dest, legend ,labels = ('',''), title = '',split='vertical', stderrL = None, fig_size = None, tight=False, yRange=(None,None)):
    sns.set(style="white", color_codes=True)
    sns.set_palette(sns.color_palette("tab10",n_colors=10), n_colors=10)
    knownSplits=('vertical','horizontal')
    if len(dataL)<= 1:
        raise ValueError("not enough data!")
    if split not in knownSplits:
        raise ValueError(str(split)+" Is not a known split")
    if fig_size is not None:
        fig = plt.figure(figsize=fig_size)
    else:
        fig = plt.figure()
    pos = np.arange(len(dataL[0]))
    try:
        if split=='vertical':
            width = 0.5/len(dataL[0])
            for i in range(len(dataL)):
                ind = pos + (i*width)
                if stderrL:
                    plt.bar(ind,dataL[i],width, yerr=stderrL[i], label = legend[i])
                else:
                    print "plotting " + str(dataL[i]) + " at index " + str(ind)
                    plt.bar(ind,dataL[i],width, label = legend[i])

        elif split=='horizontal':
            width = 0.9
            plt.bar(pos,dataL[0],width, label = legend[0])
            bottom = [0]*(len(dataL[0]))
            for i in range(1,len(dataL)): # len(dataL)
                ind = pos + (i*width)

                for j in range(len(bottom)):
                    bottom[j] += dataL[i-1][j]

                plt.bar(pos,dataL[i],width,bottom=bottom, label = legend[i])
    except Exception as e:
        if Suppress:
            print "When plotting " + dest + " encountered "+str(e)
            return
        else:
            raise e
    numMarkers = 10
    rxLabels = np.arange(0,len(dataL[0]),len(dataL[0])//numMarkers).tolist()
    xLabels = []
    labelIndex = 0
    while len(xLabels) < len(xL):
        if len(xLabels) < rxLabels[-1] and len(xLabels) == rxLabels[labelIndex]:
            xLabels.append(rxLabels[labelIndex]*20)
            labelIndex = labelIndex + 1
        else:
            xLabels.append("")
    plt.xticks(pos,xLabels)
    plt.legend()

    # Label the axes
    plt.xlabel(labels[0], fontsize=20)
    plt.ylabel(labels[1], fontsize=20)

    # range of axes
    plt.ylim(yRange)
    if yRange[1] is None: # if user has not defined ymax
        # puff up the y axis some
        y_max = plt.axis()[3]
        plt.ylim(ymax=y_max*1.1)

    # Title the graph
    plt.title(title, fontsize=20)
    if tight:
        fig.tight_layout()
    plt.savefig(dest_resolver(dest))
    plt.close(fig)


with open('dynoTestRes12.csv') as ticketCSV:
    csv_reader = csv.reader(ticketCSV, delimiter=',')
    startTime = 0
    lines=0
    aggregator = {}
    times = []
    tasksTime = [[],[],[],[],[]]
    legend = ["pred0","pred1","pred2","pred3","pred4"]
    for row in csv_reader:
        if lines == 0:
            lines = 1
            continue
        if startTime == 0:
            startTime = int(row[0])
        if row[3] != '200':
            continue
        else:
            if row[2][0:6] == "submit":
                code = row[2][-3:]
                if code[len(code) - 1] == 'a':
                    code = "pred" + str(int(code[1]) - 1)
                else:
                    code = "pred" + str(int(code[2]) - 1)
                if code not in aggregator:
                    aggregator[code] = 0
                aggregator[code] += 1
            if int(row[0]) - startTime > 10000:
                for i in range(len(legend)):
                    if legend[i] in aggregator:
                        tasksTime[i] += [aggregator[legend[i]]]
                    else:
                        tasksTime[i] += [0]
                times += [startTime]
                startTime = int(row[0])
                aggregator = {}
                
    print tasksTime
    print times
    split_bar_graph_gen(tasksTime, times, 'taskGraph.png', legend, ('time', 'task count'), title='tasks over time', split = "horizontal", fig_size = (15, 5), tight=True)