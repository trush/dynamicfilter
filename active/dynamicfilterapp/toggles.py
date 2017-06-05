import datetime as DT
now = DT.datetime.now()

RUN_NAME = 'monday0505' + "_" + str(now.date())+ "_" + str(now.time())[:-7]
#TODO: integrate this file with existing files to ensure same stuff happens

ITEM_TYPE = "Restaurant"

INPUT_PATH = 'dynamicfilterapp/simulation_files/restaurants/'
OUTPUT_PATH = 'dynamicfilterapp/simulation_files/output/'
IP_PAIR_DATA_FILE = 'real_data1.csv'

DEBUG_FLAG = True # useful print statements turned on

################ CONFIGURING THE ALGORITHM ##################################
#############################################################################
EDDY_SYS = 3
# EDDY SYS KEY:
# 1 - queue pending system (uses PENDING_QUEUE_SIZE parameter)
# 2 - random system
# 3 - controlled system (uses CHOSEN_PREDS parameter)

PENDING_QUEUE_SIZE = 1
CONTROLLED_RUN_PREDS = [3, 2] #predicates used in a controlled simulated run
# CONTROLLED_RUN_PREDS should be a list of 2 predicates (for now). They will be
# passed items in the order they appear in the list.

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

ITEM_SYS = 2
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

#################### TESTING OPTIONS FOR REAL DATA ############################
RUN_DATA_STATS = True

RUN_AVERAGE_COST = True
COST_SAMPLES = 1000

RUN_SINGLE_PAIR = True
SINGLE_PAIR_RUNS = 5000

################### OPTIONS FOR REAL OR SYNTHETIC DATA ########################
TEST_ACCURACY = True
FILTER_BY_PREDS = [2, 3] # predicates we want to check successful filtering by

RUN_TASKS_COUNT = True # actually simulate handing tasks to workers
NUM_SIM = 1 # how many simulations to run?

## WILL ONLY RUN IF RUN_TASKS_COUNT IS TRUE ##
OUTPUT_SELECTIVITIES = True
SELECTIVITY_PREDS = [2, 3] # predicates whose selectivities we want to estimate
                           # if controlled eddy system, must match CONTROLLED_RUN_PREDS

## WILL ONLY RUN IF RUN_TASKS_COUNT IS TRUE ##
OUTPUT_COST = True
COST_PREDS = [2, 3] # predicates whose cost we want to estimate
                    # if controlled eddy system, must match CONTROLLED_RUN_PREDS
