import math
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import datetime as DT
import pylab
import sys
from collections import defaultdict

def hist_gen(data, dest, labels = ('',''), title='', smoothness=True):
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

    plt.savefig(dest)
