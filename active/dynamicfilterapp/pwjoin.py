import datetime as DT
from math import *
from random import *
import numpy


#### GLOBAL VARIABLES ####
    #Settings
TIME_TO_GENERATE_TASK = 15.0
BASE_FIND_MATCHES = 60.0     #Basic requirement to find some matches
FIND_SINGLE_MATCH_TIME = 5.0 #cost per match found
AVG_MATCHES = 15.0 #average matches per item
STDDEV_MATCHES = 3 #standard deviation of matches
    #Estimates
PJF_selectivity_est = 0.5
join_selectivity_est = 0.5
PJF_cost_est = 0.0
join_cost_est = 0.0
PW_cost_est = 0.0
    #Results
results_from_pjf_join = []
results_from_pw_join = []
evaluated_with_PJF = { }
evaluated_with_smallP = {}
processed_by_pw = 0

#toggles
DEBUG_FLAG = True



#join by items
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
    return results_from_join

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


H = ["a","b","c","d","e"]
print PW_join(H)