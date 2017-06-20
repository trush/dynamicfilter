import math
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import datetime as DT
import pylab
import sys
from collections import defaultdict
import os.path

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
        mx = max(L)
    if square:
        plt.axis([-1,mx,-1,mx])
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
