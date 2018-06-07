import datetime as DT
from math import *
from random import *
import numpy

#toggles
DEBUG_FLAG = True

#join settings
TIME_TO_GENERATE_TASK = 15.0
BASE_FIND_MATCHES = 60.0     #Basic requirement to find some matches
FIND_SINGLE_MATCH_TIME = 5.0 #cost per match found
AVG_MATCHES = 15.0 #average matches per item
STDDEV_MATCHES = 3 #standard deviation of matches


#join by items
def PW_join(H):
    '''Creates a join by taking one item at a time and finding matches
    with input from the crowd '''
    
    #Metadata/debug information
    avg_cost = 0
    num_items = 0

    results_from_join = []

    for i in H:
        timer_val = 0
        # Generate task with item
        timer_val += TIME_TO_GENERATE_TASK
        #Get results of that task
        matches, timer_val = get_matches(i, timer_val)
        timer_val += BASE_FIND_MATCHES
        #Append matches to results_from_join
        results_from_join += matches
        if DEBUG_FLAG:
            avg_cost = (avg_cost*num_items + timer_val)/(num_items+1)
            num_items += 1
    if DEBUG_FLAG:
        print "AVERAGE COST: " + str(avg_cost)
        print "TOTAL COST: " + str(avg_cost*num_items)
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