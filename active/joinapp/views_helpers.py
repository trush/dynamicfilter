import toggles

from django.db.models.query import EmptyQuerySet

from models.items import *
from models.task_management_models import *


#_______________________ CHOOSE TASKS _______________________#


## @brief chooses the next task to issue based on the state of the query
# @param workerID workerID of the worker this task is going to
# @param estimator the estimator used to determine when the second list is complete
def choose_task(workerID, estimator):
    # only implemented for IW join
    # returns task that was chosen and updated
    new_worker = Worker.objects.get_or_create(worker_id=workerID)[0]
    # if task_type = JF:
        # return choose_task_joinable_filter(new_worker)
    # find pairs for all primary items
    prim_items_left = PrimaryItem.objects.filter(found_all_pairs=False)
    if prim_items_left.exists():
        return choose_task_find_pairs(prim_items_left, new_worker)
    else:
        return choose_task_sec_pred(new_worker)

#_______________________ CHOOSE TASKS HELPERS _______________________#

## @brief chooses a joinable filter task based on a worker
# @param worker workerID of the worker this task is going to
def choose_task_joinable_filter(worker):
    prim_item = PrimaryItem.objects.order_by('?').first() # random primary item
    joinable_filter_task = JFTask.objects.get_or_create(primary_item=prim_item)[0]
    prims_left = PrimaryItem.objects.exclude(pk=prim_item.pk)
    # choose new primary item if the random one has reached consensus or if worker has worked on it
    while joinable_filter_task.result == None or worker in joinable_filter_task.workers:
        prims_left = prims_left.exclude(pk=prim_item.pk)
        prim_item = prims_left.order_by('?').first()
        joinable_filter_task = JFTask.objects.get_or_create(primary_item=prim_item)[0]
    joinable_filter_task.workers.add(worker)
    joinable_filter_task.save()
    return joinable_filter_task

## @brief chooses a find pairs task based on a worker
# @param prim_items_list the current primary list objects available
# @param worker workerID of the worker this task is going to
def choose_task_find_pairs(prim_items_list,worker):
    prim_item = prim_items_list.order_by('?').first() # random primary item
    find_pairs_task = FindPairsTask.objects.get_or_create(primary_item=prim_item)[0]
    prims_left = PrimaryItem.objects.exclude(pk=prim_item.pk)
    # choose new primary item if the random one has reached consensus or if worker has worked on it
    while find_pairs_task.consensus == True: # TODO: implement this: or worker in find_pairs_task.workers.all():
        prims_left = prims_left.exclude(pk=prim_item.pk)
        prim_item = prims_left.order_by('?').first()
        find_pairs_task = FindPairsTask.objects.get_or_create(primary_item=prim_item)[0]
    find_pairs_task.workers.add(worker)
    find_pairs_task.save()
    return find_pairs_task

## @brief chooses a secondary predicate task based on a worker
# @param worker workerID of the worker this task is going to
def choose_task_sec_pred(worker):
    # only secondary items that haven't reached consensus but match at least one primary item
    sec_items_left = SecondaryItem.objects.filter(second_pred_result=None).exclude(matches_some = False)
    sec_item = sec_items_left.order_by('?').first() # random secondary item
    sec_pred_task = SecPredTask.objects.get_or_create(secondary_item=sec_item)[0]
    # choose new secondary item if worker has worked on it
    while worker in sec_pred_task.workers.all():  
        sec_item = sec_items_left.order_by('?').first()
        sec_pred_task = SecPredTask.objects.get_or_create(secondary_item=sec_item)[0]
    sec_pred_task.workers.add(worker)
    sec_pred_task.save()
    return sec_pred_task

#_____ASSIGN TASKS_____#

#_____GATHER TASKS_____#

