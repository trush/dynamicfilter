import datetime as DT
import sys
now = DT.datetime.now()
from responseTimeDistribution import *

# ****************************** DEBUG FLAG ****************************** #
# ************************************************************************ #
DEBUG_FLAG = True
# ************************************************************************ #


# **************************** INPUT SETTINGS **************************** #
# ************************************************************************ #

REAL_DATA = False

# ______ REAL DATA SETTINGS ______ #
INPUT_PATH = 'dynamicfilterapp/simulation_files/hotels/'
ITEM_TYPE = "Hotel"                   # "Hotel" or "Restaurant"
IP_PAIR_DATA_FILE = 'hotel_cleaned_data.csv'
REAL_DISTRIBUTION_FILE = 'workerDist.csv'
TRUE_TIMES, FALSE_TIMES = importResponseTimes(INPUT_PATH + IP_PAIR_DATA_FILE)

CHOSEN_PREDS = [3,4]

# ___ SYNTHETIC DATA SETTINGS ____ #
NUM_QUESTIONS = 4
NUM_ITEMS = 400
SIN = -1

SELECTIVITY_GRAPH = False

# SIN tuple is of the form (SIN, amp, period, samplingFrac, trans). If trans is 0, it starts at the
# selectvity of the previous timestep
# tuples of form (task number, (select,amb), (select,amb))
switch_list = [ (0, (0.9, 0.75), (0.7, 0.75), (0.5, 0.75), (0.4, 0.75)) ]

# ************************************************************************ #


# ************************** ALGORITHM SETTINGS ************************** #
# ************************************************************************ #

EDDY_SYS = 1
ITEM_SYS = 0
SLIDING_WINDOW = False
LIFETIME = 40
PENDING_QUEUE_SIZE = 2
ADAPTIVE_QUEUE = True
ADAPTIVE_QUEUE_MODE = 0
# 0 - only increase ql if reached that number of tickets
# 1 - increase like (0) but also decreases if a pred drops below the limit
QUEUE_LENGTH_ARRAY = [(0,1),(4,2),(8,3), (16,4)] # settings for above mode [(#tickets,qlength)]

# ************************************************************************ #



# ************************** CONSENSUS SETTINGS ************************** #
# ************************************************************************ #

NUM_CERTAIN_VOTES = 5               # Recomended val: 5 (unless using agressive bayes)
##VoteCutOff
CUT_OFF = 21
                 #TODO test more stuff on synth data
SINGLE_VOTE_CUTOFF = int(1+math.ceil(CUT_OFF/2.0))

BAYES_ENABLED = False

UNCERTAINTY_THRESHOLD = 0.05

DECISION_THRESHOLD = 0.9

FALSE_THRESHOLD = 0.05

ADAPTIVE_CONSENSUS = False
ADAPTIVE_CONSENSUS_MODE = 4
PREDICATE_SPECIFIC = True
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

NUM_WORKERS = 5000
DISTRIBUTION_TYPE = 0               # tells pick_worker how to choose workers
DUMMY_TASKS = True
DUMMY_TASK_OPTION = 0
RESPONSE_SAMPLING_REPLACEMENT = False

NUM_SIM = 10

TIME_SIMS = False

SIMULATE_TIME = True # simulate time passing/concurrency

# ___ SIMULATED TIME SETTINGS ____ #
ACTIVE_TASKS_SIZE = 25
BUFFER_TIME = 5
MAX_TASKS_OUT = 10
MAX_TASKS_COLLECTED = CUT_OFF

# ************************************************************************ #


# **************************** OUTPUT SETTINGS *************************** #
# ************************************************************************ #

# ___ FILE MANAGEMENT ____ #
RUN_NAME = 'Scaling_Investigation' + "_" + str(now.date())+ "_" + str(now.time())[:-7]
OUTPUT_PATH = 'dynamicfilterapp/simulation_files/output/'
GEN_GRAPHS = True
PACKING=True

if GEN_GRAPHS:
    print ''
    reply = raw_input("GEN_GRAPHS is turned on. Do you actually want graphs? Enter y for yes, n for no (turns off graphs), or c to cancel. ")
    if reply == "c":
        raise Exception ("Change your setup and try again!")
    elif reply == "n":
        print "~~~~~~ Graphing turned off ~~~~~~"
        GEN_GRAPHS = False

# ___ DATA COLLECTION: REAL DATA ____ #
RUN_DATA_STATS = False

RUN_AVERAGE_COST = True
COST_SAMPLES = 1

RUN_SINGLE_PAIR = True
SINGLE_PAIR_RUNS = 1

RUN_ITEM_ROUTING = False
RUN_MULTI_ROUTING = False

RUN_OPTIMAL_SIM = False #TODO: can you do this with synthetic data?

# ___ DATA COLLECTION: REAL OR SYNTHETIC DATA ____ #
COUNT_TICKETS = True
TRACK_QUEUES = True

RUN_ABSTRACT_SIM = False
ABSTRACT_VARIABLE = "NUM_WORKERS"
ABSTRACT_VALUES = [10, 20]

RUN_TASKS_COUNT = False
TRACK_IP_PAIRS_DONE = False

TRACK_ACTIVE_TASKS = True # Useful only for simulations with TIME

TRACK_PLACEHOLDERS = True

TEST_ACCURACY = False
ACCURACY_COUNT = False

OUTPUT_SELECTIVITIES = False
OUTPUT_COST = False

RUN_CONSENSUS_COUNT = False
CONSENSUS_LOCATION_STATS = False
TRACK_SIZE = False
VOTE_GRID = False
IDEAL_GRID = False

# ************************************************************************ #

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
            'RUN_CONSENSUS_COUNT','VOTE_GRID','OUTPUT_COST', 'TRACK_ACTIVE_TASKS', 'TRACK_QUEUES',
            'PREDICATE_SPECIFIC', 'W_MAX', 'CUBIC_B', 'CUBIC_C', 'ADAPTIVE_CONSENSUS_MODE',
            'IDEAL_GRID', 'K', 'CONSENSUS_STATUS', 'SINGLE_VOTE_CUTOFF', 'NUM_ITEMS', 'NUM_QUESTIONS',
            'SELECTIVITY_GRAPH', 'CONSENSUS_STATUS_LIMITS', 'ACCURACY_COUNT', 'TRACK_SIZE',
            'ADAPTIVE_CONSENSUS', 'CONSENSUS_SIZE_LIMITS', 'RENO_BONUS_RATIO', 'BAYES_ENABLED'
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
