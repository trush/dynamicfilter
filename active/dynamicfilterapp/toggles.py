import datetime as DT
import sys
now = DT.datetime.now()
from responseTimeDistribution import *

RUN_NAME = 'abstract_sim_EDDY_SYS_test' + "_" + str(now.date())+ "_" + str(now.time())[:-7]

ITEM_TYPE = "Hotel"
INPUT_PATH = 'dynamicfilterapp/simulation_files/hotels/'
OUTPUT_PATH = 'dynamicfilterapp/simulation_files/output/'
IP_PAIR_DATA_FILE = 'hotel_cleaned_data.csv'
TRUE_TIMES, FALSE_TIMES = importResponseTimes(INPUT_PATH + IP_PAIR_DATA_FILE)
REAL_DISTRIBUTION_FILE = 'workerDist.csv'

DEBUG_FLAG = True # useful print statements turned on

####################### CONFIGURING CONSENSUS ##############################

UNCERTAINTY_THRESHOLD = 0.1    # maximum acceptable proability area
FALSE_THRESHOLD = 0.05           # Used for ALMOST_FALSE TODO better docs
DECISION_THRESHOLD = 0.5        # Upper bound of integration
NUM_CERTAIN_VOTES = 5           # number of votes to gather no matter the results
CUT_OFF = 21                    # Maximum number of votes to ask for before using Majority Vote as backup metric
SINGLE_VOTE_CUTOFF = int(1+math.ceil(CUT_OFF/2.0))    # Number of votes for a single result (Y/N) before calling that the winner
# Our consensus metric is Complicated. For each IP pair chosen, we do the following
# We gather (NUM_CERTAIN_VOTES) votes on the chosen IP pair
# To take "consensus" we generate a beta distribution from the number of (y/n) votes
#   then intigrate over it from zero to (DECISION_THRESHOLD)
#   if the probability area is less than (UNCERTAINTY_THRESHOLD) then we have consensus
#   else we gather more votes
# This is repeated until one of sevreal conditions is met
#   1 - We reach consensus (naturally)
#   2 - The total number of gathered votes is equal to (CUT_OFF)
#   3 - The number of either (yes)s or (no)s on their own is equal to (SINGLE_VOTE_CUTOFF)
# If either cond. (2|3) we take a simple majority vote


################ CONFIGURING THE ALGORITHM ##################################
#############################################################################
NUM_WORKERS = 301
DISTRIBUTION_TYPE = 0 # tells pick_worker how to choose workers.
# 0  -  Uniform Distribution; (all worker equally likely)
# 1  -  Geometric Distribution; (synthetic graph which fits out data well)
# 2  -  Real Distribution (samples directly from the real data)

EDDY_SYS = 6
# EDDY SYS KEY:
# 1 - queue pending system (uses PENDING_QUEUE_SIZE parameter)
# 2 - random system
# 3 - controlled system (uses CHOSEN_PREDS parameter)
# 4 - epsilon-greedy MAB
# 5 - annealing-epsilon-greedy MAB

PENDING_QUEUE_SIZE = 4

CHOSEN_PREDS = [4,2] # predicates that will be used when run on real data
# If using EDDY_SYS 3 (controlled system), CHOSEN_PREDS should be a
# list of 2 predicates (for now). They will be passed items in the order
# they appear in the list.

# HOTEL PREDICATE INDEX
# 0 - not selective and not ambiguous
# 1 - selective and not ambiguous
# 2 - not selective and medium ambiguity
# 3 - medium selectivity and ambiguous
# 4 - not selective and not ambiguous

# RESTAURANT PREDICATE INDEX
# 1,5,4 - three most selective
# 4,5,8 - least ambiguous questions
# 0,2,9 - most ambiguous questions
# 8,2,3 - least selective

ITEM_SYS = 0
# ITEM SYS KEY:
# 0 - randomly choose an item
# 1 - item-started system
# 2 - item-almost-false system

SLIDING_WINDOW = False
LIFETIME = 20

ADAPTIVE_QUEUE = False # should we try and increase the que length for good predicates
ADAPTIVE_QUEUE_MODE = 0
# 0 - only increase ql if reached that number of tickets
# 1 - increase like (0) but also decreases if a pred drops below the limit
QUEUE_LENGTH_ARRAY = [(0,1),(4,2),(8,3)] # settings for above mode [(#tickets,qlength)]

#############################################################################
#############################################################################


###################### CONFIGURING TESTING ##################################
#############################################################################

REAL_DATA = False #if set to false, will use synthetic data (edit in syndata file)


DUMMY_TASKS = True # will distribute a placeholder task when "worker has no tasks
                   # to do" and will track the number of times this happens
