from simulation_files.plotScript import *
import toggles
import numpy as np

def gen_message(dest):
    if toggles.DEBUG_FLAG:
        print "Generated graph:" + dest+".png"

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

    gen_message(task_dest)

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

        gen_message(cum_dest)

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

    gen_message(dest)

def visualize_active_tasks(data, dest):

    xL = data[0][::100]
    yL = [data[i][1][::100] for i in range(1, len(data))]
    legendL = [data[i][0] for i in range(1, len(data))]
    labels = ("Time Steps", "Tasks in Active Array")
    title = "Composition of Active Tasks Array over Time for Queue Size " + str(toggles.PENDING_QUEUE_SIZE) + " and Active Tasks Array " + str(toggles.MAX_TASKS)

    split_bar_graph_gen(yL, xL, dest+".png", legendL, labels=labels, title = title, split = "horizontal", fig_size = (15, 5), tight=True)

    gen_message(dest)

def ticket_counts(data, dest):
    xL = []
    for i in range(1, len(data)):
        xL.append(data[0])
    yL = [data[i][1] for i in range(1, len(data))]
    legendL = [data[i][0] for i in range(1, len(data))]
    labels = ("Time Steps", "Number of Tickets")
    title = "Number of Tickets for Each Predicate During 1 Simulation"

    multi_line_graph_gen(xL, yL, legendL, dest+".png", labels = labels, title = title)

    gen_message(dest)

def queue_sizes(data, dest):
    xL = []
    for i in range(1, len(data)):
        xL.append(data[0])
    yL = [data[i][1] for i in range(1, len(data))]
    legendL = [data[i][0] for i in range(1, len(data))]
    labels = ("Time Steps", "Sizes of Predicate Queues")
    title = "Queue Sizes for Each Predicate During 1 Simulation"

    multi_line_graph_gen(xL, yL, legendL, dest+".png", labels = labels, title = title)

    gen_message(dest)

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

    gen_message(dest)

def simulated_time_distributions(data, dest):
    dataL = [data[i][1] for i in range(len(data))]
    legendL = [str(data[i][0]) for i in range(len(data))]
    labels = ("Simulated Time During Simulations", "Frequency")
    title = "Simulated Time for Various Algorithm Configurations - " + str(toggles.NUM_SIM) + " Simulations"

    multi_hist_gen(dataL, legendL, dest+".png", labels = labels, title=title, smoothness=True)

    gen_message(dest)