## @brief Generic gather_task function that updates state after a worker response is recieved
#   @param task_type An integer representing the type of task being recieved
#   @param answer A string or (0,1) representing the worker response
#   @param cost The amount of time it took the worker to complete the hit
def gather_task(task_type, answer, cost, item1_id = None, item2_id = None):
    if item1_id is None and item2_id is None:
        raise Exception("no item given")

    #call correct helper for the given task_type and collect the result (if we reach consensus)
    if task_type == 0:
        finished = collect_joinable_filter(answer, cost, item1_id)
    elif task_type == 1:
        answer = parse_pairs(answer)
        finished = collect_find_pairs(answer, cost, item1_id)
    elif task_type == 2:
        finished = collect_join_pair(answer, cost, item1_id, item2_id)
    elif task_type == 3:
        finished = collect_prejoin_filter(answer, cost, item1_id, item2_id)
    else: #if task_type == 4:
        finished = collect_secondary_predicate(answer, cost, item2_id)

    #depending on whether we want to update on consensus, we may need to update TaskStats for the relevant type
    if toggles.UPDATE_ON_CONSENSUS and finished is not None:
        task_stats = TaskStats.objects.get(task_type = task_type)
        task_stats.update_stats(cost, finished)
    else:
        task_stats = TaskStats.objects.get(task_type = task_type)
        task_stats.update_stats(cost, answer)


#_____GATHER TASKS HELPERS____#

## Collect joinable filter task
def collect_joinable_filter(answer, cost, item1_id):
    #load primary item from db
    primary_item = PrimaryItem.objects.get(pk = item1_id)

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
    return this_task.result

## Collect find pairs task
def collect_find_pairs(answer, cost, item1_id):
    #load primary item from db
    primary_item = PrimaryItem.objects.get(pk = item1_id)

    #use primary item to find the relevant task
    our_tasks = FindPairsTask.objects.filter(primary_item = primary_item)
    #if we have a joinable filter task with this item, it is our task.
    #otherwise, we must create a new task
    if not our_tasks.exists():
        this_task = FindPairsTask.objects.create(primary_item = primary_item)
    else:
        this_task = FindPairsTask.objects.get(primary_item = primary_item)

    #holds the list of secondary item (ids) we get from this task
    sec_items_list = []
    for match in answer:
        #disambiguate matches with strings
        disamb_match = disambiguate_str(match)

        #find or create a secondary item that matches this name
        known_sec_items = SecondaryItem.objects.filter(name = disamb_match)
        if known_sec_items.exists():
            this_sec_item = SecondaryItem.objects.get(name = disamb_match)
        else:
            this_sec_item = SecondaryItem.objects.create(name = disamb_match)
        sec_items_list.append(this_sec_item.id)

    #call the model's function to update its state
    this_task.get_task(sec_items_list, cost)

    return this_task.consensus

## takes a string of entries (separated by the string {{NEWENTRY}}) for find_pairs and parses them
def parse_pairs(pairs):
    if pairs is None or pairs is "":
        return []
    else:
        processed = []
        for match in pairs.strip("{{NEWENTRY}}").split("{{NEWENTRY}}"):
            temp = match.strip()
            temp = temp.lower()
            processed.append(temp)
        return processed

## turns string responses into unique identifying strings
#NOTE: this function is specific to our example (hotels and restaurants)
# new functions must be written for different queries
def disambiguate_str(sec_item_str):
    #we want the first 4 non-whitespace characters after the semicolon
    semicol_pos = sec_item_str.rfind(';')
    addr = sec_item_str[semicol_pos+1:].strip()
    for i in range(len(addr)):
        if addr[i].isspace():
            addr = addr[:i]
            break
    return addr
    
## Collect Join Pair task
def collect_join_pair(answer, cost, item1_id, item2_id):
    #load primary item from db
    primary_item = PrimaryItem.objects.get(pk = item1_id)
    #load secondary item from db
    secondary_item = SecondaryItem.objects.get(pk = item2_id)

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
    return this_task.result

## Collect Prejoin Filter task
def collect_prejoin_filter(answer, cost, item1_id=None, item2_id=None):
    #I don't know
    return True

## Collect secondary predicate task
def collect_secondary_predicate(answer, cost, item2_id):
    #load secondary item from db
    secondary_item = SecondaryItem.objects.get(pk = item2_id)

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
    return this_task.result


