import datetime as DT
import sys
import math
now = DT.datetime.now()
import responseTimeDistribution

# ****************************** DEBUG FLAG ****************************** #
# ************************************************************************ #
DEBUG_FLAG = False
SIM_TIME_STEP = 60
# ************************************************************************ #


# **************************** INPUT SETTINGS **************************** #
# ************************************************************************ #

REAL_DATA = False # if False, use synethic data

# ______ REAL DATA SETTINGS ______ #
INPUT_PATH = 'dynamicfilterapp/simulation_files/hotels/'
ITEM_TYPE = "Hotel"       # "Hotel" or "Restaurant"
IP_PAIR_DATA_FILE = 'hotel_cleaned_data.csv'
REAL_DISTRIBUTION_FILE = 'workerDist.csv'
TRUE_TIMES, FALSE_TIMES = responseTimeDistribution.importResponseTimes(INPUT_PATH + IP_PAIR_DATA_FILE)

# ___ SYNTHETIC DATA SETTINGS ____ #
NUM_QUESTIONS = 2
NUM_ITEMS = 160
SIN = -1
SELECTIVITY_GRAPH = False
switch_list = [ (0, (0.3,0), (0.3,0))]

# SIN tuple is of the form (SIN, amp, period, samplingFrac, trans). If trans is 0, it starts at the
# selectvity of the previous timestep
# tuples of form (task number, (select,amb), (select,amb))
# selectivity and ambiguity - min value: 0  max value: 1

# ___ PREDICATES (FOR REAL OR SYNTHETIC) ____ #
if REAL_DATA:
    CHOSEN_PREDS = [0]
else:
    CHOSEN_PREDS = range(len(switch_list[0]) - 1)


# ************************************************************************ #


# ************************** ALGORITHM SETTINGS ************************** #
# ************************************************************************ #

EDDY_SYS = 5
ITEM_SYS = 0
SLIDING_WINDOW = False
LIFETIME = 150
PENDING_QUEUE_SIZE = 40
QUEUE_SUM = 100

IP_LIMIT_SYS = 0   # type of predicate limit for an item
ITEM_IP_LIMIT = 4   # number of predicates an item can be in

ADAPTIVE_QUEUE = False
ADAPTIVE_QUEUE_MODE = 0
# 0 - only increase ql if reached that number of tickets
# 1 - increase like (0) but also decreases if a pred drops below the limit
QUEUE_LENGTH_ARRAY = [(0, 4), (3, 15), (10, 30)] # settings for above mode [(#tickets,qlength)]
ACTIVE_TASKS_ARRAY = [(0, 0, 0), (1, 10, 40), (10, 150, 200), (50, 350, 450)] #Only matters (atm) if batch assignment on
#[(0,0,0),(1,10,40),(10,75,100),(20,150,200),(40,350,450)]
BATCH_ASSIGNMENT = 2 # 0 - No batches, 1 - Refill limit, 2 - Periodic refill
REFILL_PERIOD = 100

EPSILON = 0.7
REWARD = 1.7
# ************************************************************************ #



# ************************** JOIN SETTINGS ************************** #
# ************************************************************************ #
#see the Join class in models.py for more information
USE_JOINS = True
PROPORTION_JOINS = 1.0
STARTED_JOIN_RATIO = 0.5
## Settings #-----------------------###############


    ## join data
JOIN_SELECTIVITY = 0.2
JOIN_TIME = 4.0 
JOIN_TIME_STD = 0.5
JOIN_AMBIGUITY = 0.0

    ## PJFjoin in particular
PJF_SELECTIVITY = 0.6
TIME_TO_EVAL_PJF = 10.0
PJF_TIME_STD = 2.0
PJF_AMBIGUITY = 0.0

    ## PWJoin in particular 
BASE_FIND_MATCHES = 6.0     #Basic requirement to find some matches
FIND_SINGLE_MATCH_TIME = 0.70 #cost per match found
AVG_MATCHES = 5 #average matches per item
STDDEV_MATCHES = 1 #standard deviation of matches

    ## small predicate in particular
