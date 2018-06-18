import datetime as DT
from math import *
from random import *
import csv
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import numpy as np
import plotly.plotly as py
import plotly.graph_objs as go
from scipy import stats

#toggles
DEBUG = False
GRAPHS = False

#dictionary for testing    
evaluated_with_PJF_private = {}

# Only used for mass testing
join_selectivities_to_test = [0.3,0.6,0.9]
PJF_selectivities_to_test =  []
for i in range(10):
    PJF_selectivities_to_test += [0.6]
pairwise_time_to_test = [10.0]
time_to_eval_PJF_test = []
size_l1_to_test = []
size_l2_to_test = [10]
for i in range(10):
    # pairwise_time_to_test += [(i+1)*10.0]
    time_to_eval_PJF_test += [(i+1)*10.0]
    size_l1_to_test += [(i+1)*10]
    # size_l2_to_test += [(i+1)*10]

# returns results from join
# takes in the settings
# need to save the average at the end of the join run through
def join(H, M, join_settings):
    """ Assuming that we have two complete lists that need to b joined, mimicks human join
    with predetermined average cost per HIT """

    #### JOIN SETTINGS ####
    trial_number           = join_settings[0]
    JOIN_SELECTIVITY       = join_settings[1]
    PJF_SELECTIVITY        = join_settings[2]
    PAIRWISE_TIME_PER_TASK = join_settings[3]
    TIME_TO_GENERATE_TASK  = 0.0
    TIME_TO_EVAL_PJF       = join_settings[4]


    if DEBUG:
        print 'INSIDE JOIN -----------------'
        print 'JOIN_SELECTIVITY: ' + str(JOIN_SELECTIVITY)
        print 'PJF_SELECTIVITY: ' + str(PJF_SELECTIVITY)
        print 'PAIRWISE_TIME_PER_TASK: ' + str(PAIRWISE_TIME_PER_TASK) 
        print 'TIME_TO_GENERATE_TASK: ' + str(TIME_TO_GENERATE_TASK)
        print 'TIME_TO_EVAL_PJF: ' + str(TIME_TO_EVAL_PJF)
        print '-----------------------------'

    #### INITIALIZE VARIABLES TO USE ####
    cost_of_PJF, PJF = generate_PJF(PJF_SELECTIVITY) # TODO: what are we going to do with the cost_of_PJF?
    avg_cost = 0
    num_pairs = 0
    num_pairs_processed = 0
    results_from_join = [ ]
    evaluated_with_PJF = { }
    run_summary = [[],[],[],[]]

    ### USED FOR ADAPTIVE ALGORITHM ###
    num_pairs1 = 0
    num_pairs2 = 0
    avg_cost1 = 40.0 #just to bias towards PJF
    avg_cost2 = 0.0
    results_from_join1 = [ ]
    evaluated_with_PJF1 = { }
    

    #### SEND OUT JOIN TUPLES ####
    for i in H:
        for j in M:
            current_pair = [i, j] 

            ### ADAPTIVE GROUP: SPLITS BASED ON AVERAGE TIME COST ###
            if(uniform(0.0,1.0) > (avg_cost1/(avg_cost1 + avg_cost2))):
                timer_val = 0
                # Generate task of current pair
                timer_val += TIME_TO_GENERATE_TASK
                # Choose whether to add to results_from_join
                timer_val += PAIRWISE_TIME_PER_TASK
                if(uniform(0.0,1.0) < JOIN_SELECTIVITY):
                    results_from_join1.append(current_pair)
                avg_cost1=(avg_cost1*num_pairs1+ timer_val)/(num_pairs1+1)
                num_pairs1 += 1
            else:
                timer_val = 0
                if(not i in evaluated_with_PJF1):
                    # save results of PJF to avoid repeated work
                    evaluated_with_PJF1[i] = evaluate(PJF_SELECTIVITY, PJF,i)
                    timer_val += TIME_TO_EVAL_PJF
                if (not j in evaluated_with_PJF1):
                    # save results of PJF to avoid repeated work
                    evaluated_with_PJF1[j] = evaluate(PJF_SELECTIVITY, PJF,j)
                    timer_val += TIME_TO_EVAL_PJF
                if(evaluated_with_PJF1[i] and evaluated_with_PJF1[j]):
                    # Generate task of current pair
                    timer_val += TIME_TO_GENERATE_TASK
                    # Choose whether to add to results_from_join
                    timer_val += PAIRWISE_TIME_PER_TASK
                if(uniform(0.0,1.0) < JOIN_SELECTIVITY):
                        results_from_join1.append(current_pair)
                avg_cost2=(avg_cost2*num_pairs2+ timer_val)/(num_pairs2+1)
                num_pairs2 += 1

            #### CONTROL GROUP: COMPLETELY USING PJF THEN PW JOIN ####
            timer_val = 0
            if(not i in evaluated_with_PJF):
                # save results of PJF to avoid repeated work
                evaluated_with_PJF[i] = evaluate(PJF_SELECTIVITY, PJF,i)
                timer_val += TIME_TO_EVAL_PJF
            if (not j in evaluated_with_PJF):
                # save results of PJF to avoid repeated work
                evaluated_with_PJF[j] = evaluate(PJF_SELECTIVITY, PJF,j)
                timer_val += TIME_TO_EVAL_PJF
            if(evaluated_with_PJF[i] and evaluated_with_PJF[j]):
                # Generate task of current pair
                timer_val += TIME_TO_GENERATE_TASK
                # Choose whether to add to results_from_join
                timer_val += PAIRWISE_TIME_PER_TASK
            if(random() < JOIN_SELECTIVITY):
                    results_from_join.append(current_pair)
            avg_cost=(avg_cost*num_pairs+ timer_val)/(num_pairs+1)
            num_pairs += 1

            num_pairs_processed +=1
            #### DEBUGGING ####
            # if DEBUG:
            #     print "After pair " + str(num_pairs_processed) + " has been processed..."
            #     print "ADAPTIVE ALGORITHM TOTAL AVERAGE COST: " + str((avg_cost1*num_pairs1+avg_cost2*num_pairs2)/(num_pairs1+num_pairs2))
            #     print "AVERAGE COST WITH PJF = " + str(avg_cost) + " WHEN SENT [ "+str(num_pairs)+" ] PAIRS"
            #     print "AVERAGE COST WITHOUT PJF = " + str(PAIRWISE_TIME_PER_TASK+TIME_TO_GENERATE_TASK)
            #     print "PJF DICTIONARY = " + str(evaluated_with_PJF)

            if GRAPHS:
                run_summary[0].append(num_pairs_processed)
                run_summary[1].append((avg_cost1*num_pairs1+avg_cost2*num_pairs2)/(num_pairs1+num_pairs2))
                run_summary[2].append(avg_cost)
                run_summary[3].append(PAIRWISE_TIME_PER_TASK+TIME_TO_GENERATE_TASK)
    if GRAPHS:
        if((avg_cost1*num_pairs1+avg_cost2*num_pairs2)/(num_pairs1+num_pairs2) < avg_cost):
            adaptive_better = True
        else:
            adaptive_better = False
        makeCSV(run_summary,trial_number)
        makeJoinCostPlot(run_summary,trial_number, adaptive_better)
    # results, PJF, adapative, PW
    return results_from_join, avg_cost, (avg_cost1*num_pairs1+avg_cost2*num_pairs2)/(num_pairs1+num_pairs2), PAIRWISE_TIME_PER_TASK+TIME_TO_GENERATE_TASK

