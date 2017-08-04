import datetime as DT
import sys
now = DT.datetime.now()
from responseTimeDistribution import *
DEBUG_FLAG = True # useful print statements turned on
RUN_NAME = 'Scaling_Investigation' + "_" + str(now.date())+ "_" + str(now.time())[:-7]
OUTPUT_PATH = 'dynamicfilterapp/simulation_files/output/'

# INPUT SETTINGS

#_________________ Real Data Settings ___________________#
ITEM_TYPE = "Hotel"
INPUT_PATH = 'dynamicfilterapp/simulation_files/hotels/'
IP_PAIR_DATA_FILE = 'hotel_cleaned_data.csv'
REAL_DISTRIBUTION_FILE = 'workerDist.csv'
TRUE_TIMES, FALSE_TIMES = importResponseTimes(INPUT_PATH + IP_PAIR_DATA_FILE)
REAL_DATA = False
CHOSEN_PREDS = [0,1]
####################### CONFIGURING CONSENSUS ##############################
# This desc. is old and some of the variable names may no longer match, but the
# algorithm described is still the same
    # Our consensus metric is Complicated. For each IP pair chosen, we do the following
    # We gather (NUM_CERTAIN_VOTES) votes on the chosen IP pair
    # To take "consensus" we generate a beta distribution from the number of (y/n) votes
    #   then intigrate over it from zero to (DECISION_THRESHOLD)
    #   if the probability area is less than (UNCERTAINTY_THRESHOLD) then we have consensus
    #   else we gather more votes
    # This is repeated until one of several conditions is met
    #   1 - We reach consensus (naturally(Bayes))
    #   2 - The total number of gathered votes is equal to (CUT_OFF)
    #   3 - The number of either (yes)s or (no)s on their own is equal to (SINGLE_VOTE_CUTOFF)
    # If either cond. (2|3) we take a simple majority vote

##General Consensus
NUM_CERTAIN_VOTES = 5   # number of votes to gather no matter the results
                        # higher values leave consensus less vulnerable to initial randomness
                        # Should never go below 3 (5 is really low anyway)
                        # Recomended val: 5 (unless using agressive bayes)
##VoteCutOff
CUT_OFF = 21    # Maximum number of votes to ask for before using Majority Vote as backup metric
                # Only rather ambiguous IP pairs should ever actually reach this limit
                # Recomended value (21 for real data) #TODO test more stuff on synth data
SINGLE_VOTE_CUTOFF = int(1+math.ceil(CUT_OFF/2.0))  # Number of votes for a single result (Y/N) before calling that the winner #TODO remove this!
                                                    # This should be depricated soon
                                                    # if you're reading this, Jake forgot to take this variable out or was lazy

##Bayes:
    # The Bayes portion of the alg is weird and bayesian
    # we assume no prior knowledge of the IP pair and thus that there is an
    # even likelyhood of it being either true or false.
    # In the bayesian world we represent everything as a distribution of probability.
    # We use a beta-distribution [https://en.wikipedia.org/wiki/Beta_distribution]
    # to represent the distribution of our probability. the beta-distribution has two
    # parameters which govern its shape, (a&b). we start with both at 1 which is a
    # uniform flat distribution. These a and b represent the number of votes for either
    # yes or no on a given IP pair where their values should always be 1 more than the
    # number of votes for each catagory. To take consensus, we build our distribution
    # and integrate over it from zero to DECISION_THRESHOLD. If the total area in that
    # area is less than the UNCERTAINTY_THRESHOLD, we have reached consensus.
    # The motivation is this. The integration is asking the question:
    # "With the data we have right now, what's the probability that the true [...]
    # probability is between 0 and (e.g.) 0.5." (Our IP pair has some true ratio of
    # yes votes to no votes.) If the probability of the ratio being within that range
    # is small enough, (smaller than UNCERTAINTY_THRESHOLD) we can conclude that the
    # true ratio must be larger than that. If the probability is low enough, and the
    # DECISION_THRESHOLD chosen correctly, we can say that we have determined the
    # ratio, and thus know the "true" answer to our question.
