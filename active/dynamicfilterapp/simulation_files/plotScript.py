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
    if os.path.isfile(dest):
        name = dest
        num = 1
        name += '(1)'
        while os.path.isfile(name):
            num+=1
            name[-2] = num
        return name
    else:
        return dest


def hist_gen(data, dest, labels = ('',''), title='', smoothness=True):
    """
    Automagically generates a Histogram for you from a given list of data and a
    destination name (ending in .png). Can additionally be passed many arguments
        labels a touple in the format ('x-axis label', 'y-axis label')
        title, a string title of your graph
        smoothness, defaults true, set False to get a blocky version instead
    """

    fig = plt.figure()
    ax = fig.add_subplot(111)
    if smoothness:
        sns.set(style="white", palette="muted", color_codes=True)
        sns.despine(left=True)
        sns.distplot(data, hist=False, kde_kws={"shade": False}, ax=ax)
    else:
        n, bins, patches = ax.hist(data, 1000, normed=1, facecolor='green')
        bincenters = 0.5*(bins[1:]+bins[:-1])
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 0.3)
	ax.set_xlabel(labels[0])
	ax.set_ylabel(labels[1])
	ax.set_title(title)
	ax.grid(True)
    plt.savefig(dest)

def multi_hist_gen(dataList, legendList, dest, labels=('',''), title=''):
    """
    Very similar to hist_gen, however takes a list of datasets and a list of
    names of your datasets and a destination name, plots all datasets on one
    plot in differing colors. takes in optional labels and title like before.
    """

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
    # Add legend
    legend = ax.legend()
    #ax.set_xlim(100, 320)
    ax.grid(True)

    plt.savefig(dest)

def line_graph_gen(xpoints, ypoints, dest, labels = ('',''), title = '', stderr = []):
    """
    Generate a linegraph from a set of x and y points, similarly takes in
    optional axis-labels and title, also takes in error bars
    """

    # Make the graph
    fig = plt.figure()
    ax = fig.add_subplot(111)

    #ax.grid()
    if len(stderr) != 0:
        ax.errorbar(xpoints,ypoints,yerr=stderr)
    else:
        ax.plot(xpoints, ypoints)
    # Label the axes
    plt.xlabel(labels[0])
    plt.ylabel(labels[1])

    # Title the graph
    plt.title(title)


    #plot curve of best fit
    #plt.plot(queue_size, np.poly1d(np.polyfit(queue_size, num_tasks, 1))(queue_size))
    #plt.show()
    plt.savefig(dest)
def multi_line_graph_gen(xL, yL, dest, legendList, labels = ('',''), title = '', stderrL = []):
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
    legend = ax.legend()
    # save
    plt.savefig(dest)
