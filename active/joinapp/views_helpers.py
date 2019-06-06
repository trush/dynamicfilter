import toggles
import models

from scipy.special import btdtr




#_____FIND CONSENSUS_____#


def find_consensus(item):
    #NOTE: Toggles needed

    if item.yes_votes + item.no_votes < toggles.NUM_CERTAIN_VOTES:
        item.ambiguity = "No Consensus"
        return None
    votes_cast = item.yes_votes + item.no_votes
    larger = max(item.yes_votes, item.no_votes)
    smaller = min(item.yes_votes, item.no_votes)
    single_max = toggles.SINGLE_VOTE_CUTOFF
    uncert_level = 2

    if toggles.BAYES_ENABLED:
        if item.yes_votes - item.no_votes > 0:
            uncert_level = btdtr(item.yes_votes+1, item.no_votes+1, toggles.DECISION_THRESHOLD)
        else:
            uncert_level = btdtr(item.no_votes+1, item.yes_votes+1, toggles.DECISION_THRESHOLD)
    #print("Uncertainty: " + str(uncertLevel))

    consensus = (larger == item.yes_votes)

    if votes_cast >= toggles.CUT_OFF:
        item.ambiguity = "Most Ambiguity"
        return consensus

    elif uncert_level < toggles.UNCERTAINTY_THRESHOLD:
        item.ambiguity = "Unambiguous"
        return consensus

    elif larger >= single_max:
        if smaller < single_max*(1.0/3.0):
            item.ambiguity = "Unambiguous+"
        elif smaller < single_max*(2.0/3.0):
            item.ambiguity = "Medium Ambiguity"
        else:
            item.ambiguity = "Low Ambiguity"
        return consensus
    else:
        item.ambiguity = "No Consensus"
        return None    




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