def generate_PJF(PJF_SELECTIVITY):
    return (15,PJF_SELECTIVITY)

def evaluate(PJF_SELECTIVITY, prejoin, item):
    if(item in evaluated_with_PJF_private):
        return evaluated_with_PJF_private[item]
    else:
        evaluated_with_PJF_private[item] = random()<sqrt(PJF_SELECTIVITY) 
        return evaluated_with_PJF_private[item]


# If the graphs toggle is on this is called in join. Generates a csv of the data of one run as the averages 
# change with time. Trial number is used for naming when saved. Specifically with many runs and csvs.
def makeCSV(data, trial_number):
    ''' Writes a 4 by n 2D list to a CSV file called join_data.csv '''
    download_dir = "join_data" + str(trial_number) + ".csv" #where you want the file to be downloaded to 
    csv = open(download_dir, "w") #"w" indicates that you're writing strings to the file

    columnTitleRow = "Pairs processed, Cost of Adaptive Algorithm, Cost of PJF Join, Cost of PW Join\n"
    csv.write(columnTitleRow)

    for iteration in range(len(data[0])):
        pair = data[0][iteration]
        cost_AA = data[1][iteration]
        cost_PFJ = data[2][iteration]
        cost_PW = data[3][iteration]
        row = str(pair) + "," + str(cost_AA) + "," + str(cost_PFJ) + "," + str(cost_PW) + "\n"
        csv.write(row)

