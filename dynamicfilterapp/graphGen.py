from simulation_files.plotScript import *
import toggles
import numpy as np

def gen_message(dest):
    if toggles.DEBUG_FLAG:
        print "Generated graph: " + dest+".png"

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
    title = "Real and Placeholder Task Counts Over Time for Current Configuration"
    multi_line_graph_gen(xL, yL, legendList, dest+".png", labels = labels, title = title)

    gen_message(dest)

def visualize_active_tasks(data, dest):

    xL = data[0][::20]
    yL = [data[i][1][::20] for i in range(1, len(data))]
    legendL = [data[i][0] for i in range(1, len(data))]
    labels = ("Time Steps", "Tasks in Active Array")
    title = "Active Tasks Over Time for Current Configuration"

    split_bar_graph_gen(yL, xL, dest+".png", legendL, labels=labels, title = title, split = "horizontal", fig_size = (15, 5), tight=True)

    gen_message(dest)

def ticket_counts(data, dest):
    xL = []
    for i in range(1, len(data)):
        xL.append(data[0])
    yL = [data[i][1] for i in range(1, len(data))]
    legendL = [data[i][0] for i in range(1, len(data))]
    labels = ("Time Steps", "Number of Tickets")
    title = "Number of Tickets Over Time for Current Configuration"

    multi_line_graph_gen(xL, yL, legendL, dest+".png", labels = labels, title = title)

    gen_message(dest)

def queue_sizes(data, dest):
    xL = []
    for i in range(1, len(data)):
        xL.append(data[0])
    yL = [data[i][1] for i in range(1, len(data))]
    legendL = [data[i][0] for i in range(1, len(data))]
    labels = ("Time Steps", "Sizes of Predicate Queues")
    title = "Queue Sizes for Each Predicate for Current Configuration"

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

def ticket_distributions(dataL, legendL, dest, numSim):
    # print histogram for each predicate's ticket after each simulation of the same setting
    labels = ("Number of Tickets", "Frequency")
    title = "Number of Tickets for Predicates in Current Configuration for " + str(numSim) + " Simulations"

    multi_hist_gen(dataL, legendL, dest+".png", labels = labels, title = title, smoothness = True)

    gen_message(dest)

def task_distributions_over_settings (data, dest):
    # print histogram for each predicate's ticket after each simulation of the same setting
    dataL = []
    legendL = []
    for tup in range(len(data)):
        legendL.append(data[tup][0]) # settingCount
        dataL.append(data[tup][1])   # task list

    labels = ("Number of Tasks", "Frequency")
    title = "Number of Tasks for Different Configurations"

    multi_hist_gen(dataL, legendL, dest+".png", labels = labels, title = title, smoothness = True)

    gen_message(dest)

def task_count(data, legend, dest):
    # task count for a single simulation
    labels = ('Predicates', 'Tasks')
    title = 'Number of Tasks for Predicates with Current Configuration'

    bar_graph_gen(data, legend, dest+".png", labels = labels, title = title)

    gen_message(dest)


def task_count_over_settings(data, legend, dest, numSim):
    labels = ('Predicates', 'Tasks')
    title = 'Number of Tasks for Predicates with Current Configuration over ' + str(numSim) +'Simulations'

    bar_graph_gen(data, legend, dest+".png", labels = labels, title = title)

    gen_message(dest)

def ips_done(data, dest, time):
    if time:
        num = 1
        caption = "Time Steps"
    else:
        num = 2
        caption = "Number of Tasks Completed"
    labels = (caption, "Number IP Pairs Completed")
    title = "Number IP Pairs Done vs. " + caption + " During 1 Simulation"
    line_graph_gen(data[num], data[0], dest+".png", labels=labels, title=title)

    gen_message(dest)

def consensus_over_time(tasks, legend, consensus, dest):
    multi_line_graph_gen([tasks]*len(legend), consensus, legend,
                        dest + ".png", labels = ('Tasks','Max Num Tasks'),
						title = "Consensus Algorithm Over Time")
    gen_message(dest)

def item_routing(data1, data2, labels, dest):
    title = "Items Routed To Predicates During One Simulation"
    line_graph_gen(data1, data2, dest+'.png', labels=labels, title=title, square=True)

    gen_message(dest)

def single_pair_cost(data, dest):
    hist_gen(data, dest+".png", labels = ("Number of Tasks", "Frequency"),
            title = "Distribution of Single Pair Cost", smoothness = True)

    gen_message(dest)

def function_timing(data, output_path, time):
    dest = output_path + "simTimes"
    line_graph_gen(data[0], data[1], dest+".png", labels=("Number of simulations run", "Simulation runtime") )
    gen_message(dest)

    dest = output_path + "eddyTimes"
    line_graph_gen(data[0], data[2], dest+".png", labels=("Number of simulations run", "Total pending_eddy() runtime per sim"))
    gen_message(dest)

    dest = output_path + "taskTimes"
    line_graph_gen(data[0], data[3], dest+".png", labels = ("Number of simulations run", "Total simulate_task() runtime per sim"))
    gen_message(dest)

    if not time:
        dest = output_path + "workerDoneTimes"
        line_graph_gen(data[0], data[4], labels=("Number of simulations run", "Total worker_done() runtime per sim") )
        gen_message(dest)

    xL = [data[0]*(len(data)-2)]
    yL = data[1:]
    legends = ["run_sim()", "pending_eddy()", "simulate_task()"]
    if not time:
        legends.append("worker_done()")
        xL.append(data[0])
    labels = ("Number simulations run", "Duration of function call (seconds)")
    title = "Cum. Duration function calls vs. Number Simulations Run"
    dest = output_path + "funcTimes"

    multi_line_graph_gen(xL, yL, legends, dest+".png", labels=labels, title=title)
    gen_message(dest)

def accuracy_change_votes(xL, incorrList, incorrStdList, tasksList, taskStdList, legendList, output_path):
    dest = output_path + "varyMinVotes_taskCounts"
    labels = ("Uncertainty Threshold", "Avg. Number Tasks Per Sim")
    title = "Average Number Tasks Per Sim Vs. Uncertainty, Varying Min. # Votes"
    multi_line_graph_gen(xL, tasksList, legendList, dest+".png", labels=labels, title=title, stderrL=taskStdList)

    gen_message(dest)

    dest = output_path + "varyMinVotes_incorrectCounts"
    labels = ("Uncertainty Threshold", "Avg. Number of Incorrect Items Per Sim")
    title = "Average Number Incorrect Items Per Sim Vs. Uncertainty, Varying Min. # Votes"
    multi_line_graph_gen(xL, incorrList, legendList, dest+".png",labels=labels, title=title, stderrL=incorrStdList )

    gen_message(dest)

def abstract_sim(globalVar, listOfValuesToTest, avgL, stdL, counts, output_path):
    dest = output_path + "abstract_sim_"
    labels = (str(globalVar),'Task Count')
    title = "Impact of Varying " + str(globalVar) + " on Task Count"
    line_graph_gen(listOfValuesToTest, avgL, dest+"_line.png", stderr=stdL, labels=labels, title=title )

    gen_message(dest+"_line")

    if len(counts[0]) > 1:
        multi_hist_gen(counts, listOfValuesToTest, dest+"_hist.png", labels=labels, title=title )

        gen_message(dest+"_hist")

    else:
        print "Only ran one sim, ignoring hist generation for abstract sim."
