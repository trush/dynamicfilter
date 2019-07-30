import math

#________ Path Info For Real Data__________#
## paths for real data
PRIMARY_LIST = './simulation_files/Hotel_items.csv'
REAL_DATA_JF = './simulation_files/JOINABLE_FILTER_RESULTS.csv'
REAL_DATA_SEC_PRED = './simulation_files/SECOND_PRED_RESULTS.csv'
REAL_DATA_FP = './simulation_files/FIND_PAIRS_RESULTS.csv'

#_____________________________ For Synthetic Data _____________________________#
NUM_PRIM_ITEMS = 100
NUM_SEC_ITEMS = 50
## we set this depending on what join path the sim is running
HAVE_SEC_LIST = False #Do we start with the secondary list populated yes/no 
## list of tuples of prejoin filters and the percent of items that have that pjf
PJF_LIST = [("0",0.20), ("1",0.20), ("2",0.20), ("3",0.20),("4",0.20)]

#_________________ For The Crowd _________________#
## the worker gives a random percent between floor ambiguity and 1 of all the items in a find pairs task
FLOOR_AMBIGUITY_FIND_PAIRS = 0.95

#________ Simulation Settings ________#
REAL_DATA = False # real or synthetic data
## float representing the join path that our simulation is running
# 0 = joinable filter
# 1 = item-wise join (all-items then sec preds) (breadth-first)
# 1.1 = item-wise join (item-by-item) (depth-first)
# 2 = pre-join filtered join
# 2.1 = pre-join filtered join starting with 2nd list
# 2.2 = pre-join filtered join starting with 2nd list - secondary predicates first
# 2.3 = pre-join filtered join - secondary predicates first
# 3.1 = item-wise join on second list (all sec preds then find pairs) (breadth-first)
# 3.2 = item-wise join on second list (all find pairs then sec preds)
# 3.3 = item-wise join on second list (item-by-item, sec preds first) (depth-first)
JOIN_TYPE = 3.1
NUM_WORKERS = 200 # number of distinct workers
## number of sims that run_multi_sim() runs
NUM_SIMS = 10 # number of simulations to run
SIMULATE_TIME = False
TIME_STEP = 1
## only for find pairs tasks to finish tasks that have been started before starting a new task
USE_IN_PROGRESS = False

if JOIN_TYPE >= 3 and JOIN_TYPE < 3.5:
    HAVE_SEC_LIST = True

if JOIN_TYPE == 2.1 or JOIN_TYPE == 2.2:
    HAVE_SEC_LIST = True

# ________ Consensus Settings _________#
## Values used in the find_consensus for an item/task function
NUM_CERTAIN_VOTES = 5  # Recommended val: 5 (unless using agressive bayes)
CUT_OFF = 21 #should be an odd number
SINGLE_VOTE_CUTOFF = int(1+math.ceil(CUT_OFF/2.0))
BAYES_ENABLED = True
UNCERTAINTY_THRESHOLD = 0.2
DECISION_THRESHOLD = 0.5

UPDATE_ON_CONSENSUS = False #decides whether the task statistics are updated for every assignment (false) or after consensus for each task (true)


#_______ Selectivity and Ambiguity Settings _________#
## what percent of secondary items pass the secondary predicate
SEC_PRED_SELECTIVITY = 0.3
## likelyhood of being a pair given that they are in the same PJF
JOIN_COND_SELECTIVITY = 0.5 

## how likely it is that a worker will give a random answer instead of the correct answer for each task type
JF_AMBIGUITY = 0
SEC_PRED_AMBIGUITY = 0
JOIN_COND_AMBIGUITY = 0
PJF_AMBIGUITY = 0


#__________________ Time Settings _____________________#
JF_TASK_TIME_MEAN = 200
JF_TASK_TIME_SD = 0

FIND_PAIRS_TASK_TIME_MEAN = 160
FIND_PAIRS_TASK_TIME_SD = 0

SEC_PRED_TASK_TIME_MEAN = 100
SEC_PRED_TASK_TIME_SD = 0

PJF_TIME_MEAN = 80
PJF_TIME_SD = 0

JOIN_PAIRS_TIME_MEAN = 80
JOIN_PAIRS_TIME_SD = 0


#______ Miscellany ___________#
## Used in the enumeration estimate in chao_estimator(). If the difference between the size of list2 and the size of the 
# estimated number is less than this fraction of the size of the estimate then chao_estimator() will return True.
THRESHOLD = 0.1

#_________Task Settings___________#
## Setting where we choose to prioritize evaluating secondary items that match with more primary item matches 
SEC_INFLUENTIAL = True
