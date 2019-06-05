import toggles
import models

from scipy.special import btdtr

def find_consensus(item):
    #NOTE: Toggles needed

    if item.yes_votes + item.no_votes < toggles.NUM_CERTAIN_VOTES:
        item.second_pred_consensus = None
        item.ambiguity = "No Consensus"
        return None
    votes_cast = item.yes_votes + item.no_votes
    larger = max(item.yes_votes, item.no_votes)
    smaller = min(item.yes_votes, item.no_votes)
    single_max = int(1+math.ceil(toggles.CUT_OFF/2.0))
    uncert_level = 2

    if toggles.BAYES_ENABLED:
        if item.yes_votes - votes_no > 0:
            uncert_level = btdtr(item.yes_votes+1, item.no_votes+1, toggles.DECISION_THRESHOLD)
        else:
            uncert_level = btdtr(item.no_votes+1, item.yes_votes+1, toggles.DECISION_THRESHOLD)
    #print("Uncertainty: " + str(uncertLevel))

    consensus = (larger == item.yes_votes)

    if votes_cast >= toggles.CUT_OFF:
        item.second_pred_consensus = consensus
        item.ambiguity = "Most Ambiguity"
        return consensus

    elif uncertLevel < toggles.UNCERTAINTY_THRESHOLD:
        item.second_pred_consensus = consensus
        item.ambiguity = "Unambiguous"
        return consensus

    elif larger >= single_max:
        if smaller < single_max*(1.0/3.0):
            item.ambiguity = "Unambiguous+"
        elif smaller < single_max*(2.0/3.0):
            item.ambiguity = "Medium Ambiguity"
        else:
            item.ambiguity = "Low Ambiguity"
        item.second_pred_consensus = consensus
        return consensus
    else:
        item.second_pred_consensus = None
        item.ambiguity = "No Consensus"
        return None    