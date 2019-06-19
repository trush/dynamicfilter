from tests.plotting import *
import toggles
import numpy as np

def gen_message(dest):
    print "Generated graph: " + dest

## @brief graphs a histogram of time to run simulations
# @param results from multiple simulation runs
# @param task_dest where the graph will save
def graph_time(results, task_dest):
    data = results[4]
    dest = task_dest #joinapp/simulation_files/test.png
    labels = ('time','frequency')
    title = 'test w/ 0 chance of none'
    xRange = (None,None)
    yRange = (None,None)
    smoothness = True

    hist_gen(data, dest, labels, title, xRange, yRange, smoothness)
    
    gen_message(task_dest)

## @brief graphs a line graph of primary items left vs. tasks completed
# @param results from multiple simulation runs
# @param task_dest where the graph will save
def graph_prim_items_left(results, task_dest):
    xL = []
    #gets assignments for x list
    for n in range(len(results[5])):
        xpoints = range(results[5][n])
        xL.append(xpoints)
    yL = results[6]


    # print "y list ",len(yL[0])
    # print "x list ",len(xL[0])
    # for yList in yL:
    #     for xList in xL:
    #         if len(yList) < len(xList):
    #             xList = xList[:len(xList)-len(yList)]
    #         elif len(xList) < len(yList):
    #             yList = yList[:len(yList)-len(xList)]
    #             xList += [0]*(len(yList)-len(xList))


    legendList = []
    for n in range(len(results[5])):
        legendList.append(n)
    dest = task_dest
    labels = ('tasks completed','number of primary items left')
    title = 'IW find pair all then sec pred all'
    stderrL = []
    square = False
    xRange = (None,None)
    yRange = (None,None)
    scatter = False

    multi_line_graph_gen(xL, yL, legendList, dest, labels, title, stderrL, square, xRange, yRange, scatter)

    gen_message(task_dest)


