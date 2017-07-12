from simulation_files.plotScript import *
import toggles
import numpy as np

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

    yL = [num_tasks_avgs, real_avgs, placeholders_avgs]
    errL = [num_tasks_stds, real_stds, placeholders_stds]

    xL = task_array_sizes
    legend = ["Total tasks", "'Real' Tasks", "Placeholder Tasks"]
    title = "Average Relative Task Counts for " + str(toggles.NUM_SIM) + " Simulations with Queue Size " + str(toggles.PENDING_QUEUE_SIZE)
    labels = ("Size of Active Tasks Array", "Avg. Number of Tasks During Simulations")
    split_bar_graph_gen(yL, xL, task_dest+".png", legend, labels = labels, title = title, split = 'vertical',
                        stderrL = errL)

    if toggles.DEBUG_FLAG:
        print "Generated graph: " + task_dest + ".png"

    if toggles.SIMULATE_TIME:
        cum_total_avgs = cum_times[1]
        cum_total_stds = cum_times[2]
        cum_placeholder_avgs = cum_times[3]
        cum_placeholder_stds = cum_times[4]

        yL = [cum_total_avgs, cum_placeholder_avgs]
        errL = [cum_total_stds, cum_placeholder_stds]
        legend = ["All tasks", "Placeholder tasks"]
        title = "Average Cumulative Work Times for " + str(toggles.NUM_SIM) + " Simulations with Queue Size " + str(toggles.PENDING_QUEUE_SIZE)
        labels = ("Size of Active Tasks Array", "Cumulative Work Time (time steps)")

        split_bar_graph_gen(yL, xL, cum_dest+".png", legend, labels = labels, title = title, split = 'vertical',
                            stderrL = errL)

        if toggles.DEBUG_FLAG:
            print "Generated graph: " + cum_dest + ".png"

def placeholder_time_graph(data, dest):
    '''
    Graphing script used in placeholderActiveTest
    '''
    time_steps = data[0]
    task_counts = data[1]
    placeholder_counts = data[2]
    ip_time = data[3]
    ip_done = data[4]

    xL = [time_steps, time_steps]
    yL = [task_counts, placeholder_counts]
    legendList = ["'Real Tasks'", "Placeholders"]
    labels = ("Time Steps", "Number of tasks released")
    title = "Real and Placeholder Task Counts Over Time - Active Tasks: " + str(toggles.MAX_TASKS) + " Queue: " + str(toggles.PENDING_QUEUE_SIZE)

    multi_line_graph_gen(xL, yL, legendList, dest+".png", labels = labels, title = title)

    if toggles.DEBUG_FLAG:
        print "Generated graph: " + dest + ".png"

def visualize_active_tasks(data, dest):

    xL = data[0][::100]
    yL = [data[i][1][::100] for i in range(1, len(data))]
    legendL = [data[i][0] for i in range(1, len(data))]
    labels = ("Time Steps", "Tasks in Active Array")
    title = "Composition of Active Tasks Array over Time for Queue Size " + str(toggles.PENDING_QUEUE_SIZE) + " and Active Tasks Array " + str(toggles.MAX_TASKS)

    split_bar_graph_gen(yL, xL, dest+".png", legendL, labels=labels, title = title, split = "horizontal", fig_size = (15, 5), tight=True)

    if toggles.DEBUG_FLAG:
        print "Generated graph: " + dest + ".png"
