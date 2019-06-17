# NOTE: MOVE THIS SOMEWHERE? JUST TRYING TO GET IT WORKING

import math
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import datetime as DT
import pylab
import sys
Suppress = True

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

## Generates a plot containing a line-graph
# @param xpoints a python iterable containing the x values of each point
# @param ypoints a python iterable containing the matching y values for each point in xpoints
# @param dest a path + filename for the output grapn (ending in .png)
# @param labels a python iterable containing strings (X axis label, Y axis label)
# defaults to no labels
# @ param title a string to use as the graph's title. defaults to no title
# @param stderr a python iterable of the y-error bars desired for each point
# @param square Boolean (False by default) should the x&y axis be the same dimensions?
# @param xRange sets the minimum and maximum value of the x axis (xMin, xMax) Defaults to (None, None)
# @param yRange sets the minimum and maximum value of the y axis (yMin, yMax) Defaults to (None, None), ymax to defaults to a bit above the max y-value
# @param scatter Boolean (False by default) if false, line graph is depicted as scattering of points
def line_graph_gen(xpoints, ypoints, dest, labels = ('',''), title = '', stderr = [], square = False, xRange=(None,None), yRange=(None,None), scatter=False):
    """
    Generate a linegraph from a set of x and y points, optional parameters:
        labels a tuple in the format ('x-axis label', 'y-axis label')
        title, a string title of your graph
        stderr a list of standard error for adding y-error bars to data
    """
    std = []
    if len(stderr) != 0:
        std = [stderr]
    multi_line_graph_gen([xpoints],[ypoints], [''], dest, labels=labels, title = title, stderrL = std, square = square, xRange=xRange, yRange=yRange, scatter=scatter)

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
    plt.savefig(dest)
    plt.close(fig)
