import math

#________ Path Info __________#
PRIMARY_LIST = ''#TODO hotel list
REAL_DATA_CSV = ''#TODO MTURK data CSV

#________ For Synthetic Data _________#
NUM_PRIM_ITEMS = 90
NUM_SEC_ITEMS = 1000
HAVE_SEC_LIST = True #Do we start with the secondary list populated yes/no  <not currently in use?


#to determine how many secondary items each primary item is going to be matched with, used in syn_load_find_pairs_tasks
MEAN_SEC_PER_PRIM = 20
SD_SEC_PER_PRIM = 4
SAMPLE_W_REPLACE_NUM_SEC = False


#________ For Real Data ________#
INPUT_PATH = ''
PRIMARY_ITEM_TYPE = "Hotel"       # "Hotel" or "Restaurant"

#________ Simulation Settings ________#
REAL_DATA = True
# 0 = joinable filter
# 1 = item-wise join
# 2 = pre-join filtered join
JOIN_TYPE = 0 

# ________ Consensus Settings _________#

NUM_CERTAIN_VOTES = 5            # Recomended val: 5 (unless using agressive bayes)
CUT_OFF = 21
SINGLE_VOTE_CUTOFF = int(1+math.ceil(CUT_OFF/2.0))
BAYES_ENABLED = True
UNCERTAINTY_THRESHOLD = 0.2
DECISION_THRESHOLD = 0.5


#_______ Selectivity and Ambiguity Settings _________#
JF_AMBIGUITY = 0.1
JF_SELECTIVITY = 0.1
SEC_PRED_SELECTIVITY = 0.1 #Actually a join-wide toggle
SEC_PRED_AMBIGUITY = 0.1 #Actually a join-wide toggle
JOIN_COND_AMBIGUITY = 0.1 
JOIN_COND_SELECTIVITY = 0.1 #given that these pairs were created by the crowd
PJF_SELECTIVITY_PRIMARY = 0.1
PJF_SELECTIVITY_SECONDARY = 0.1
PJF_AMBIGUITY_PRIMARY = 0.1
PJF_AMBIGUITY_SECONDARY = 0.1

#__________________ Time Settings _____________________#
JF_TIME = 100
FIND_PAIRS_TASK_TIME = 20
SEC_PRED_TASK_TIME = 20
PJF_TIME_PRIMARY = 20
PJF_TIME_SECONDARY = 20


#______ Miscellany ___________#
UPDATE_ON_CONSENSUS = False #decides whether the task statistics are updated for every assignment (false) or after consensus for each task (true)

# Used in the enumeration estimate in chao_estimator(). If the difference between the size of list2 and the size of the 
# estimate is less than this fraction of the size of the estimate then chao_estimator() will return True.
THRESHOLD = 0