BAYES_ENABLED = False           # Should we even use bayes at all?

UNCERTAINTY_THRESHOLD = 0.05    # maximum acceptable proability area
                                # how likely to be wrong we're ok with being
DECISION_THRESHOLD = 0.9        # Upper bound of integration
                                # (how significant the ratio must be)
FALSE_THRESHOLD = 0.05          # Used for ALMOST_FALSE TODO better docs

##Adaptive Consensus
    # Our algorithm can attempt to "Learn" what a good consensus alg. looks like
    # by looking at the IP pairs which reach Completion (Total Number of tasks, "Location", etc.)
    # Below are the configurations the adaptability. This section is still very
    # much in progress and subject to much change

ADAPTIVE_CONSENSUS = False  # Enables of disables the adaptive Consensus outright
ADAPTIVE_CONSENSUS_MODE = 4 #Which algorithm should the adaptive consensus use?
                            # 1 - RENO:  [https://en.wikipedia.org/wiki/TCP_congestion_control#TCP_Tahoe_and_Reno]
                            # 2 - TAHOE: See reno
                            # 3 - CUTE:  [goo.gl/etdxtC]
                            # 4 - CUBIC: [https://en.wikipedia.org/wiki/CUBIC_TCP]
PREDICATE_SPECIFIC = False  # Should each predicate have their own adaptive Consensus metric? or should it be one general metric
                            # Generally most useful for predicates of vastly differing ambiguity
                                # or unkown ambiguity.
                            # Recomended setting: True
CONSENSUS_STATUS_LIMITS = (-3,3)    # The limits we need to reach before inc/dec-rementing the max votes size
                                    # format (-#, +#) for (decrement val, increment val)
CONSENSUS_SIZE_LIMITS = (7, 101)
RENO_BONUS_RATIO = 1.5
CONSENSUS_STATUS = 0        # Used only when PREDICATE_SPECIFIC is False.
                            # used as universal version of consensus_status
K = 8
W_MAX = 6
CUBIC_C = (1.0/50.0)
CUBIC_B = (0.8)
#________________ CONFIGURING THE ALGORITHM ___________________#

## The number of unique worker (IDs) that a simulation can pick from
NUM_WORKERS = 300
## Tells pick_worker() how to choose workers
# 0  -  Uniform Distribution; (all worker equally likely)
# 1  -  Geometric Distribution; (synthetic graph which fits out data well)
# 2  -  Real Distribution (samples directly from the real data)
DISTRIBUTION_TYPE = 0 # tells pick_worker how to choose workers.

## Determines which algorithm we're actually using to pick IP Pairs
# 1 - queue pending system (uses PENDING_QUEUE_SIZE parameter)
# 2 - random system
# 3 - controlled system (uses CHOSEN_PREDS parameter)
EDDY_SYS = 7

## The size of the "queue" for each predicate. This can be made dynamic if desired.
# For toggles.EDDY_SYS = 5, this is the \a minimum number of unique IP Pairs to be in progress at any given time for a predicate. For toggles.EDDY_SYS = 1,
# this is a \a maximum number of IP Pairs in progress for each predicate.
PENDING_QUEUE_SIZE = 2



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
NUM_QUESTIONS = 2
NUM_ITEMS = 300
SIN = -1

SELECTIVITY_GRAPH = False

# SIN tuple is of the form (SIN, amp, period, samplingFrac, trans). If trans is 0, it starts at the 
# selectvity of the previous timestep
#switch_list = [(0, (0.6, 0.68), (0.6, 0.87)), (100, ((SIN, .2, 100, .1, 0), 0.68), (0.6, 0.87))]
 #(time,(selectivity,ambiguity), (...))
switch_list = [(0, (0.9, 0.7), (0.3, 0.98))]#, (800, (0.3, 0.3), (0.8, 0.3))]

