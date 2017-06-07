import datetime as DT
now = DT.datetime.now()

RUN_NAME = 'accuracyGraphsTest' + "_" + str(now.date())+ "_" + str(now.time())[:-7]
#TODO: integrate this file with existing files to ensure same stuff happens

ITEM_TYPE = "Restaurant"
#We have 5 questions for hotels right now, 10 for restaurants
NUM_QUEST = 10 #used for accuracy testing

INPUT_PATH = 'dynamicfilterapp/simulation_files/restaurants/'
OUTPUT_PATH = 'dynamicfilterapp/simulation_files/output/'
IP_PAIR_DATA_FILE = 'real_data1.csv'

DEBUG_FLAG = True # useful print statements turned on

####################### CONFIGURING CONSENSUS ##############################
NUM_CERTAIN_VOTES = 5
UNCERTAINTY_THRESHOLD = 1
FALSE_THRESHOLD = 0.2
DECISION_THRESHOLD = 0.5
CUT_OFF = 21

################ CONFIGURING THE ALGORITHM ##################################
#############################################################################
NUM_WORKERS = 101
EDDY_SYS = 1
# EDDY SYS KEY:
# 1 - queue pending system (uses PENDING_QUEUE_SIZE parameter)
# 2 - random system
# 3 - controlled system (uses CHOSEN_PREDS parameter)

PENDING_QUEUE_SIZE = 1

CHOSEN_PREDS = [2, 3] # predicates that will be used when run on real data
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
# 1,4,5 - three most selective
# 4,5,8 - least ambiguous questions
# 0,2,9 - most ambiguous questions
# 2,3,8 - least selective

ITEM_SYS = 0
# ITEM SYS KEY:
# 0 - randomly choose an item
# 1 - item-started system
# 2 - item-almost-false system

SLIDING_WINDOW = False # right now, only works in controlled run mode
LIFETIME = 10

#############################################################################
#############################################################################


###################### CONFIGURING TESTING ##################################
#############################################################################

REAL_DATA = True #if set to false, will use synthetic data (edit in syndata file)

GEN_GRAPHS = False

#################### TESTING OPTIONS FOR REAL DATA ############################
RUN_DATA_STATS = False

RUN_DATA_STATS = False

RUN_AVERAGE_COST = False
COST_SAMPLES = 1000

RUN_SINGLE_PAIR = False
SINGLE_PAIR_RUNS = 5000

################### OPTIONS FOR REAL OR SYNTHETIC DATA ########################
RUN_ITEM_ROUTING = False

RUN_TASKS_COUNT = False # actually simulate handing tasks to workers
NUM_SIM = 50 # how many simulations to run?

## WILL ONLY RUN IF RUN_TASKS_COUNT IS TRUE ##
TEST_ACCURACY = True

OUTPUT_SELECTIVITIES = True

OUTPUT_COST = True