# Called in testing_join_settings(). Creates a csv of information on each of the graphs and the settings they were run at.
def makeCSV_forTrialInfo(data):
    ''' Writes a 7 by n 2D list to a CSV file called join_data.csv '''
    download_dir = "trial_info.csv" #where you want the file to be downloaded to 
    csv = open(download_dir, "w") #"w" indicates that you're writing strings to the file

    columnTitleRow = "Pairs processed, Cost of Adaptive Algorithm, Cost of PJF Join, Cost of PW Join\n"
    csv.write(columnTitleRow)

    for iteration in range(len(data)):
        col0 = data[iteration][0]
        col1 = data[iteration][1]
        col2 = data[iteration][2]
        col3 = data[iteration][3]
        col4 = data[iteration][4]
        col5 = data[iteration][5]
        col6 = data[iteration][6]
        row = str(col0) + "," + str(col1) + "," + str(col2) + "," + str(col3) + "," + str(col4) + "," + str(col5) + "," + str(col6) + "\n"
        csv.write(row)

# Called in testing_join_settings(). Creates a csv of information on each of the graphs and the settings they were run at.
def makeCSV_deep_dive(data):
    ''' Writes a 7 by n 2D list to a CSV file called join_data.csv '''
    download_dir = "deep_dives.csv" #where you want the file to be downloaded to 
    csv = open(download_dir, "w") #"w" indicates that you're writing strings to the file

    columnTitleRow = "Trial No., Join selectivity, PJF selectivity, PW time, PJF time, Size 1, Size 2, PJF Average Cost, PW Average Cost, Adaptive Average Cost\n"
    csv.write(columnTitleRow)

    for iteration in range(len(data)):
        col0 = data[iteration][0]
        col1 = data[iteration][1]
        col2 = data[iteration][2]
        col3 = data[iteration][3]
        col4 = data[iteration][4]
        col5 = data[iteration][5]
        col6 = data[iteration][6]
        col7 = data[iteration][7]
        col8 = data[iteration][8]
        col9 = data[iteration][9]
        row = str(col0) + "," + str(col1) + "," + str(col2) + "," + str(col3) + "," + str(col4) + "," + str(col5) + "," + str(col6) + "," + \
                str(col7) + "," + str(col8) + "," + str(col9) + "\n" 
        csv.write(row)

# Graphs information about the average costs along a run. Saves the graph into the directory, tagging it if the adaptive
# algorithm did better.
def makeJoinCostPlot(data, trial_number, adaptive_better):
    '''Make a plot of 3 lines given a 4 by n 2D list. Used to plot graphs of join costs '''
    ### PLOT COSTS ###
    plt.figure(trial_number)
    plt.plot(data[0], data[1],'r--' ) 
    plt.plot(data[0], data[2], 'b--') 
    plt.plot(data[0], data[3], 'g--') 


    ### ADJUST AXES AND LEGEND ###
    max_y = max( [max(data[1]),max(data[2]),max(data[3])] )
    min_y = min( [min(data[1]),min(data[2]),min(data[3])] )
    plt.ylim(ymin=min_y*0.9,ymax=max_y*1.1) # TODO:need to automate this assignment
    plt.legend(['Adaptive Algorithm Average Cost','PJF Join Average Cost','PW Join Average Cost'])
    plt.xlabel('Pairs Processed')
    plt.ylabel('Cost (time units)')

    adaptive = ""
    if adaptive_better:
        adaptive += "Adaptive-"
        print "adaptive"

    ### DEBUGGING ###
    if DEBUG:
        print "ABOUT GRAPH ---------"
        print "max and min y values: " + str(max_y) + ", " + str(min_y)
        print "---------------------"

    ### SHOW AND SAVE ###
    fig = plt.gcf()
    fig.savefig(adaptive + 'Cost of Various Join algorithms' + str(trial_number) + '.png')


