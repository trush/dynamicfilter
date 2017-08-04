import math
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import datetime as DT
import pylab
import sys
from collections import defaultdict, Counter
import os.path
from os import makedirs
import csv
Suppress = True

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

## Writes data to a csv in a predictable, standardized way
# @param filename the path + name of the output csv
# @param the data to write. format: [[row1],[row2]...[rowN]]
def generic_csv_write(filename, data):
    """
    given a file name and a list, writes out the data to be easily recalled with
    generic_csv_read. assumes that data is a list of lists. please do that
    """
    toWrite = open(filename, 'w')
    writer = csv.writer(toWrite)
    for row in data:
        writer.writerow(row)
    toWrite.close()

## Reads back in data that was saved with generic_csv_read
# @param filename the path + name of the file to read
# @returns the data originally written
def generic_csv_read(filename):
    """
    Given a file name, returns a list of lists containing all the data from a
    single row in a list. Properly converts ints assuming that any row beginning
    with an int contains only ints
    """
    retArray = []
    toRead = open(filename,'r')
    reader = csv.reader(toRead)
    for row in reader:
        isFloat=False
        if len(row) > 0:
            try:
                float(row[0])
                isFloat=True
            except ValueError:
                isFloat=False
        if isFloat:
            retArray.append(map(float, row))
        else:
            retArray.append(row)
    toRead.close()
    return retArray

## Generates a single histogram from data
# @param data a python iterable storing integer/float data
# @param dest a path + filename for the output grapn (ending in .png)
# @param labels a python iterable containing strings (X axis label, Y axis label)
# defaults to no labels
# @ param title a string to use as the graph's title. defaults to no title
# @param smoothness Boolean (default True). Leave this on until legend display is fixed
def hist_gen(data, dest, labels = ('',''), title='', smoothness=True):
    """
    Automagically generates a Histogram for you from a given list of data and a
    destination name (ending in .png). Can additionally be passed many arguments
        labels a touple in the format ('x-axis label', 'y-axis label')
        title, a string title of your graph
        smoothness, defaults true, set False to get a blocky version instead
    """
    multi_hist_gen([data], [None], dest, labels = labels, title = title,smoothness=smoothness)

## Generates a graph congaining multiple histograms
# @param dataList a python interable of iterables. each sub iterable containing numeric data
# @param legendList iterable of strings with names used for each dataSet in dataList
# @param dest a path + filename for the output grapn (ending in .png)
# @param labels a python iterable containing strings (X axis label, Y axis label)
# defaults to no labels
# @ param title a string to use as the graph's title. defaults to no title
# @param smoothness Boolean (default True). Leave this on until legend display is fixed
def multi_hist_gen(dataList, legendList, dest, labels=('',''), title='',smoothness=True):
    """
    Very similar to hist_gen, however takes a list of datasets and a list of
    names of your datasets and a destination name, plots all datasets on one
    plot in differing colors. takes in optional labels and title like before.
    """
    #TODO Consider axis ranging?
    #TODO Print out relevant data to a description?
    if len(legendList) < len(dataList):
        raise ValueError('Not enough legends ')
    sns.set(style="white", palette="muted", color_codes=True)
    fig = plt.figure()
    ax = fig.add_subplot(111)
    sns.despine(left=True)
    # the histogram of the data
    try:
        for i in range(len(dataList)):
        	sns.distplot(dataList[i], hist=(not smoothness), kde_kws={"shade": False}, ax=ax, label=legendList[i])
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
    # puff up the y axis some
    y_max = plt.axis()[3]
    plt.ylim(ymax=y_max*1.25)
    plt.savefig(dest_resolver(dest))

