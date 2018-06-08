import datetime as DT
from math import *
from random import *

#### GLOBAL VARIABLES ####
    #Settings
JOIN_SELECTIVITY = 0.1
PJF_SELECTIVITY = 0.3
PAIRWISE_TIME_PER_TASK = 40.0
TIME_TO_GENERATE_TASK = 10.0
TIME_TO_EVAL_PJF = 100.0
    #Estimates
PJF_selectivity_est = 0.5
join_selectivity_est = 0.5
PJF_cost_est = 0.0
join_cost_est = 0.0
    #Results
results_from_join = []
evaluated_with_PJF = { }
evaluated_with_smallP = {}

DEBUG = True

# TODO: 
def join(i, j):
    """ Assuming that we have two items of a join tuple that need to be evaluated, 
    this function mimicks human join with predetermined costs and selectivity specified.
    This retruns information about selectivity and cost."""

    #### INITIALIZE VARIABLES TO USE ####
    cost_of_PJF, PJF = generate_PJF() # TODO: what are we going to do with the cost_of_PJF? Move somewhere else?

    #### CONTROL GROUP: COMPLETELY USING PJF THEN PW JOIN ####
    timer_val = 0
    if(not i in evaluated_with_PJF):
        # save results of PJF to avoid repeated work
        evaluated_with_PJF[i],PJF_cost = evaluate(PJF,i)
        # if the item evaluated True for the PFJ then adjust selectivity
        PJF_selectivity_est = (PJF_selectivity_est*(len(evaluated_with_PJF)-1)+evaluated_with_PJF[i])/len(evaluated_with_PJF)
        # adjust our cost estimates for evaluating PJF
        PJF_cost_est = (PJF_cost_est*len(evaluated_with_PJF-1)+PJF_cost)/len(evaluated_with_PJF)
        timer_val += TIME_TO_EVAL_PJF

    if (not j in evaluated_with_PJF):
        # save results of PJF to avoid repeated work
        evaluated_with_PJF[j],PJF_cost = evaluate(PJF,j)
        # if the item evaluated True for the PFJ then adjust selectivity
        PJF_selectivity_est = (PJF_selectivity_est*(len(evaluated_with_PJF)-1)+evaluated_with_PJF[j])/len(evaluated_with_PJF)
        # adjust our cost estimates for evaluating PJF
        PJF_cost_est = (PJF_cost_est*len(evaluated_with_PJF-1)+PJF_cost)/len(evaluated_with_PJF)
        timer_val += TIME_TO_EVAL_PJF

    if(evaluated_with_PJF[i] and evaluated_with_PJF[j]):
        # Generate task of current pair
        timer_val += TIME_TO_GENERATE_TASK
        # Choose whether to add to results_from_join
        timer_val += PAIRWISE_TIME_PER_TASK
        # Adjust join cost with these two time costs
        join_cost_est = (join_cost_est*len(results_from_join)+TIME_TO_GENERATE_TASK+PAIRWISE_TIME_PER_TASK)/(len(results_from_join)+1)

    #### DEBUGGING ####
    if DEBUG:
        num_pairs_processed +=1
        print "After pair " + str(num_pairs_processed) + " has been processed..."
        print "AVERAGE COST = " + str(avg_cost) + " WHEN SENT [ "+str(num_pairs)+" ] PAIRS"
        print "AVERAGE COST WITHOUT PJF = " + str(PAIRWISE_TIME_PER_TASK+TIME_TO_GENERATE_TASK)
        print "PJF DICTIONARY = " + str(evaluated_with_PJF)

    if(random() < JOIN_SELECTIVITY):
            return [i,j], PJF_cost, PJF_select, join_cost, join_select
    else:
            return [], PJF_cost, PJF_select, join_cost, join_select


def generate_PJF():
    return (15,PJF_SELECTIVITY)

def evaluate(prejoin, item):
    return random()<sqrt(PJF_SELECTIVITY),TIME_TO_EVAL_PJF