# Alternative to generating graphs. This produces one csv for many trials run in testing_join_settings()
def mass_trial_csv(data, PJF_avg_cost, PW_avg_cost, ad_avg_cost):
    ''' Writes a 11 by n 2D list to a CSV file called join_data.csv '''
    download_dir = "trial_info.csv" #where you want the file to be downloaded to 
    csv = open(download_dir, "w") #"w" indicates that you're writing strings to the file

    if not len(data)==len(PJF_avg_cost):
        print "not same size, all is not good!"
    for iteration in range(len(data)):
        col0 = data[iteration][0]
        col1 = data[iteration][1]
        col2 = data[iteration][2]
        col3 = data[iteration][3]
        col4 = data[iteration][4]
        col5 = data[iteration][5]
        col6 = data[iteration][6]
        col7 = PJF_avg_cost[iteration]
        col8 = PW_avg_cost[iteration]
        col9 = ad_avg_cost[iteration]
        if iteration==0:
            col10 = "Best Algo"
        elif col7<col9:
            col10 = "PJF"
        else:
            col10 = "ADAPT"
        row = str(col0) + "," + str(col1) + "," + str(col2) + "," + str(col3) + "," + str(col4) + "," + str(col5) + "," + \
            str(col6) + "," + str(col7) + "," + str(col8) + "," + str(col9) + "," + str(col10) +"\n"
        csv.write(row)

# Summarizes all the trials that are run at the same settings. Assuming that PJF selectivties to test 
# are all the same and it is only the other settings that are being changed. So it is the same as mass_trial_csv except it
# removes duplicate runs and instead averages the performances of the different algorithms. Also includes the standard deviations 
# of the average costs across a certain setting. 
def summary_csv(data):
    download_dir = "summary_data.csv" #where you want the file to be downloaded to 
    csv = open(download_dir, "w") #"w" indicates that you're writing strings to the file

    columnTitleRow = "Trial Start No., Avg PJF Avg cost, Avg PW Avg Cost, Avg Adapt AVg Cost, PJF STD, PW STD, ADAPT STD\n"
    csv.write(columnTitleRow)

    for iteration in range(len(data)):
        trial = data[iteration][0]
        PJF = np.mean(data[iteration][1])
        PW = np.mean(data[iteration][2])
        ADAPT = np.mean(data[iteration][3])
        PJF_std = np.std(data[iteration][1]) 
        PW_std = np.std(data[iteration][2])
        ADAPT_std = np.std(data[iteration][3])
        row = str(trial) + "," + str(PJF) + "," + str(PW) + "," + str(ADAPT) + "," + str(PJF_std) + "," + str(PW_std) + "," + str(ADAPT_std) +"\n"
        csv.write(row)

# Takes data (summary data produced by the testing join settings function) and filters it by what is statistically significant. 
# Then puts thta data into a heat map whose x axis is the ratio of sizes of the two lists and whose y axis is the ratio of the 
# time costs (of pairwise joins and of the PJF)
def heatmap(data, trial_info):
    significant_data_x, significant_data_y = [],[]
    size_1s = []
    size_2s = []
    for entry in range(len(data)):
        a = data[entry][1] #PJF
        b = data[entry][3] #ADAPT
        t, p = stats.ttest_ind(a,b)
        if np.mean(a) > np.mean(b):
            if p < 0.05:
                ###                     (                size1          ) / (            size 2             )
                significant_data_x += [ float(trial_info[int(data[entry][0])][5]) / float(trial_info[int(data[entry][0])][6])]
                size_1s += [trial_info[int(data[entry][0])][5]]
                size_2s += [trial_info[int(data[entry][0])][6]]
                ##                      (    pairwise time              ) / (   PJF time                    )
                significant_data_y += [ float(trial_info[int(data[entry][0])][3]) / float(trial_info[int(data[entry][0])][4]) ]
    
    heatmap, xedges, yedges = np.histogram2d(significant_data_x, significant_data_y,bins=(10,10))
    extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
 
    # Plot heatmap 
    plt.clf()
    plt.title('Heatmap of significantly different average costs')
    plt.ylabel('y')
    plt.xlabel('x')
    plt.imshow(heatmap, extent=extent, origin='lower', aspect=100)
    
    ### SHOW AND SAVE ###
    fig = plt.gcf()
    fig.savefig('heatmap.png')