SMALL_P_SELECTIVITY = 0.5
TIME_TO_EVAL_SMALL_P = 3.0
SMALL_P_TIME_STD = 0.5
SP_AMBIGUITY = 0.0

    ## Other private variables used for simulations
HAS_LIST2 = False
EXPLORATION_REQ = 5 #once join has two lists, it will try each path this many times at least
private_list2 = [ "Red", "Blue", "Green", "Yellow", "Orange", "Purple", "Mauve", "Peridot", "Periwinkle", "Gold", "Gray", "Burgundy", "Silver", "Taupe", "Brown", "Ochre", "Jasper", "Lavender", "Violet", "Pink", "Magenta" ] 
pjf_dict = {"PJF1": (0.3, 10.0), "PJF2": (0.75, 2.0), "PJF3": (0.35, 14.0), "PJF4": (0.66, 7.0)}
GEN_PJF_AMBIGUITY = 0.1
GEN_PJF_TIME = 5.0
GEN_PJF_STD = 1.0

#denotes how close the actual number of estimated 2nd list items must be found
# to the estimated number for species estimation
THRESHOLD = 0.1


# ************************************************************************ #



# ************************** CONSENSUS SETTINGS ************************** #
# ************************************************************************ #

NUM_CERTAIN_VOTES = 5            # Recomended val: 5 (unless using agressive bayes)
##VoteCutOff
CUT_OFF = 21
                 #TODO test more stuff on synth data
SINGLE_VOTE_CUTOFF = int(1+math.ceil(CUT_OFF/2.0))

BAYES_ENABLED = True

UNCERTAINTY_THRESHOLD = 0.2

DECISION_THRESHOLD = 0.5

FALSE_THRESHOLD = 0.05

ADAPTIVE_CONSENSUS = False
ADAPTIVE_CONSENSUS_MODE = 4
PREDICATE_SPECIFIC = False
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

# ************************************************************************ #


# ************************** SIMULATION SETTINGS ************************* #
# ************************************************************************ #

NUM_WORKERS = 100000
DISTRIBUTION_TYPE = 0            # tells pick_worker how to choose workers
DUMMY_TASKS = True
DUMMY_TASK_OPTION = 0
RESPONSE_SAMPLING_REPLACEMENT = True

NUM_SIM = 0
NUM_GRAPH_SIM = 0

SIMULATE_TIME = True # simulate time passing/concurrency

# ___ SIMULATED TIME SETTINGS ____ #
TASKS_PER_SECOND = True ## \todo add to toggles_info
ACTIVE_TASKS_SIZE = 160
RESIZE_ACTIVE_TASKS = False
BUFFER_TIME = 0
MAX_TASKS_OUT = 40
MAX_TASKS_COLLECTED = CUT_OFF

MULTI_SIM = True 
MULTI_SIM_ARRAY = [(1,(0, 1),[(0,0,0),(1,10,40),(10,150,200),(50,350,450)],[(0,4),(3,15),(10,30)],[(0,(0.2,0.25,.5),(0.2,0.25,.5))],0)]
# ************************************************************************ #


# **************************** OUTPUT SETTINGS *************************** #
# ************************************************************************ #

# ___ FILE MANAGEMENT ____ #
RUN_NAME = 'aaa_test' + "_" + str(now.date())+ "_" + str(now.time())[:-7]
OUTPUT_PATH = 'dynamicfilterapp/simulation_files/output/'
GEN_GRAPHS = False
PACKING=True

if GEN_GRAPHS:
    print ''
    reply = raw_input("GEN_GRAPHS is turned on. Do you actually want graphs?\
                        Enter y for yes, n for no (turns off graphs), or c \
                        to cancel. ")
    if reply == "c":
        raise Exception ("Change your setup and try again!")
    elif reply == "n":
        print "~~~~~~ Graphing turned off ~~~~~~"
        GEN_GRAPHS = False

# ___ DATA COLLECTION: REAL DATA ____ #
RUN_DATA_STATS = True
RUN_TASKS_STATS = True

RUN_AVERAGE_COST = True
COST_SAMPLES = 1

