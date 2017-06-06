import math
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import datetime as DT
import pylab
import sys
from collections import defaultdict
import os.path
from ..toggles import *
SAVE_CONFIG_DATA = False

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



def hist_gen(data, dest, labels = ('',''), title='', smoothness=True, writeStats = False):
    """
    Automagically generates a Histogram for you from a given list of data and a
    destination name (ending in .png). Can additionally be passed many arguments
        labels a touple in the format ('x-axis label', 'y-axis label')
        title, a string title of your graph
        smoothness, defaults true, set False to get a blocky version instead
    """

    if smoothness:
        text = ''
        if writeStats:
            avg = int(np.mean(data))
            n = len(data)
            text = ' $\mu=$' + str(avg) + ' $n=$'+str(n)
        multi_hist_gen([data], [None], dest, labels = labels, title = title + text)
    else:
        #TODO make this section actually work consistently
        mx = max(data)
        fig = plt.figure()
        ax = fig.add_subplot(111)
        n, bins, patches = ax.hist(data, 30 , normed=1, facecolor='g')
        ax.set_xlim(0, mx+5)
        ax.set_ylim(0, 0.3)
    	ax.set_xlabel(labels[0])
    	ax.set_ylabel(labels[1])
    	ax.set_title(title)
    	ax.grid(True)
        plt.savefig(dest_resolver(dest))

def multi_hist_gen(dataList, legendList, dest, labels=('',''), title=''):
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
    	sns.distplot(dataList[i], hist=False, kde_kws={"shade": False}, ax=ax, label=legendList[i])
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

def line_graph_gen(xpoints, ypoints, dest, labels = ('',''), title = '', stderr = [], square = False):
    """
    Generate a linegraph from a set of x and y points, optional parameters:
        labels a touple in the format ('x-axis label', 'y-axis label')
        title, a string title of your graph
        stderr a list of standard error for adding y-error bars to data
    """
    std = []
    if len(stderr) != 0:
        std = [stderr]
    multi_line_graph_gen([xpoints],[ypoints], [''], dest, labels=labels, title = title, stderrL = std, square = square)

def multi_line_graph_gen(xL, yL, legendList, dest, labels = ('',''), title = '', stderrL = [], square = False):
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
