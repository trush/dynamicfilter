import datetime as DT
import sys
now = DT.datetime.now()
from responseTimeDistribution import *

RUN_NAME = 'Scaling_Investigation' + "_" + str(now.date())+ "_" + str(now.time())[:-7]
ITEM_TYPE = "Hotel"

INPUT_PATH = 'dynamicfilterapp/simulation_files/hotels/'
OUTPUT_PATH = 'dynamicfilterapp/simulation_files/output/'
IP_PAIR_DATA_FILE = 'hotel_cleaned_data.csv'
TRUE_TIMES, FALSE_TIMES = importResponseTimes(INPUT_PATH + IP_PAIR_DATA_FILE)
REAL_DISTRIBUTION_FILE = 'workerDist.csv'
## Turns on useful print statements
DEBUG_FLAG = True # useful print statements turned on

REAL_DATA = False #if set to false, will use synthetic data (edit in syndata file)
#_________________ CONFIGURING CONSENSUS _____________________#

## Maximum acceptable probability area
UNCERTAINTY_THRESHOLD = 0.1
## Used for ALMOST_FALSE \todo better docs
FALSE_THRESHOLD = 0.05
## Upper bound of integration for beta distribution
DECISION_THRESHOLD = 0.5
## Number of votes to gather, no matter the results, before evaluating consensus
NUM_CERTAIN_VOTES = 5
## Maximum number of votes to ask for before using Majority Vote as backup metric
CUT_OFF = 21
## Number of votes for a single result (Y/N) before calling that the winner
SINGLE_VOTE_CUTOFF = int(1+math.ceil(CUT_OFF/2.0))


#________________ CONFIGURING THE ALGORITHM ___________________#

## The number of unique worker (IDs) that a simulation can pick from
NUM_WORKERS = 5000
## Tells pick_worker() how to choose workers
# 0  -  Uniform Distribution; (all worker equally likely)
# 1  -  Geometric Distribution; (synthetic graph which fits out data well)
# 2  -  Real Distribution (samples directly from the real data)
DISTRIBUTION_TYPE = 0 # tells pick_worker how to choose workers.

## Determines which algorithm we're actually using to pick IP Pairs
# 1 - queue pending system (uses PENDING_QUEUE_SIZE parameter)
# 2 - random system
# 3 - controlled system (uses CHOSEN_PREDS parameter)
EDDY_SYS = 1

## The size of the "queue" for each predicate. This can be made dynamic if desired.
# For toggles.EDDY_SYS = 5, this is the \a minimum number of unique IP Pairs to be in progress at any given time for a predicate. For toggles.EDDY_SYS = 1,
# this is a \a maximum number of IP Pairs in progress for each predicate.
PENDING_QUEUE_SIZE = 2

CHOSEN_PREDS = [3,4]

ITEM_SYS = 0
# ITEM SYS KEY:
# 0 - randomly choose an item
# 1 - item-started system
# 2 - item-almost-false system

SLIDING_WINDOW = False
LIFETIME = 40

ADAPTIVE_QUEUE = True # should we try and increase the que length for good predicates
ADAPTIVE_QUEUE_MODE = 0
# 0 - only increase ql if reached that number of tickets
# 1 - increase like (0) but also decreases if a pred drops below the limit
QUEUE_LENGTH_ARRAY = [(0,1),(4,2),(8,3), (16,4)] # settings for above mode [(#tickets,qlength)]

#############################################################################
#############################################################################


###################### CONFIGURING TESTING ##################################
#############################################################################




DUMMY_TASKS = True # will distribute a placeholder task when "worker has no tasks
                   # to do" and will track the number of times this happens
DUMMY_TASK_OPTION = 0
# 0 gives a complete placeholder task

GEN_GRAPHS = True # if true, any tests run will generate their respective graphs automatically

#################### TESTING OPTIONS FOR SYNTHETIC DATA ############################
NUM_QUESTIONS = 4
NUM_ITEMS = 400
SIN = -1

SELECTIVITY_GRAPH = False

# SIN tuple is of the form (SIN, amp, period, samplingFrac, trans). If trans is 0, it starts at the
# selectvity of the previous timestep
# tuples of form (task number, (select,amb), (select,amb))
switch_list = [ (0, (0.9, 0.75), (0.7, 0.75), (0.5, 0.75), (0.4, 0.75)) ]
#################### TESTING OPTIONS FOR REAL DATA ############################
RUN_DATA_STATS = False

RESPONSE_SAMPLING_REPLACEMENT = False # decides if we should sample our response data with or without replacement

RUN_ABSTRACT_SIM = False

ABSTRACT_VARIABLE = "UNCERTAINTY_THRESHOLD"
ABSTRACT_VALUES = [.1, .2, .3]