RUN_SINGLE_PAIR = False # deprecated?
SINGLE_PAIR_RUNS = 1    # deprecated?

RUN_ITEM_ROUTING = False # deprecated?
RUN_MULTI_ROUTING = True

RUN_OPTIMAL_SIM = False #TODO: can you do this with synthetic data?

# ___ DATA COLLECTION: REAL OR SYNTHETIC DATA ____ #
COUNT_TICKETS = True
TRACK_QUEUES = True

RUN_ABSTRACT_SIM = False
ABSTRACT_VARIABLE = "NUM_WORKERS"
ABSTRACT_VALUES = [100, 200]

RUN_TASKS_COUNT = True
TRACK_IP_PAIRS_DONE = False

TRACK_ACTIVE_TASKS = True # Useful only for simulations with TIME
TRACK_PLACEHOLDERS = True
TRACK_WASTE = True  # Tracks tasks leftover from finished items

EDDY_SET = [5]     # Used only when TRACK_ACTIVE_TASKS is true   
QUEUE_SET = [40] 
ACTIVE_TASKS_SET = [160]

TEST_ACCURACY = False
ACCURACY_COUNT = False

OUTPUT_SELECTIVITIES = False
OUTPUT_COST = False
PRED_SCORE_COUNT = False

RUN_CONSENSUS_COUNT = False
CONSENSUS_LOCATION_STATS = False
TRACK_SIZE = False
VOTE_GRID = False
IDEAL_GRID = False

TIME_SIMS = False # NOT turning on simulated time; counting how long function calls take

# ************************************************************************ #

# List of toggles for debug printing and Config.ini generation
            ##### PLEASE UPDATE AS NEW TOGGLES ADDED #####
