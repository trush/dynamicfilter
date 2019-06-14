import math

#________ Path Info __________#
PRIMARY_LIST = ''#TODO hotel list
REAL_DATA_CSV = '/simulation_files/CLEANED_ROUND1.csv'#TODO MTURK data CSV

#_____________________________ For Synthetic Data _____________________________#
NUM_PRIM_ITEMS = 90
NUM_SEC_ITEMS = 40
HAVE_SEC_LIST = True #Do we start with the secondary list populated yes/no  <not currently in use?
FAKE_SEC_ITEM_LIST = ["Fake 1; " + str(NUM_SEC_ITEMS+1), "Fake 2; " + str(NUM_SEC_ITEMS+2), "Fake 3; " + str(NUM_SEC_ITEMS+3), "Fake 4; " + str(NUM_SEC_ITEMS+4), "Fake 5; " + str(NUM_SEC_ITEMS+5)] #fake secondary items to choose from

# used in syn_load_find_pairs_tasks
# to determine how many secondary items each primary item is going to be matched with 
MEAN_SEC_PER_PRIM = 3
SD_SEC_PER_PRIM = 0.5
PROB_NONE_SECONDARY = 0

#________ For Real Data ________#
INPUT_PATH = ''
PRIMARY_ITEM_TYPE = "Hotel"  # "Hotel" or "Restaurant"

#________ Simulation Settings ________#
REAL_DATA = False # real or synthetic data
# 0 = joinable filter
# 1 = item-wise join
# 2 = pre-join filtered join
JOIN_TYPE = 1
NUM_WORKERS = 200 # number of distinct workers
NUM_SIMS = 20 # number of simulations to run
PROB_CHOOSING_TRUE_SEC_ITEM = 0.95

# ________ Consensus Settings _________#
# Values used in the find_consensus for an item/task function
NUM_CERTAIN_VOTES = 5  # Recommended val: 5 (unless using agressive bayes)
CUT_OFF = 21
SINGLE_VOTE_CUTOFF = int(1+math.ceil(CUT_OFF/2.0))
BAYES_ENABLED = True
UNCERTAINTY_THRESHOLD = 0.2
DECISION_THRESHOLD = 0.5

UPDATE_ON_CONSENSUS = False #decides whether the task statistics are updated for every assignment (false) or after consensus for each task (true)


#_______ Selectivity and Ambiguity Settings _________#
JF_AMBIGUITY = 0.1
JF_SELECTIVITY = 0.1
SEC_PRED_SELECTIVITY = 0.5 
SEC_PRED_AMBIGUITY = 0.3
JOIN_COND_AMBIGUITY = 0 
JOIN_COND_SELECTIVITY = 0.8 # given that these pairs were created by the crowd
PJF_SELECTIVITY_PRIMARY = 0.1 # PJF selectivity for primary list 
PJF_SELECTIVITY_SECONDARY = 0.1 # PJF selectivity for secondary list
PJF_AMBIGUITY_PRIMARY = 0.1
PJF_AMBIGUITY_SECONDARY = 0.1

#__________________ Time Settings _____________________#
JF_TASK_TIME_MEAN = 100
JF_TASK_TIME_SD = 5
FIND_PAIRS_TASK_TIME_MEAN = 20
FIND_PAIRS_TASK_TIME_SD = 3
SEC_PRED_TASK_TIME_MEAN = 20
SEC_PRED_TASK_TIME_SD = 3
PJF_TIME_PRIMARY_MEAN = 20
PJF_TIME_PRIMARY_SD = 3
PJF_TIME_SECONDARY_MEAN = 20
PJF_TIME_SECONDARY_SD = 3


#______ Miscellany ___________#
# Used in the enumeration estimate in chao_estimator(). If the difference between the size of list2 and the size of the 
# estimated number is less than this fraction of the size of the estimate then chao_estimator() will return True.
THRESHOLD = 0.1