DUMMY_TASK_OPTION = 0
# 0 gives a complete placeholder task

GEN_GRAPHS = True # if true, any tests run will generate their respective graphs automatically

#################### TESTING OPTIONS FOR SYNTHETIC DATA ############################
NUM_QUESTIONS = 2
NUM_ITEMS = 150
SIN = -1

SELECTIVITY_GRAPH = False

# SIN tuple is of the form (SIN, amp, period, samplingFrac, trans). If trans is 0, it starts at the 
# selectvity of the previous timestep
#switch_list = [(0, (0.6, 0.68), (0.6, 0.87)), (100, ((SIN, .2, 100, .1, 0), 0.68), (0.6, 0.87))]
 #(time,(selectivity,ambiguity), (...))
switch_list = [(0, (0.9, 1.0), (0.2, 1.0))]#, (800, (0.3, 0.3), (0.8, 0.3))]

#################### TESTING OPTIONS FOR REAL DATA ############################
RUN_DATA_STATS = False

RESPONSE_SAMPLING_REPLACEMENT = False # decides if we should sample our response data with or without replacement

RUN_ABSTRACT_SIM = True
ABSTRACT_VARIABLE = "EDDY_SYS"
ABSTRACT_VALUES = [1,2,6]

#produces ticket count graph for 1 simulation
COUNT_TICKETS = False

RUN_AVERAGE_COST = False
COST_SAMPLES = 100

RUN_SINGLE_PAIR = False
SINGLE_PAIR_RUNS = 50

RUN_ITEM_ROUTING = False # runs a single test with two predicates, for a 2D graph showing which predicates were priotatized

RUN_MULTI_ROUTING = True # runs NUM_SIM simulations and averges the number of "first items" given to each predicate, can auto gen a bar graph

##################	EPSILON GREEDY MAB OPTIONS	##################
EPSILON = 0.7
REWARD = 1.7
RUN_OPTIMAL_SIM = False # runs NUM_SIM simulations where IP pairs are completed in an optimal order. ignores worker rules

################### OPTIONS FOR REAL OR SYNTHETIC DATA ########################
NUM_SIM = 50 # how many simulations to run?

TIME_SIMS = False # track the computer runtime of simulations

SIMULATE_TIME = False # simulate time passing/concurrency
MAX_TASKS = 25 # maximum number of active tasks in a simulation with time

BUFFER_TIME = 5 # amount of time steps between task selection and task starting
MAX_TASKS_OUT = MAX_TASKS

RUN_TASKS_COUNT = False # actually simulate handing tasks to workers

TRACK_IP_PAIRS_DONE = False

TRACK_PLACEHOLDERS = False # keeps track of the number of times the next worker has no possible task

## WILL ONLY RUN IF RUN_TASKS_COUNT IS TRUE ##
TEST_ACCURACY = False
ACCURACY_COUNT = False

OUTPUT_SELECTIVITIES = False

RUN_CONSENSUS_COUNT = False # keeps track of the number of tasks needed before consensus for each IP

CONSENSUS_LOCATION_STATS = False

VOTE_GRID = False #draws "Vote Grids" from many sims. Need RUN_CONSENSUS_COUNT on. works w/ accuracy

IDEAL_GRID = False #draws the vote grid rules for our consensus metric

TEST_ACCURACY = False
## WILL ONLY RUN IF RUN_TASKS_COUNT IS TRUE ##
OUTPUT_COST = False

PRED_SCORE_COUNT = False

PRED_RANK_COUNT = False

PACKING = True # Enable for "Packing" of outputs into a folder and generation of config.ini

if GEN_GRAPHS:
    print ''
    reply = raw_input("GEN_GRAPHS is turned on. Do you actually want graphs? Enter y for yes, n for no.  ")
    if reply == "n":
        raise Exception ("Set GEN_GRAPHS to False and try again!")

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
            'ABSTRACT_VARIABLE','ABSTRACT_VALUES','COUNT_TICKETS','PRED_RANK_COUNT', 'PRED_SCORE_COUNT', 'RUN_AVERAGE_COST',
            'COST_SAMPLES','RUN_SINGLE_PAIR','SINGLE_PAIR_RUNS','RUN_ITEM_ROUTING',
            'RUN_MULTI_ROUTING','RUN_OPTIMAL_SIM','NUM_SIM','TIME_SIMS','SIMULATE_TIME',
            'MAX_TASKS','BUFFER_TIME','RUN_TASKS_COUNT','TRACK_IP_PAIRS_DONE',
            'TRACK_PLACEHOLDERS','TEST_ACCURACY','OUTPUT_SELECTIVITIES',
            'RUN_CONSENSUS_COUNT','VOTE_GRID','OUTPUT_COST'
]