# Used to call join many times and save information about performances and settings tested. Returns data that is used in
# summary_csv() and heatmap() and mass_trial_csv() mostly.
def testing_join_settings():
    trial_number_info = [["Trial Number", "Join Selectivity", "PFJ Selectivity", "Pairwise time per task", 
                    "Time to eval PJF", "Size of List 1", "Size of List 2"]]
    trial_number = 1
    all_PJF_costs = ["Avg. Cost of PJF"]
    all_adaptive_costs = ["Avg. Cost of Adaptive"]
    all_PW_costs = ["Avg. Cost of PW"]
    summary_data = [ ]
    for size_2 in size_l2_to_test:
        for size_1 in size_l1_to_test:
            for join_selectivity in join_selectivities_to_test:
                for pairwise_time in pairwise_time_to_test:
                    for eval_PJF_time in time_to_eval_PJF_test:
                        sum_avg_PJF = []
                        sum_avg_PW = []
                        sum_avg_adapt = []
                        trial_number_start = trial_number
                        for PJF_selectivity in PJF_selectivities_to_test:
                            # Keep track of the settings for this trial
                            join_settings = [trial_number, join_selectivity, PJF_selectivity, pairwise_time, eval_PJF_time,size_1,size_2]
                            trial_number_info += [join_settings]
                            # Prep fake data
                            H,M = [],[]
                            for i in range(size_1):
                                H += [i]
                            for i in range(size_2):
                                M += [100+i]
                            # Run join
                            results, PJF_cost, adaptive_cost, PW_cost = join(H,M,join_settings)
                            trial_number += 1
                            # here are the costs that we will save
                            all_PJF_costs += [PJF_cost]
                            all_adaptive_costs += [adaptive_cost]
                            all_PW_costs += [PW_cost]
                            if DEBUG:
                                print 'INSIDE TESTING JOIN SETTINGS -------'
                                print 'JOIN_SELECTIVITY: ' + str(join_selectivity)
                                print 'PJF_SELECTIVITY: ' + str(PJF_selectivity)
                                print 'PAIRWISE_TIME_PER_TASK: ' + str(pairwise_time) 
                                print 'TIME_TO_EVAL_PJF: ' + str(eval_PJF_time)
                                print '-------------------------------------'
                            sum_avg_PJF += [PJF_cost]
                            sum_avg_PW += [PW_cost]
                            sum_avg_adapt += [adaptive_cost]
                        summary_data += [[trial_number_start, sum_avg_PJF, \
                            sum_avg_PW, sum_avg_adapt]]
                        if DEBUG:
                            print "SETTINGS:"
                            print join_selectivity, PJF_selectivity, pairwise_time, eval_PJF_time,size_1,size_2
                            print "AVERAGE PJF COST: " + str(float(sum_avg_PJF)/len(PJF_selectivities_to_test))
                            print "AVERAGE PW COST: " + str(float(sum_avg_PW)/len(PJF_selectivities_to_test))
                            print "AVERAGE ADAPT COST: " + str(float(sum_avg_adapt)/len(PJF_selectivities_to_test))
    return trial_number_info, all_PJF_costs, all_adaptive_costs, all_PW_costs, summary_data

# DEEP DIVE SINGLE TESTS


setting = [2,0.3,0.9,10,100,100,20] 
results = []
for i in range (20):
    # Prep fake data
    H,M = [],[]
    for i in range(setting[5]):
        H += [i]
    for i in range(setting[6]): 
        M += [100+i]
    cur_res, cur_PJF, cur_adapt, cur_PW = join(H,M,setting)
    results += [setting + [cur_PJF,cur_PW,cur_adapt]]
    evaluated_with_PJF_private = { }
makeCSV_deep_dive(results)

# MASS TESTING
# trial_number_info, all_PJF_costs, all_adaptive_costs, all_PW_costs, summary_data = testing_join_settings()
# mass_trial_csv( trial_number_info, all_PJF_costs, all_adaptive_costs, all_PW_costs )
# summary_csv(summary_data)
# heatmap(summary_data , trial_number_info )
