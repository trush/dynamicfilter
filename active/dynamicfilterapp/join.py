import datetime as DT
from math import *
from random import *

#########################
## GLOBAL VARIABLES #####
#########################

## INPUTS ########################################

list1 = []
list2 = []

## Settings #######################################

JOIN_SELECTIVITY = 0.1
TIME_TO_GENERATE_TASK = 10.0

    ## PJFjoin in particular
PJF_SELECTIVITY = 0.3
PAIRWISE_TIME_PER_TASK = 40.0 # TODO: RENAME
TIME_TO_EVAL_PJF = 100.0

    ## PWJoin in particular
BASE_FIND_MATCHES = 60.0     #Basic requirement to find some matches
FIND_SINGLE_MATCH_TIME = 5.0 #cost per match found
AVG_MATCHES = 15.0 #average matches per item
STDDEV_MATCHES = 3 #standard deviation of matches

    ## small predicate in particular
SMALL_P_SELECTIVITY = 0.5
TIME_TO_EVAL_SMALL_P = 30.0


## Estimates ######################################

PJF_selectivity_est = 0.5
join_selectivity_est = 0.5
PJF_cost_est = 0.0
join_cost_est = 0.0
PW_cost_est = 0.0
small_p_cost_est = 0.0
small_p_selectivity_est = 0.0

## Results ########################################

results_from_pjf_join = []
results_from_pw_join = [] # TODO: why did we want these seperate again?
evaluated_with_PJF = { }
evaluated_with_smallP = []
processed_by_pw = 0
processed_by_PJF = 0
processed_by_smallP = 0

## Other Variables ################################

has_2nd_list = False
total_num_ips_processed = 0
enumerator_est = False # TODO: read more about this and use in our code

## TOGGLES ########################################
DEBUG = True

# TODO: 

#########################
## PJF Join         #####
######################### 

def PJF_join(i, j):
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
        processed_by_PJF += 1 # TODO: check that these are correct for what we are trying to record
        # if the item evaluated True for the PFJ then adjust selectivity
        PJF_selectivity_est = (PJF_selectivity_est*(processed_by_PJF-1)+evaluated_with_PJF[i])/processed_by_PJF
        # adjust our cost estimates for evaluating PJF
        PJF_cost_est = (PJF_cost_est*len(evaluated_with_PJF-1)+PJF_cost)/processed_by_PJF
        timer_val += TIME_TO_EVAL_PJF

    if (not j in evaluated_with_PJF):
        # save results of PJF to avoid repeated work
        evaluated_with_PJF[j],PJF_cost = evaluate(PJF,j)
        processed_by_PJF += 1 # TODO: check that these are correct for what we are trying to record
        # if the item evaluated True for the PFJ then adjust selectivity
        PJF_selectivity_est = (PJF_selectivity_est*(processed_by_PJF-1)+evaluated_with_PJF[j])/processed_by_PJF
        # adjust our cost estimates for evaluating PJF
        PJF_cost_est = (PJF_cost_est*len(evaluated_with_PJF-1)+PJF_cost)/processed_by_PJF
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

#########################
## PJF Join Helpers #####
#########################
def generate_PJF():
    """ Generates the PJF, returns the cost of finding the PJF and selectivity fo the PJF"""
    return (15,PJF_SELECTIVITY)

def evaluate(prejoin, item):
    """ Evaluates the PJF and returns whether it evaluate to true and how long it took to evluate it"""
    return random()<sqrt(PJF_SELECTIVITY),TIME_TO_EVAL_PJF

#########################
## PW Join          #####
#########################

def PW_join(i, itemlist):
    '''Creates a join by taking one item at a time and finding matches
    with input from the crowd '''
    
    #Metadata/debug information
    avg_cost = 0
    num_items = 0

    timer_val = 0
    # Generate task with item
    timer_val += TIME_TO_GENERATE_TASK
    #Get results of that task
    matches, timer_val = get_matches(i, timer_val)
    timer_val += BASE_FIND_MATCHES
    #recalculate average cost
    PW_cost_est = (PW_cost_est*processed_by_pw + timer_val)/(processed_by_pw+1)
    processed_by_pw += 1
    #Append matches to results_from_join
    results_from_pw_join += matches
    #remove processed item from itemlist
    itemlist.remove(i)
    if DEBUG_FLAG:
        print "PW AVERAGE COST: " + str(PW_cost_est)
        print "PW TOTAL COST: " + str(PW_cost_est*processed_by_pw)
    results_from_pw_join += results_from_join
    results_from_pjf_join += results_from_join

