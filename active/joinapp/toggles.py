### Settings for test_simulations ###





#________ For Synthetic Data _________#
NUM_PRIMARY_LIST = 90
NUM_SECONDARY_LIST = 1000
MEAN_PRIMARY_PER_SECONDARY = 5
SD_PRIMARY_PER_SECONDARY = 2.58



#________ For Real Data ________#
INPUT_PATH = ''
PRIMARY_ITEM_TYPE = "Hotel"       # "Hotel" or "Restaurant"
ITEM_ITEM_DATA_FILE = ''

#________ Simmulation Settings ________#
REAL_DATA = True
# 0 = joinable filter
# 1 = item-wise join
# 2 = pre-join filtered join
JOIN_TYPE = 0 

#_______ Joinable Filter Specific Toggles _______#
JF_TIME = 100


#_______ Item-wise Join Specific Toggles _______#
IW_ENUMERATION_TIME = 20
IW_SECONDARY_PRED_TIME = 20
SECONDARY_PRED_SELECTIVITY = 0.1
SECONDARY_PRED_AMBIGUITY = 0.1
JOIN_COND_AMBIGUITY = 0.1



#_______ PJF specific toggles _______#
PJF_SELECTIVITY_PRIMARY = 0.1
PJF_SELECTIVITY_SECONDARY = 0.1
PJF_AMBIGUITY_PRIMARY = 0.1
PJF_AMBIGUITY_SECONDARY = 0.1
PJF_TIME_PRIMARY = 20
PJF_TIME_SECONDARY = 20


