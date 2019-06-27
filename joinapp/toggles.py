import math

#________ Path Info __________#
PRIMARY_LIST = ''#TODO hotel list
REAL_DATA_CSV = '/simulation_files/CLEANED_ROUND1.csv'#TODO MTURK data CSV

#_____________________________ For Synthetic Data _____________________________#
NUM_PRIM_ITEMS = 20
NUM_SEC_ITEMS = 20
HAVE_SEC_LIST = False #Do we start with the secondary list populated yes/no 
FAKE_SEC_ITEM_LIST = [str(NUM_SEC_ITEMS+1), str(NUM_SEC_ITEMS+2), str(NUM_SEC_ITEMS+3), str(NUM_SEC_ITEMS+4), str(NUM_SEC_ITEMS+5), str(NUM_SEC_ITEMS+6), str(NUM_SEC_ITEMS+7), str(NUM_SEC_ITEMS+8), str(NUM_SEC_ITEMS+9), str(NUM_SEC_ITEMS+10)] #fake secondary items to choose from
PJF_LIST = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]

#__________________________ For Consensus Exploration__________________#
CHANCE_FEWER_THAN_HALF = 0.5 #< NOT IN USE CURRENTLY
CHANCE_MORE_THAN_7 = 0.3
CROWD_RESPONSES = [0,0,0.25,0,0.25,0.75,1,0.25,0,0.6,0.2,1,1,0.8,0,0,1,0.6,0.7,0,0.3,1,0.5,0.3,0,0.1,0.6,0,0,0.25,0,0.25,1,0,0.75,0.25,0.25,0,0,0.5,1,0.25,0,0.25,0]
YES_VOTES_THRESHOLD = 5
NO_VOTES_THRESHOLD = 15
YES_VOTES_FRACTION = 0.33
NO_VOTES_FRACTION = 0.66

# used in syn_load_find_pairs_tasks
# to determine how many secondary items each primary item is going to be matched with 
MEAN_SEC_PER_PRIM = 4
SD_SEC_PER_PRIM = 0
PROB_NONE_SECONDARY = 0.25


#________ For Real Data ________#
INPUT_PATH = ''
PRIMARY_ITEM_TYPE = "Hotel"  # "Hotel" or "Restaurant"

#________ Simulation Settings ________#
REAL_DATA = False # real or synthetic data
# 0 = joinable filter
# 1 = item-wise join
# 2 = pre-join filtered join
JOIN_TYPE = 2
NUM_WORKERS = 1000 # number of distinct workers
NUM_SIMS = 15 # number of simulations to run
PROB_CHOOSING_TRUE_SEC_ITEM = 1
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
JF_AMBIGUITY = 0.5
JF_SELECTIVITY = 0.1
SEC_PRED_SELECTIVITY = 0.5
SEC_PRED_AMBIGUITY = 0
JOIN_COND_AMBIGUITY = 0
JOIN_COND_SELECTIVITY = 0.5 # given that these pairs were created by the crowd
PJF_AMBIGUITY = 0
JP_SELECTIVITY_W_PJF = 0.5 #likelyhood of being a pair given that they are in the same PJF

#__________________ Time Settings _____________________#
JF_TASK_TIME_MEAN = 100
JF_TASK_TIME_SD = 5
FIND_PAIRS_TASK_TIME_MEAN = 20
FIND_PAIRS_TASK_TIME_SD = 3
SEC_PRED_TASK_TIME_MEAN = 20
SEC_PRED_TASK_TIME_SD = 3
PJF_TIME_MEAN = 20
PJF_TIME_SD = 3
JOIN_PAIRS_TIME_MEAN = 20
JOIN_PAIRS_TIME_SD = 3


#______ Miscellany ___________#
# Used in the enumeration estimate in chao_estimator(). If the difference between the size of list2 and the size of the 
# estimated number is less than this fraction of the size of the estimate then chao_estimator() will return True.
THRESHOLD = 0.1

#_________Task Settings___________#
SEC_INFLUENTIAL = True
