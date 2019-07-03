import math

#________ Path Info For Real Data__________#
PRIMARY_LIST = './simulation_files/Hotel_items.csv'
REAL_DATA_JF = './simulation_files/JOINABLE_FILTER_RESULTS.csv'#TODO MTURK data CSV
REAL_DATA_SEC_PRED = './simulation_files/SECOND_PRED_RESULTS.csv'
REAL_DATA_FP = './simulation_files/FIND_PAIRS_RESULTS.csv'

#_____________________________ For Synthetic Data _____________________________#
NUM_PRIM_ITEMS = 100
NUM_SEC_ITEMS = 50
HAVE_SEC_LIST = False #Do we start with the secondary list populated yes/no 
PJF_LIST = [("0",0.20), ("1",0.20), ("2",0.20), ("3",0.20),("4",0.20)]

#_________________ For The Crowd _________________#
FLOOR_AMBIGUITY_FIND_PAIRS = 0.80

#________ Simulation Settings ________#
REAL_DATA = False # real or synthetic data
# 0 = joinable filter
# 1 = item-wise join
# 2 = pre-join filtered join
JOIN_TYPE = 1
PATH_NUM = 1
NUM_WORKERS = 200 # number of distinct workers
NUM_SIMS = 10 # number of simulations to run
SIMULATE_TIME = False
TIME_STEP = 1

# ________ Consensus Settings _________#
# Values used in the find_consensus for an item/task function
NUM_CERTAIN_VOTES = 5  # Recommended val: 5 (unless using agressive bayes)
CUT_OFF = 21 #should be an odd number
SINGLE_VOTE_CUTOFF = int(1+math.ceil(CUT_OFF/2.0))
BAYES_ENABLED = True
UNCERTAINTY_THRESHOLD = 0.2
DECISION_THRESHOLD = 0.5

UPDATE_ON_CONSENSUS = False #decides whether the task statistics are updated for every assignment (false) or after consensus for each task (true)


#_______ Selectivity and Ambiguity Settings _________#
SEC_PRED_SELECTIVITY = 0.3
JOIN_COND_SELECTIVITY = 0.9 #likelyhood of being a pair given that they are in the same PJF

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
# Used in the enumeration estimate in chao_estimator(). If the difference between the size of list2 and the size of the 
# estimated number is less than this fraction of the size of the estimate then chao_estimator() will return True.
THRESHOLD = 0.1

#_________Task Settings___________#
SEC_INFLUENTIAL = True
