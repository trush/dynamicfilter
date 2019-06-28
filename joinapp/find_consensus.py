import toggles

from scipy.special import btdtr
"""
#_____FIND CONSENSUS_____#

## @brief determines if an task has reached consensus or not (and what that consensus is)
#   @param item task that needs to be evaluated for consensus
def find_consensus(item):
    if item.yes_votes + item.no_votes < toggles.NUM_CERTAIN_VOTES:
        #item.ambiguity = "No Consensus"
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
        # item.ambiguity = "Most Ambiguity"
        return consensus

    elif uncert_level < toggles.UNCERTAINTY_THRESHOLD:
        # item.ambiguity = "Unambiguous"
        return consensus

    elif larger >= single_max:
        # if smaller < single_max*(1.0/3.0):
        #     item.ambiguity = "Unambiguous+"
        # elif smaller < single_max*(2.0/3.0):
        #     item.ambiguity = "Medium Ambiguity"
        # else:
        #     item.ambiguity = "Low Ambiguity"
        return consensus
    else:
        # item.ambiguity = "No Consensus"
        return None    


#_________________________ VOTE THRESHOLD FIND CONSENSUS _________________________#
def find_consensus(item):
    if item.yes_votes >= toggles.YES_VOTES_THRESHOLD:
        consensus = True
    elif item.no_votes >= toggles.NO_VOTES_THRESHOLD:
        consensus = False
    else:
        consensus = None
    return consensus


"""
#_________________________ VOTE FRACTION FIND CONSENSUS _________________________#
def find_consensus(item):
    if item.yes_votes + item.no_votes >= 15:
        yes = float(item.yes_votes)/float(item.yes_votes + item.no_votes)
        no = float(item.no_votes)/float(item.no_votes + item.yes_votes)
        if yes >= toggles.YES_VOTES_FRACTION:
            consensus = True
        elif no >= toggles.NO_VOTES_FRACTION:
            consensus = False
        else:
            consensus = None
        return consensus
    else:
        return None
