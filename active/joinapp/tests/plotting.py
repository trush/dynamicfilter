# NOTE: MOVE THIS SOMEWHERE? JUST TRYING TO GET IT WORKING

import math
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import datetime as DT
import pylab
import sys

## Generates a single histogram from data
# @param data a python iterable storing integer/float data
# @param dest a path + filename for the output grapn (ending in .png)
# @param labels a python iterable containing strings (X axis label, Y axis label)
# defaults to no labels
# @ param title a string to use as the graph's title. defaults to no title
# @param xRange sets the minimum and maximum value of the x axis (xMin, xMax) Defaults to (None, None)
# @param yRange sets the minimum and maximum value of the y axis (yMin, yMax) Defaults to (None, None), ymax to defaults to a bit above the max y-value
# @param smoothness Boolean (default True). Leave this on until legend display is fixed
def hist_gen(data, dest, labels = ('',''), title='', xRange=(None,None), yRange=(None,None), smoothness=True):
    """
    Automagically generates a Histogram for you from a given list of data and a
    destination name (ending in .png). Can additionally be passed many arguments
        labels a touple in the format ('x-axis label', 'y-axis label')
        title, a string title of your graph
        smoothness, defaults true, set False to get a blocky version instead
    """
    multi_hist_gen([data], [None], dest, labels = labels, title = title,xRange=xRange, yRange=yRange, smoothness=smoothness)

## Generates a graph congaining multiple histograms
# @param dataList a python interable of iterables. each sub iterable containing numeric data
# @param legendList iterable of strings with names used for each dataSet in dataList
# @param dest a path + filename for the output grapn (ending in .png)
# @param labels a python iterable containing strings (X axis label, Y axis label)
# defaults to no labels
# @param title a string to use as the graph's title. defaults to no title
# @param xRange sets the minimum and maximum value of the x axis (xMin, xMax) Defaults to (None, None)
# @param yRange sets the minimum and maximum value of the y axis (yMin, yMax) Defaults to (None, None), ymax to defaults to a bit above the max y-value
# @param smoothness Boolean (default True). Leave this on until legend display is fixed
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

    plt.savefig(dest)
    plt.close(fig)

