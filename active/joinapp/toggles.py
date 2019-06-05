### Settings for test_simulations ###





#________ For Synthetic Data _________#
NUM_PRIM_ITEMS = 90
NUM_SEC_ITEMS = 1000

#toggles whether or not we want to generate all possible PS pairs:
ALL_PS_PAIRS = False
#to determine how many primary items each secondary item is going to be matched with:
MEAN_PRIM_PER_SEC = 20
SD_PRIM_PER_SEC = 4
SAMPLE_W_REPLACE_NUM_PRIM = False




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
JF_AMBIGUITY = 0.1
JF_SELECTIVITY = 0.1


#_______ Item-wise Join Specific Toggles _______#
IW_ENUMERATION_TIME = 20
IW_SECONDARY_PRED_TIME = 20
SEC_PRED_SELECTIVITY = 0.1
SEC_PRED_AMBIGUITY = 0.1
JOIN_COND_AMBIGUITY = 0.1



#_______ PJF specific toggles _______#
PJF_SELECTIVITY_PRIMARY = 0.1
PJF_SELECTIVITY_SECONDARY = 0.1
PJF_AMBIGUITY_PRIMARY = 0.1
PJF_AMBIGUITY_SECONDARY = 0.1
PJF_TIME_PRIMARY = 20
PJF_TIME_SECONDARY = 20


