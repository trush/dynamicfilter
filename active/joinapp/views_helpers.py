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



#_____GATHER TASKS_____#

def gather_task(task_type, answer, cost, item1_id = None, item2_id = None):
    if item1_id is None and item2_id is None:
        raise Exception("no item given")

    #call correct helper for the given task_type and collect the result (if we reach consensus)
    if task_type == 0:
        ans = collect_joinable_filter(answer, cost, item1_id)
    elif task_type == 1:
        ans = collect_find_pairs(answer, cost, item1_id)
    elif task_type == 2:
        ans = collect_prejoin_filter(answer, cost, item1_id, item2_id)
    elif task_type == 3:
        ans = collect_secondary_predicate(answer, cost, item2_id)
    else: #if task_type == 4:
        ans = collect_join_pair(answer, cost, item1_id, item2_id)

    #depending on whether we want to update on consensus, we may need to update TaskStats for the relevant type
    if toggles.UPDATE_ON_CONSENSUS and ans is not None:
        task_stats = TaskStats.objects.get(task_type = task_type)
        task_stats.update_stats(cost, answer)
    else:
        task_stats = TaskStats.objects.get(task_type = task_type)
        task_stats.update_stats(cost, answer)


#_____GATHER TASKS HELPERS____#

## Collect joinable filter task
def collect_joinable_filter(answer, cost, item1_id):
    #load primary item from db
    primary_item = PrimaryItem.objects.get(item_id = item1_id)

    #use primary item to find the relevant task
    our_tasks = JFTask.objects.filter(primary_item = primary_item)
    #if we have a joinable filter task with this item, it is our task.
    #otherwise, we must create a new task
    if not our_tasks.exists():
        this_task = JFTask.objects.create(primary_item = primary_item)
    else:
        this_task = JFTask.objects.get(primary_item = primary_item)
    
    #allow model functionality to update its fields accordingly
    this_task.get_task(answer, cost)

    #return the result from this_task for use
    this_task.refresh_from_db()
    return this_task.result()

## Collect find pairs task
def collect_find_pairs(answer, cost, item1_id):
    #load primary item from db
    primary_item = PrimaryItem.objects.get(item_id = item1_id)

    #use primary item to find the relevant task
    our_tasks = FindPairsTask.objects.filter(primary_item = primary_item)
    #if we have a joinable filter task with this item, it is our task.
    #otherwise, we must create a new task
    if not our_tasks.exists():
        this_task = FindPairsTask.objects.create(primary_item = primary_item)
    else:
        this_task = FindPairsTask.objects.get(primary_item = primary_item)

    


## Collect secondary predicate task
def collect_secondary_predicate(answer, cost, item2_id):
    #load secondary item from db
    secondary_item = SecondaryItem.objects.get(item_id = item2_id)

    #use secondary item to find the relevant task
    our_tasks = SecPredTask.objects.filter(secondary_item = secondary_item)
    #if we have a secondary predicate task with this item, it is our task.
    #otherwise, we must create a new task
    if not our_tasks.exists():
        this_task = SecPredTask.objects.create(secondary_item = secondary_item)
    else:
        this_task = SecPredTask.objects.get(secondary_item = secondary_item)
    
    #allow model functionality to update its fields accordingly
    this_task.get_task(answer, cost)

    #return the result from this_task for use
    this_task.refresh_from_db()
    return this_task.result()

## Collect Join Pair task
def collect_join_pair(answer, cost, item1_id, item2_id):
    #load primary item from db
    primary_item = PrimaryItem.objects.get(item_id = item1_id)
    #load secondary item from db
    secondary_item = SecondaryItem.objects.get(item_id = item2_id)

    #use primary item to find the relevant task
    our_tasks = JoinPairTask.objects.filter(primary_item = primary_item, secondary_item = secondary_item)
    #if we have a join pair task with these items, it is our task.
    #otherwise, we must create a new task
    if not our_tasks.exists():
        this_task = JoinPairTask.objects.create(primary_item = primary_item, secondary_item = secondary_item)
    else:
        this_task = JoinPairTask.objects.get(primary_item = primary_item, secondary_item = secondary_item)
    
    #allow model functionality to update its fields accordingly
    this_task.get_task(answer, cost)

    #return the result from this_task for use
    this_task.refresh_from_db()
    return this_task.result()

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