VARLIST =  ['RUN_NAME','ITEM_TYPE','INPUT_PATH','OUTPUT_PATH','IP_PAIR_DATA_FILE',
            'REAL_DISTRIBUTION_FILE','DEBUG_FLAG',
            'NUM_CERTAIN_VOTES','CUT_OFF','SINGLE_VOTE_CUTOFF','BAYES_ENABLED',
            'UNCERTAINTY_THRESHOLD','DECISION_THRESHOLD','FALSE_THRESHOLD',
            'ADAPTIVE_CONSENSUS','ADAPTIVE_CONSENSUS_MODE','PREDICATE_SPECIFIC',
            'CONSENSUS_STATUS_LIMITS','CONSENSUS_SIZE_LIMITS','RENO_BONUS_RATIO',
            'CONSENSUS_STATUS','K','W_MAX','CUBIC_C','CUBIC_B','NUM_WORKERS',
            'DISTRIBUTION_TYPE','EDDY_SYS','PENDING_QUEUE_SIZE',
            'CHOSEN_PREDS','ITEM_SYS','SLIDING_WINDOW','LIFETIME','ADAPTIVE_QUEUE',
            'ADAPTIVE_QUEUE_MODE','QUEUE_LENGTH_ARRAY','REAL_DATA', 'DUMMY_TASKS',
            'DUMMY_TASK_OPTION','GEN_GRAPHS','NUM_ITEMS','SIN', 'QUEUE_SUM',
            'SELECTIVITY_GRAPH','switch_list', 'ITEM_IP_LIMIT', 'IP_LIMIT_SYS',
            'RUN_DATA_STATS','RESPONSE_SAMPLING_REPLACEMENT','RUN_ABSTRACT_SIM',
            'ABSTRACT_VARIABLE','ABSTRACT_VALUES','COUNT_TICKETS', 'PRED_SCORE_COUNT', 'RUN_AVERAGE_COST',
            'COST_SAMPLES','RUN_SINGLE_PAIR','SINGLE_PAIR_RUNS','RUN_ITEM_ROUTING',
            'RUN_MULTI_ROUTING','RUN_OPTIMAL_SIM', 'SIM_TIME_STEP', 'TRACK_WASTE', 
            'EDDY_SET', 'QUEUE_SET', 'ACTIVE_TASKS_SET', 'ACTIVE_TASKS_ARRAY',
            'NUM_SIM','TIME_SIMS','SIMULATE_TIME', 'NUM_GRAPH_SIM', 'BATCH_ASSIGNMENT',
            'ACTIVE_TASKS_SIZE', "MAX_TASKS_COLLECTED", "MAX_TASKS_OUT", 'BUFFER_TIME','RUN_TASKS_COUNT','TRACK_IP_PAIRS_DONE',
            'TRACK_PLACEHOLDERS','TEST_ACCURACY','OUTPUT_SELECTIVITIES', 'REFILL_PERIOD',
            'RUN_CONSENSUS_COUNT','VOTE_GRID','OUTPUT_COST', 'TRACK_ACTIVE_TASKS', 'TRACK_QUEUES',
            'PREDICATE_SPECIFIC', 'W_MAX', 'CUBIC_B', 'CUBIC_C', 'ADAPTIVE_CONSENSUS_MODE',
            'IDEAL_GRID', 'K', 'CONSENSUS_STATUS', 'SINGLE_VOTE_CUTOFF', 'NUM_ITEMS', 'NUM_QUESTIONS',
            'SELECTIVITY_GRAPH', 'CONSENSUS_STATUS_LIMITS', 'ACCURACY_COUNT', 'TRACK_SIZE',
            'ADAPTIVE_CONSENSUS', 'CONSENSUS_SIZE_LIMITS', 'RENO_BONUS_RATIO', 'BAYES_ENABLED', 'RESIZE_ACTIVE_TASKS',
            'TASKS_PER_SECOND', 'EPSILON', 'REWARD',
            'MULTI_SIM', 'MULTI_SIM_ARRAY', 'USE_JOINS', 'JOIN_SELECTIVITY', 'PJF_SELECTIVITY',
            'JOIN_TIME', 'TIME_TO_EVAL_PJF', 'BASE_FIND_MATCHES', 'FIND_SINGLE_MATCH_TIME',
            'AVG_MATCHES', 'STDDEV_MATCHES', 'SMALL_P_SELECTIVITY', 'TIME_TO_EVAL_SMALL_P',
            'HAS_LIST2', 'private_list2', 'THRESHOLD', 'EXPLORATION_REQ', 'JOIN_AMBIGUITY',
            'SP_AMBIGUITY', 'PJF_AMBIGUITY', 'SMALL_P_TIME_STD', 'JOIN_TIME_STD', 'PJF_TIME_STD',
            'pjf_dict', 'GEN_PJF_TIME', 'GEN_PJF_STD', 'GEN_PJF_AMBIGUITY', 'PROPORTION_JOINS', 'STARTED_JOIN_RATIO','RUN_TASKS_STATS'
]

#This is a blocklist. the variables to store in config.ini is now auto-generated from this file
    # THIS MEANS NEW VARIABLES WILL BE AUTO ADDED IN PLACE
    # if you added a new variable and don't want it to be added to config.ini, put it's name here
VARBLOCKLIST = ['__builtins__','__package__','__name__','__doc__',
                'name','sys','__file__','now','DT','responseTimeDistribution',
                'TRUE_TIMES','FALSE_TIMES','math','configDict','VARLIST',
                'VARBLOCKLIST','CONSENSUS_LOCATION_STATS','PACKING','reply',
                'line_graph_gen', 'pylab', 'hist_gen', 'SIN', 'importResponseTimes',
                'scipy', 'stats_bar_graph_gen', 'multi_hist_gen', 'multi_line_graph_gen',
                'csv', 'generic_csv_read', 'generic_csv_write', 'restaurants',
                'bar_graph_gen', 'split_bar_graph_gen', "Suppress", 'makedirs',
                'defaultdict', 'plt', 'Counter', 'packageMaker', 'os', 'hotels',
                'np', 'sns', 'dest_resolver'
                ]



name = ""
for name in locals():
    if name not in VARLIST and name not in VARBLOCKLIST:
        raise ValueError("Toggle: " + name + " not in either VARLIST or VARBLOCKLIST... Please add it!")
