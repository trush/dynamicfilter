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

def multi_hist_gen(dataList, legendList, dest, labels=('',''), title='', xRange=(None,None), yRange=(None,None), smoothness=True):
    """
    Very similar to hist_gen, however takes a list of datasets and a list of
    names of your datasets and a destination name, plots all datasets on one
    plot in differing colors. takes in optional labels and title like before.
    """
    #TODO Print out relevant data to a description?
    if len(legendList) < len(dataList):
        raise ValueError('Not enough legends ')
    sns.set(style="white", color_codes=True)
    sns.set_palette(sns.color_palette("tab10",n_colors=10), n_colors=10)
    fig = plt.figure()
    ax = fig.add_subplot(111)
    sns.despine(left=True)
    lineWidth = 1.2
    # the histogram of the data
    try:
        for i in range(len(dataList)):
        	sns.distplot(dataList[i], hist=(not smoothness), kde_kws={"shade": False, "linewidth":lineWidth}, ax=ax, label=legendList[i])
    except Exception as e:
        if Suppress:
            print "When plotting " + dest + " encountered "+str(e)
            return
        else:
            raise e
    ax.set_xlabel(labels[0])
    ax.set_ylabel(labels[1])
    ax.set_title(title)
    #ax.set_xlim(100, 320)
    ax.grid(True)

    # range of axes
    plt.xlim(xRange)
    plt.ylim(yRange)
    if yRange[1] is None: # if user has not defined ymax
        # puff up the y axis some
        y_max = plt.axis()[3]
        plt.ylim(ymax=y_max*1.1)

    plt.savefig(dest_resolver(dest))
    plt.close(fig)

## Generates a plot containing multiple line-graphs
# @param xL an iterable of xpoints (see line_graph_gen xpoints)
# @param yL an iterable of ypoints
# @param legendList iterable of strings with names used for each line
# @param dest a path + filename for the output grapn (ending in .png)
# @param labels a python iterable containing strings (X axis label, Y axis label)
# defaults to no labels
# @ param title a string to use as the graph's title. defaults to no title
# @param stderr a python iterable of the y-error bars desired for each point
# @param square Boolean (False by default) should the x&y axis be the same dimensions?
# @param xRange sets the minimum and maximum value of the x axis (xMin, xMax) Defaults to (None, None)
# @param yRange sets the minimum and maximum value of the y axis (yMin, yMax) Defaults to (None, None), ymax to defaults to a bit above the max y-value
# @param scatter Boolean (False by default) if false, line graph is depicted as scattering of points
def multi_line_graph_gen(xL, yL, legendList, dest, labels = ('',''), title = '', stderrL = [], square = False, xRange=(None,None), yRange=(None,None), scatter=False):
    """
    plot multiple linegraphs on one graph. takes in lists of lists of x and y
    values for each graph, a list of strings for naming each linegraph and an
    output destination enging in .png. optional parameters:
        labels a touple in the format ('x-axis label', 'y-axis label')
        title, a string title of your graph
        stderrL a list of lists of standard error for adding y-error bars to data
    """
    sns.set(style="white", color_codes=True)
    sns.set_palette(sns.color_palette("tab10",n_colors=10), n_colors=10)
    heatMap=True
    # Make the graph
    fig = plt.figure()
    ax = fig.add_subplot(111)
    # Catch bad data inputs
    if len(xL) != len(yL):
        raise ValueError('xL and yL are different lengths!')

    try:
        # Plot each given line
        for i in range(len(xL)):
            x, y = xL[i], yL[i]
            # If given errors, plot them
            if len(stderrL) != 0:
                std = stderrL[i]
                ax.errorbar(x,y,yerr=std, label=legendList[i])
            elif scatter:
                alph = None
                if heatMap:
                    mL=[]
                    for i in range(len(xL)):
                        pl = Counter(zip(xL[i],yL[i]))
                        mL.append(pl.most_common(1)[0])
                    mx = 0
                    for i in range(1,len(mL)):
                        if mL[i][1] > mL[mx][1]:
                            mx=i
                    count = mL[mx][1]
                    alph = 1.0/math.sqrt(count)
                ax.scatter(x, y, label=legendList[i],alpha=alph)
            else:
                ax.plot(x, y, label=legendList[i])
    except Exception as e:
        if Suppress:
            print "When plotting " + dest + " encountered "+str(e)
            return
        else:
            raise e
    # Label the axes
    plt.xlabel(labels[0])
    plt.ylabel(labels[1])

    # range of axes
    plt.xlim(xRange)
    plt.ylim(yRange)
    if yRange[1] is None: # if user has not defined ymax
        # puff up the y axis some
        y_max = plt.axis()[3]
        plt.ylim(ymax=y_max*1.1)

    # Title the graph
    plt.title(title)
    # Add legend
    if len(xL) > 1:
        legend = ax.legend()
    # save # TODO undo this
    mx = 0
    for L in xL+yL:
        mx = max(list(L)+[mx])
    if square:
        plt.axis([-1,mx+2,-1,mx+2])
        plt.grid()
    plt.savefig(dest_resolver(dest))
    plt.close(fig)

with open('dynoTicketing12.csv') as ticketCSV:
    csv_reader = csv.reader(ticketCSV, delimiter=',')
    line_count = 0
    aggregator = []
    legend = []
    for row in csv_reader:
        if line_count == 0:
            for entry in row:
                if line_count == 0:
                    legend += ['time']
                else:
                    legend += ['pred' + str(line_count - 1)]
                aggregator += [[]]
                line_count += 1
        for i in range((len(row))):
            aggregator[i] += [int(row[i])]

    normalizer = []
    for i in range(len(aggregator[0])):
        normalizer.append(aggregator[0][i] - aggregator[0][0])
    times = []
    for i in range(len(legend) - 1):
        times += [normalizer]
    #multi_hist_gen(aggregator[1:], legend[1:], 'tixGraph.png', ('time', 'ticket count'), title='ticketing over time')
    multi_line_graph_gen(times, aggregator[1:], legend[1:], 'tixGraph.png')


        