import datetime as DT
from math import *
from random import *

# GLOBAL VARIABLES
JOIN_SELECTIVITY = 0.1
PJF_SELECTIVITY = 0.3
PAIRWISE_TIME_PER_TASK = 40.0
TIME_TO_GENERATE_TASK = 10.0
TIME_TO_EVAL_PJF = 100.0

# OTHER NECESSARY VARIABLES TODO: Decide if these go in main or remain global
evaluated_with_PJF = { }

DEBUG = True

# TODO: 
def join(i, j):
    """ Assuming that we have two items of a join tuple that need to be evaluated, 
    this function mimicks human join with predetermined costs and selectivity specified.
    This retruns information about selectivity and cost."""

    #### INITIALIZE VARIABLES TO USE ####
    cost_of_PJF, PJF = generate_PJF() # TODO: what are we going to do with the cost_of_PJF?
    avg_cost = 0
    num_pairs = 0
    num_pairs_processed = 0
    results_from_join = [ ]

    #### INFORMATION WE WILL RETURN LATER ####
    PJF_cost = 0
    PJF_select = 0
    join_cost = 0
    join_select = 0

    #### CONTROL GROUP: COMPLETELY USING PJF THEN PW JOIN ####
    timer_val = 0
    if(not i in evaluated_with_PJF):
        # save results of PJF to avoid repeated work
        evaluated_with_PJF[i],PJF_cost = evaluate(PJF,i)
        timer_val += TIME_TO_EVAL_PJF
    if (not j in evaluated_with_PJF):
        # save results of PJF to avoid repeated work
        evaluated_with_PJF[j],PJF_additional_cost = evaluate(PJF,j)
        PJF_cost += PJF_additional_cost
        timer_val += TIME_TO_EVAL_PJF
    if(evaluated_with_PJF[i] and evaluated_with_PJF[j]):
        # Generate task of current pair
        join_cost = TIME_TO_GENERATE_TASK
        timer_val += TIME_TO_GENERATE_TASK
        # Choose whether to add to results_from_join
        join_cost += PAIRWISE_TIME_PER_TASK
        timer_val += PAIRWISE_TIME_PER_TASK
    if(random() < JOIN_SELECTIVITY):
            results_from_join.append([i,j])
    avg_cost=(avg_cost*num_pairs+ timer_val)/(num_pairs+1)
    num_pairs += 1

    #### DEBUGGING ####
    if DEBUG:
        num_pairs_processed +=1
        print "After pair " + str(num_pairs_processed) + " has been processed..."
        print "AVERAGE COST = " + str(avg_cost) + " WHEN SENT [ "+str(num_pairs)+" ] PAIRS"
        print "AVERAGE COST WITHOUT PJF = " + str(PAIRWISE_TIME_PER_TASK+TIME_TO_GENERATE_TASK)
        print "PJF DICTIONARY = " + str(evaluated_with_PJF)

    return results_from_join, PJF_cost, PJF_select, join_cost, join_select

def generate_PJF():
    return (15,PJF_SELECTIVITY)

def evaluate(prejoin, item):
    return random()<sqrt(PJF_SELECTIVITY),TIME_TO_EVAL_PJF
