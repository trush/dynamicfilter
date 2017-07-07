from simulation_files.plotScript import *
import toggles
import numpy as np

task_counts = [[10, 11], [3, 3], [], [3, 3], [], [3, 3], []]
def placeholder_graphing(task_counts, task_dest, cum_times, cum_dest):
    """
    Graphing script for the placeholderActiveTest method in test_simulations
    """
    task_array_sizes = task_counts[0]
    num_tasks_avgs = task_counts[1]
    num_tasks_stds = task_counts[2]
    placeholders_avgs = task_counts[3]
    placeholders_stds = task_counts[4]
    real_avgs = task_counts[5]
    real_stds = task_counts[6]

    #yL = [num_tasks_avgs, real_avgs, placeholders_avgs]
    yL = [[3, 4], [3, 2], [3, 1], [3, 6]]
    errL = [num_tasks_stds, real_stds, placeholders_stds]

    xL = task_array_sizes
    legend = ["Total tasks", "'Real' Tasks", "Placeholder Tasks", "blah"]
    title = "Average Relative Task Counts for " + str(toggles.NUM_SIM) + " Simulations"
    labels = ("Size of Active Tasks Array", "Avg. Number of Tasks During Simulations")
    split_bar_graph_gen(yL, xL, task_dest+".png", legend, labels = labels, title = title, split = 'horizontal',
                        stderrL = errL)

    if toggles.DEBUG_FLAG:
        print "Generated graph: " + task_dest + ".png"


    cum_total_avgs = cum_times[1]
    cum_total_stds = cum_times[2]
    cum_placeholder_avgs = cum_times[3]
    cum_placeholder_stds = cum_times[4]

    yL = [cum_total_avgs, cum_placeholder_avgs]
    errL = [cum_total_stds, cum_placeholder_stds]
    legend = ["All tasks", "Placeholder tasks"]
    title = "Average Cumulative Work Times for " + str(toggles.NUM_SIM) + " Simulations"
    labels = ("Size of Active Tasks Array", "Cumulative Work Time (seconds)")

    split_bar_graph_gen(yL, xL, cum_dest+".png", legend, labels = labels, title = title, split = 'vertical',
                        stderrL = errL)

    if toggles.DEBUG_FLAG:
        print "Generated graph: " + cum_dest + ".png"

placeholder_graphing(task_counts, "new_aa_placeholderLegend", [[10], [10], [1], [20], [1]], "new_aa_cumulative")
