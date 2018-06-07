import datetime as DT
from math import *
from random import *
import csv
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import numpy as np

#toggles
DEBUG = False
GRAPHS = True

# Only used for mass testing
join_selectivities_to_test = [0.3,0.6,0.9]
PJF_selectivities_to_test =  [0.3,0.6,0.9]
pairwise_time_to_test = [10.0,20.0,40.0]
time_to_eval_PJF_test = [10.0,20.0,40.0]
size_l1_to_test = [5,20,50]
size_l2_to_test = [5,20,50]

def join(H, M, join_settings):
    """ Assuming that we have two complete lists that need to b joined, mimicks human join
    with predetermined average cost per HIT """

    #### JOIN SETTINGS ####
    trial_number           = join_settings[0]
    JOIN_SELECTIVITY       = join_settings[1]
    PJF_SELECTIVITY        = join_settings[2]
    PAIRWISE_TIME_PER_TASK = join_settings[3]
    TIME_TO_GENERATE_TASK  = 10.0
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
        makeCSV(run_summary,trial_number)
        makeJoinCostPlot(run_summary,trial_number)
    return results_from_join

def generate_PJF(PJF_SELECTIVITY):
    return (15,PJF_SELECTIVITY)

def evaluate(PJF_SELECTIVITY, prejoin, item):
    return random()<sqrt(PJF_SELECTIVITY)

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

def makeJoinCostPlot(data, trial_number):
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

    ### DEBUGGING ###
    if DEBUG:
        print "ABOUT GRAPH ---------"
        print "max and min y values: " + str(max_y) + ", " + str(min_y)
        print "---------------------"

    ### SHOW AND SAVE ###
    fig = plt.gcf()
    fig.savefig('Cost of Various Join algorithms' + str(trial_number) + '.png')

def testing_join_settings():
    trial_number_info = [["Trial Number", "Join Selectivity", "PFJ Selectivity", "Pairwise time per task", 
                    "Time to eval PJF", "Size of List 1", "Size of List 2"]]
    trial_number = 1
    for join_selectivity in join_selectivities_to_test:
        for PJF_selectivity in PJF_selectivities_to_test:
            for pairwise_time in pairwise_time_to_test:
                for eval_PJF_time in time_to_eval_PJF_test:
                    for size_1 in size_l1_to_test:
                        for size_2 in size_l2_to_test:
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
                            join(H,M,join_settings)
                            trial_number += 1

                            if DEBUG:
                                print 'INSIDE TESTING JOIN SETTINGS -------'
                                print 'JOIN_SELECTIVITY: ' + str(join_selectivity)
                                print 'PJF_SELECTIVITY: ' + str(PJF_selectivity)
                                print 'PAIRWISE_TIME_PER_TASK: ' + str(pairwise_time) 
                                print 'TIME_TO_EVAL_PJF: ' + str(eval_PJF_time)
                                print '-------------------------------------'
    return trial_number_info

makeCSV_forTrialInfo( testing_join_settings() )