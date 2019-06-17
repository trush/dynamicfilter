from tests.plotting import *
import toggles
import numpy as np

def gen_message(dest):
    print "Generated graph: " + dest +".png"

def graph_time_vs_freq(results, task_dest):
    """
    Generates time vs. frequency graph for run_multi_sims
    """
    data = results[4]
    dest = task_dest #joinapp/simulation_files/test.png
    labels = ('time','frequency')
    title = 'test w/ 0 chance of none'
    xRange = (None,None)
    yRange = (None,None)
    smoothness = True

    hist_gen(data, dest, labels, title, xRange, yRange, smoothness)
    
    gen_message(task_dest)