#produces ticket count graph for 1 simulation
COUNT_TICKETS = True
TRACK_QUEUES = True

RUN_AVERAGE_COST = False
COST_SAMPLES = 100

RUN_SINGLE_PAIR = False
SINGLE_PAIR_RUNS = 50

RUN_ITEM_ROUTING = False # runs a single test with two predicates, for a 2D graph showing which predicates were priotatized

RUN_MULTI_ROUTING = False # runs NUM_SIM simulations and averges the number of "first items" given to each predicate, can auto gen a bar graph

RUN_OPTIMAL_SIM = False # runs NUM_SIM simulations where IP pairs are completed in an optimal order. ignores worker rules

################### OPTIONS FOR REAL OR SYNTHETIC DATA ########################
NUM_SIM = 10 # how many simulations to run?


TIME_SIMS = False # track the computer runtime of simulations

SIMULATE_TIME = True # simulate time passing/concurrency
ACTIVE_TASKS_SIZE = 25 # maximum number of active tasks in a simulation with time

BUFFER_TIME = 5 # amount of time steps between task selection and task starting
MAX_TASKS_OUT = 10
MAX_TASKS_COLLECTED = CUT_OFF

RUN_TASKS_COUNT = False # actually simulate handing tasks to workers

TRACK_IP_PAIRS_DONE = False

TRACK_ACTIVE_TASKS = True

TRACK_PLACEHOLDERS = True # keeps track of the number of times the next worker has no possible task

## WILL ONLY RUN IF RUN_TASKS_COUNT IS TRUE ##
TEST_ACCURACY = False
ACCURACY_COUNT = False

OUTPUT_SELECTIVITIES = False

RUN_CONSENSUS_COUNT = False # keeps track of the number of tasks needed before consensus for each IP

CONSENSUS_LOCATION_STATS = False

VOTE_GRID = False #draws "Vote Grids" from many sims. Need RUN_CONSENSUS_COUNT on. works w/ accuracy

IDEAL_GRID = False #draws the vote grid rules for our consensus metric

## WILL ONLY RUN IF RUN_TASKS_COUNT IS TRUE ##
OUTPUT_COST = False

PACKING=True # Enable for "Packing" of outputs into a folder and generation of config.ini

if GEN_GRAPHS:
    print ''
    reply = raw_input("GEN_GRAPHS is turned on. Do you actually want graphs? Enter y for yes, n for no (turns off graphs), or c to cancel. ")
    if reply == "c":
        raise Exception ("Change your setup and try again!")
    elif reply == "n":
        print "~~~~~~ Graphing turned off ~~~~~~"
        GEN_GRAPHS = False

# List of toggles for debug printing and Config.ini generation
            ##### PLEASE UPDATE AS NEW TOGGLES ADDED #####
VARLIST =  ['RUN_NAME','ITEM_TYPE','INPUT_PATH','OUTPUT_PATH','IP_PAIR_DATA_FILE',
            'REAL_DISTRIBUTION_FILE','DEBUG_FLAG',
            'NUM_CERTAIN_VOTES','UNCERTAINTY_THRESHOLD','FALSE_THRESHOLD','DECISION_THRESHOLD',
            'CUT_OFF','NUM_WORKERS','DISTRIBUTION_TYPE','EDDY_SYS','PENDING_QUEUE_SIZE',
            'CHOSEN_PREDS','ITEM_SYS','SLIDING_WINDOW','LIFETIME','ADAPTIVE_QUEUE',
            'ADAPTIVE_QUEUE_MODE','QUEUE_LENGTH_ARRAY','REAL_DATA', 'switch_list',
            'DUMMY_TASKS', 'DUMMY_TASK_OPTION','GEN_GRAPHS',
            'RUN_DATA_STATS','RESPONSE_SAMPLING_REPLACEMENT','RUN_ABSTRACT_SIM',
            'ABSTRACT_VARIABLE','ABSTRACT_VALUES','COUNT_TICKETS','RUN_AVERAGE_COST',
            'COST_SAMPLES','RUN_SINGLE_PAIR','SINGLE_PAIR_RUNS','RUN_ITEM_ROUTING',
            'RUN_MULTI_ROUTING','RUN_OPTIMAL_SIM','NUM_SIM','TIME_SIMS','SIMULATE_TIME',
            'ACTIVE_TASKS_SIZE', "MAX_TASKS_COLLECTED", "MAX_TASKS_OUT", 'BUFFER_TIME','RUN_TASKS_COUNT','TRACK_IP_PAIRS_DONE',
            'TRACK_PLACEHOLDERS','TEST_ACCURACY','OUTPUT_SELECTIVITIES',
            'RUN_CONSENSUS_COUNT','VOTE_GRID','OUTPUT_COST', 'TRACK_ACTIVE_TASKS', 'TRACK_QUEUES'
]
