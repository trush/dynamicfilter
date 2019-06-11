from simulation_files.plotScript import *
import toggles
import numpy as np

def gen_message(dest):
    print "Generated graph: " + dest+".png"

# taken from graphGen.py from dynamicfilterapp
def task_distributions(data, dest, real):
    dataL = [data[i][1] for i in range(len(data))]
    legendL = [str(data[i][0]) for i in range(len(data))]

    if real:
        labels = ("Number of Real Tasks During a Simulation", "Frequency")
        title = "Number of Real Tasks Completed for Various Algorithm Configurations - " + str(toggles.NUM_SIM) + " Simulations"
    else:
        labels = ("Number of Tasks During a Simulation", "Frequency")
        title = "Number of Tasks Completed for Various Algorithm Configurations - " + str(toggles.NUM_SIM) + " Simulations"


    multi_hist_gen(dataL, legendL, dest+".png", labels = labels, title=title, smoothness=True)

def simulated_time_distributions(data, dest):
    dataL = [data[i][1] for i in range(len(data))]
    legendL = [str(data[i][0]) for i in range(len(data))]
    labels = ("Simulated Time During Simulations", "Frequency")
    title = "Simulated Time for Various Algorithm Configurations - " + str(toggles.NUM_SIM) + " Simulations"

    multi_hist_gen(dataL, legendL, dest+".png", labels = labels, title=title, smoothness=True)