#################### TESTING OPTIONS FOR REAL DATA ############################
RUN_DATA_STATS = False

RESPONSE_SAMPLING_REPLACEMENT = False # decides if we should sample our response data with or without replacement

RUN_ABSTRACT_SIM = False
ABSTRACT_VARIABLE = "EDDY_SYS"
ABSTRACT_VALUES = [1,2,6]

#produces ticket count graph for 1 simulation
COUNT_TICKETS = False
TRACK_QUEUES = False

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
NUM_SIM = 3 # how many simulations to run?

TIME_SIMS = False # track the computer runtime of simulations

SIMULATE_TIME = True # simulate time passing/concurrency
ACTIVE_TASKS_SIZE = 25 # maximum number of active tasks in a simulation with time

BUFFER_TIME = 5 # amount of time steps between task selection and task starting
MAX_TASKS_OUT = 10
MAX_TASKS_COLLECTED = CUT_OFF

RUN_TASKS_COUNT = True # actually simulate handing tasks to workers

TRACK_IP_PAIRS_DONE = False

TRACK_ACTIVE_TASKS = False

TRACK_PLACEHOLDERS = False # keeps track of the number of times the next worker has no possible task

## WILL ONLY RUN IF RUN_TASKS_COUNT IS TRUE ##
TEST_ACCURACY = False
ACCURACY_COUNT = False

OUTPUT_SELECTIVITIES = False

RUN_CONSENSUS_COUNT = False # keeps track of the number of tasks needed before consensus for each IP

CONSENSUS_LOCATION_STATS = False

TRACK_SIZE = True
VOTE_GRID = False #draws "Vote Grids" from many sims. Need RUN_CONSENSUS_COUNT on. works w/ accuracy

IDEAL_GRID = False #draws the vote grid rules for our consensus metric

TEST_ACCURACY = False
## WILL ONLY RUN IF RUN_TASKS_COUNT IS TRUE ##
OUTPUT_COST = False

PRED_SCORE_COUNT = False

PACKING = True # Enable for "Packing" of outputs into a folder and generation of config.ini

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
            'ABSTRACT_VARIABLE','ABSTRACT_VALUES','COUNT_TICKETS', 'PRED_SCORE_COUNT', 'RUN_AVERAGE_COST',
            'COST_SAMPLES','RUN_SINGLE_PAIR','SINGLE_PAIR_RUNS','RUN_ITEM_ROUTING',
            'RUN_MULTI_ROUTING','RUN_OPTIMAL_SIM','NUM_SIM','TIME_SIMS','SIMULATE_TIME',
            'ACTIVE_TASKS_SIZE', "MAX_TASKS_COLLECTED", "MAX_TASKS_OUT", 'BUFFER_TIME','RUN_TASKS_COUNT','TRACK_IP_PAIRS_DONE',
            'TRACK_PLACEHOLDERS','TEST_ACCURACY','OUTPUT_SELECTIVITIES',
            'RUN_CONSENSUS_COUNT','VOTE_GRID','OUTPUT_COST', 'TRACK_ACTIVE_TASKS', 'TRACK_QUEUES'
]

#This is a blocklist. the variables to store in config.ini is now auto-generated from this file
    # THIS MEANS NEW VARIABLES WILL BE AUTO ADDED IN PLACE
    # if you added a new variable and don't want it to be added to config.ini, put it's name here
VARBLOCKLIST = ['__builtins__','__package__','__name__','__doc__',
                'name','sys','__file__','now','DT','responseTimeDistribution',
                'TRUE_TIMES','FALSE_TIMES','math','configDict','VARLIST',
                'VARBLOCKLIST','CONSENSUS_LOCATION_STATS','PACKING','reply']



# name = ""
# for name in locals():
#     if name not in VARLIST and name not in VARBLOCKLIST:
#         raise ValueError("Toggle: " + name + " not in either VARLIST or VARBLOCKLIST... Please add it!")
