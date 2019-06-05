from models import *
import toggles



#_____GIVE TASKS_____#

## Function that gives tasks to workers
# @param workerID The ID for the worker that is being assigned a task

# choosing a task

# for joinable filters
# task:
# give a primary item that hasn't reached consensus
# ask for an answer y/n

# for itemwise join
# task:
# give a primary item and ask for all the associated secondary items

# if second list is complete
# then make pairs of primary and secondary list items (make and store these somewhere else?)
# task:
# give a secondary item that hasn't reached consensus and filter w secondary predicate

# if consensus on secondary predicate for all secondary items
# secondary item that pass which have highest # of num_prim_items chosen first
# task:
# primary item w/ relation to that secondary item 
# mark true if secondary predicate true
# delete relation if secondary predicate false

# for prejoin filters
# task:
# give a primary item
# ask for prejoin filter

# task:
# 1st task from IW join

# if primary list done for PJ filter
# task:
# give a secondary item
# ask for prejoin filter

# if both are completed
# 2nd and 3rd tasks from IW join





#_____FIND CONSENSUS_____#

