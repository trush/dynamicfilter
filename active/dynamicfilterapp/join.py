import datetime as DT
from math import *
from random import *

JOIN_SELECTIVITY = 0.1
PJF_SELECTIVITY = 0.3
PAIRWISE_TIME_PER_TASK = 40.0
TIME_TO_GENERATE_TASK = 10.0
TIME_TO_EVAL_PJF = 100.0

# Temporary for testing
SIZE_L1 = 26
SIZE_L2 = 26

DEBUG = True

# TODO: 
def join(H, M):
    """ Assuming that we have two complete lists that need to b joined, mimicks human join
    with predetermined average cost per HIT """

    SIZE_L1 = len(H)
    SIZE_L2 = len(M)

    #### INITIALIZE VARIABLES TO USE ####
    cost_of_PJF, PJF = generate_PJF() # TODO: what are we going to do with the cost_of_PJF?
    avg_cost = 0
    num_pairs = 0
    num_pairs_processed = 0
    results_from_join = [ ]
    evaluated_with_PJF = { }
    

    #### SEND OUT JOIN TUPLES ####
    for i in H:
        for j in M:
            current_pair = [i, j] 

            #### CONTROL GROUP: COMPLETELY USING PJF THEN PW JOIN ####
            timer_val = 0
            if(not i in evaluated_with_PJF):
                # save results of PJF to avoid repeated work
                evaluated_with_PJF[i] = evaluate(PJF,i)
                timer_val += TIME_TO_EVAL_PJF
            if (not j in evaluated_with_PJF):
                # save results of PJF to avoid repeated work
                evaluated_with_PJF[j] = evaluate(PJF,j)
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

            #### DEBUGGING ####
            if DEBUG:
                num_pairs_processed +=1
                print "After pair " + str(num_pairs_processed) + " has been processed..."
                print "AVERAGE COST = " + str(avg_cost) + " WHEN SENT [ "+str(num_pairs)+" ] PAIRS"
                print "AVERAGE COST WITHOUT PJF = " + str(PAIRWISE_TIME_PER_TASK+TIME_TO_GENERATE_TASK)
                print "PJF DICTIONARY = " + str(evaluated_with_PJF)
    return results_from_join

def generate_PJF():
    return (15,PJF_SELECTIVITY)

def evaluate(prejoin, item):
    return random()<sqrt(PJF_SELECTIVITY)


# temporary for testing 
H,M = [],[]
for i in range(SIZE_L1):
    H += [i]
for i in range(SIZE_L2):
    M += [100+i]
print join(H,M)