import math
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import datetime as DT
import pylab
import sys
from collections import defaultdict
import os.path
import csv
#from ..toggles import *
SAVE_CONFIG_DATA = False # Expirimental info writing (doesn't work well atm)

def dest_resolver(dest):
    """
    given a filename (ending in .png) returns a version which wont overide data
    """
    if dest[-4:] != '.png':
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

def get_config_text():
    """
    a probably allready depricated system for getting run info to save into a graph
    """
    eddy_names = ["Queue", "Random", "Controlled"]
    item_sys_names = ["Random", "Item-started", "item-almost-false"]
    text = "Using Eddy system: " + eddy_names[EDDY_SYS-1]
    text += " and Item System: " + item_sys_names[ITEM_SYS] +"\n"
    if SLIDING_WINDOW:
        text+= "Using Sliding window with LIFETIME = " + str(LIFETIME) +'\n'
    elif EDDY_SYS == 1:
        text += "PENDING_QUEUE_SIZE = " + str(PENDING_QUEUE_SIZE) +'\n'
    text += "With consensus options: " +str(NUM_CERTAIN_VOTES) +";"+str(UNCERTAINTY_THRESHOLD) +";"
    text += str(FALSE_THRESHOLD) +";"+str(DECISION_THRESHOLD) +";"+str(CUT_OFF) +"\n"
    return text

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
        if len(row) > 0:
            try:
                int(row[0])
                isInt=True
            except ValueError:
                isInt=False
        if isInt:
            retArray.append(map(int, row))
        else:
            retArray.append(row)
    toRead.close()
    return retArray

def hist_gen(data, dest, labels = ('',''), title='', smoothness=False, writeStats = False):
    """
    Automagically generates a Histogram for you from a given list of data and a
    destination name (ending in .png). Can additionally be passed many arguments
        labels a touple in the format ('x-axis label', 'y-axis label')
        title, a string title of your graph
        smoothness, defaults true, set False to get a blocky version instead
    """
    multi_hist_gen([data], [None], dest, labels = labels, title = title,smoothness=smoothness)


def multi_hist_gen(dataList, legendList, dest, labels=('',''), title='',smoothness=False):
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
    for i in range(len(dataList)):
    	sns.distplot(dataList[i], hist=(not smoothness), kde_kws={"shade": False}, ax=ax, label=legendList[i])
    ax.set_xlabel(labels[0])
    ax.set_ylabel(labels[1])
    ax.set_title(title)
    #ax.set_xlim(100, 320)
    ax.grid(True)
    if SAVE_CONFIG_DATA:
        ax.set_position((.1, .3, .8, .6)) # made room for 6 whole lines
        text = get_config_text()
        fig.text(0.02,0.02,text)

    plt.savefig(dest_resolver(dest))

def line_graph_gen(xpoints, ypoints, dest, labels = ('',''), title = '', stderr = [], square = False, scatter=False):
    """
    Generate a linegraph from a set of x and y points, optional parameters:
        labels a touple in the format ('x-axis label', 'y-axis label')
        title, a string title of your graph
        stderr a list of standard error for adding y-error bars to data
    """
    std = []
    if len(stderr) != 0:
        std = [stderr]
    multi_line_graph_gen([xpoints],[ypoints], [''], dest, labels=labels, title = title, stderrL = std, square = square, scatter=scatter)

def multi_line_graph_gen(xL, yL, legendList, dest, labels = ('',''), title = '', stderrL = [], square = False, scatter=False):
    """
    plot multiple linegraphs on one graph. takes in lists of lists of x and y
    values for each graph, a list of strings for naming each linegraph and an
    output destination enging in .png. optional parameters:
        labels a touple in the format ('x-axis label', 'y-axis label')
        title, a string title of your graph
        stderrL a list of lists of standard error for adding y-error bars to data
    """
    # Make the graph
    fig = plt.figure()
    ax = fig.add_subplot(111)
    # Catch bad data inputs
    if len(xL) != len(yL):
        raise ValueError('xL and yL are different lengths!')

    # Plot each given line
    for i in range(len(xL)):
        x, y = xL[i], yL[i]
        # If given errors, plot them
        if len(stderrL) != 0:
            std = stderrL[i]
            ax.errorbar(x,y,yerr=std, label=legendList[i])
        elif scatter:
            ax.scatter(x, y, label=legendList[i])
        else:
            ax.plot(x, y, label=legendList[i])

    # Label the axes
    plt.xlabel(labels[0])
    plt.ylabel(labels[1])

    # Title the graph
    plt.title(title)
    # Add legend
    if len(xL) > 1:
        legend = ax.legend()
    # save
    mx = 0
    for L in xL+yL:
        mx = max(L+[mx])
    if square:
        plt.axis([-1,mx+2,-1,mx+2])
    plt.savefig(dest_resolver(dest))

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
    plt.bar(pos, data, align='center', alpha = 0.5, yerr = stderr)
    plt.xticks(pos,legend)

    # Label the axes
    plt.xlabel(labels[0])
    plt.ylabel(labels[1])

    # Title the graph
    plt.title(title)
    plt.savefig(dest_resolver(dest))
def stats_bar_graph_gen(dataL, legend, dest, labels = ('',''), title = ''):
    avg, std = [],[]
    for L in dataL:
        avg.append(np.mean(L))
        std.append(np.std(L))
    bar_graph_gen(avg, legend, dest, labels = labels, title = title, stderr = std)

def kcluster(data,k,iterations = 300):
    mL,pL = [],[]
    diff = len(data)/(k)
    for i in range(k):
        mL.append(data[i*diff])
        pL.append([])
    for i in range(iterations):
        for point in data:
            dL = []
            for mean in mL:
                dL.append(abs(point-mean))
            closest = min(dL)
            index = dL.index(closest)
            pL[index].append(point)
        for i in range(len(mL)):
            mL[i] = np.mean(pL[i])
    return pL