#########################
## PW Join Helpers  #####
#########################

def get_matches(item, timer):
    '''gets matches for an item, eventually from the crowd, currently random'''
    #assumes a normal distribution
    num_matches = int(round(numpy.random.normal(AVG_MATCHES, STDDEV_MATCHES, None)))
    matches = []
    #add num_matches pairs
    for i in range(num_matches):
        matches.append((item, i))
        timer += FIND_SINGLE_MATCH_TIME
    return matches, timer

#########################
## Main Join        #####
#########################

def main_join(predicate, item):
    """ This is the main join function. It calls PW_join(), PJF_join(), and small_pred(). Uses 
    cost estimates to determine which function to call item by item."""
    
    if not has_2nd_list:
        if enumerator_est:
            has_2nd_list = True
    
    else:
        if total_num_ips_processed < 0.15*len(list1)*len(list2): # TODO: think more about this metric
             if random(0,1) < 0.5:
                 costs = find_costs()
                 if cost[0] < cost[1]:
                    eval_results = small_pred(item) # TODO: adjust cost and make it item from 2nd list!!
                    PJF_join()
        # TODO: finish main


#########################
## Main Join Helpers ####
#########################

def find_costs():
    """ Finds the cost of the quickest path and returns the path number associated with that 
    path. Path 1 = PJF w/ small predicate applied early. Path 2 = PJF w/ small predicate
    applied later. Path 3 = PW on list 2. Path 4 = PW on list 1."""
    # COST 1 CALCULATION - equation explained in written work TODO: explain eq
    cost_1 = small_p_cost_est*len(list2) + \
            PJF_cost_est*(small_p_selectivity_est *(len(list2)-len(evaluated_with_smallP))+(len(list1))) + \
            join_cost_est*len(list2)*len(list1)*small_p_selectivity_est*PJF_selectivity_est
    # COST 2 CALCULATION - equation explained in written work TODO: explain eq
    cost_2 = PJF_cost_est*(len(list2)+len(list1)) + \
            join_cost_est*len(list2)*len(list1)*PJF_selectivity_est+ \
            small_p_cost_est*join_selectivity_est*len(list1)*len(list2)
    # COST 3 CALCULATION - equation explained in written work TODO: explain eq
    cost_3 = PW_cost_est*len(list2) + \
            join_selectivity_est*len(list1)*len(list2)*small_p_cost_est
    # COST 4 CALCULATION - equation explained in written work TODO: explain eq
    cost_4 = PW_cost_est*len(list1)+ \
            small_p_cost_est*join_selectivity_est*len(list1)*len(list2)

    #### DEBUGGING ####
    if DEBUG:
        print "FIND COSTS -----------------"
        print "COST 1 = " + str(cost_1)
        print "COST 2 = " + str(cost_2)
        print "COST 3 = " + str(cost_3)
        print "COST 4 = " + str(cost_4)
        print "----------------------------"

    return [cost_1, cost_2, cost_3, cost_4]


###param item: the item to be evaluated
##return val whether the item evaluates to true, the cost of this run of small_pred
def small_pred(item):
    """ Evaluates the small predicate, adding the results of that into a global dictionary. 
    Also adjusts the global estimates for the cost and selectivity of the small predicate."""
    #first, check if we've already evaluated this item as true
    if item in evaluated_with_smallP:
        return True
    #if not, evaluate it with the small predicate
    else:
        #increment the number of items 
        processed_by_smallP += 1
        # Update the cost
        small_p_cost_est = (small_p_cost_est*(processed_by_smallP-1)+TIME_TO_EVAL_SMALL_P)/processed_by_smallP
        #for preliminary testing, we randomly choose whether or not an item passes
        eval_results = random() < SMALL_P_SELECTIVITY
        # Update the selectivity
        small_p_selectivity_est = (small_p_selectivity_est*(processed_by_smallP-1)+eval_results)/processed_by_smallP
        #if the item does not pass, we remove it from the list entirely
        if not eval_results:
            list2.remove(item)
        #if the item does pass, we add it to the list of things already evaluated
        else:
            evaluated_with_smallP.append[item]
        return eval_results
    