## Generates a plot containing a line-graph
# @param xpoints a python iterable containing the x values of each point
# @param ypoints a python iterable containing the matching y values for each point in xpoints
# @param dest a path + filename for the output grapn (ending in .png)
# @param labels a python iterable containing strings (X axis label, Y axis label)
# defaults to no labels
# @ param title a string to use as the graph's title. defaults to no title
# @param stderr a python iterable of the y-error bars desired for each point
# @param square Boolean (False by default) should the x&y axis be the same dimensions?
# @param scatter Boolean (False by default) if false, line graph is depicted as scattering of points
def line_graph_gen(xpoints, ypoints, dest, labels = ('',''), title = '', stderr = [], square = False, scatter=False):
    """
    Generate a linegraph from a set of x and y points, optional parameters:
        labels a tuple in the format ('x-axis label', 'y-axis label')
        title, a string title of your graph
        stderr a list of standard error for adding y-error bars to data
    """
    std = []
    if len(stderr) != 0:
        std = [stderr]
    multi_line_graph_gen([xpoints],[ypoints], [''], dest, labels=labels, title = title, stderrL = std, square = square, scatter=scatter)

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
# @param scatter Boolean (False by default) if false, line graph is depicted as scattering of points
def multi_line_graph_gen(xL, yL, legendList, dest, labels = ('',''), title = '', stderrL = [], square = False, scatter=False):
    """
    plot multiple linegraphs on one graph. takes in lists of lists of x and y
    values for each graph, a list of strings for naming each linegraph and an
    output destination enging in .png. optional parameters:
        labels a touple in the format ('x-axis label', 'y-axis label')
        title, a string title of your graph
        stderrL a list of lists of standard error for adding y-error bars to data
    """
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

    # puff up the y axis some
    y_max = plt.axis()[3]
    plt.ylim(ymax=y_max*1.25)

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

## Generates a set of bargraphs
# @param data a python iterable storing integer/float data for the height of each bar
# @param legend a string for the label under each bar
# @param dest a path + filename for the output grapn (ending in .png)
# @param labels a python iterable containing strings (X axis label, Y axis label)
# defaults to no labels
# @ param title a string to use as the graph's title. defaults to no title
# @param stderr a python iterable of the y-error bars desired for the top of each bar
def bar_graph_gen(data, legend, dest, labels = ('',''), title = '', stderr = None):
    """
    Generate a bargraph from a list of heights and a list of names optional parameters:
        labels a touple in the format ('x-axis label', 'y-axis label')
        title, a string title of your graph
        stderr a list of standard error for adding y-error bars to data
    """
    if len(data) != len(legend):
        raise ValueError('data and legend are different lengths!')
    fig = plt.figure()
    pos = np.arange(len(data))
    try:
        plt.bar(pos, data, align='center', alpha = 0.5, yerr = stderr)
    except Exception as e:
        if Suppress:
            print "When plotting " + dest + " encountered "+str(e)
            return
        else:
            raise e
    plt.xticks(pos,legend)

    # Label the axes
    plt.xlabel(labels[0])
    plt.ylabel(labels[1])

    # puff up the y axis some
    y_max = plt.axis()[3]
    plt.ylim(ymax=y_max*1.25)

    # Title the graph
    plt.title(title)
    plt.savefig(dest_resolver(dest))

def split_bar_graph_gen(dataL, xL, dest, legend ,labels = ('',''), title = '',split='vertical', stderrL = None, fig_size = None, tight=False):
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
                plt.bar(ind,dataL[i],width, yerr=stderrL[i], label = legend[i])

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
    plt.xticks(pos,xL)
    plt.legend()

    # Label the axes
    plt.xlabel(labels[0])
    plt.ylabel(labels[1])

    # puff up the y axis some
    y_max = plt.axis()[3]
    plt.ylim(ymax=y_max*1.25)

    # Title the graph
    plt.title(title)
    if tight:
        fig.tight_layout()
    plt.savefig(dest_resolver(dest))

## A wrapper for bar_graph_gen Calculates statistics for you
# @param dataL a python iterable of iterables containing numeric data
# @param legend a string for the label under each bar
# @param dest a path + filename for the output grapn (ending in .png)
# @param labels a python iterable containing strings (X axis label, Y axis label)
# defaults to no labels
# @ param title a string to use as the graph's title. defaults to no title
def stats_bar_graph_gen(dataL, legend, dest, labels = ('',''), title = ''):
    avg, std = [],[]
    for L in dataL:
        avg.append(np.mean(L))
        std.append(np.std(L))
    bar_graph_gen(avg, legend, dest, labels = labels, title = title, stderr = std)

def packageMaker(dest,conf):
    """Generates a "package" for the current simulation"""
    if not os.path.exists(dest):
        makedirs(dest)
    configName = "config.ini"
    with open(dest+configName,'w') as f:
        f.write(conf)
