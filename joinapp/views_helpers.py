import toggles
import random
from django.db.models.query import EmptyQuerySet

from models.items import *
from models.task_management_models import *


#_______________________ CHOOSE TASKS _______________________#

## @brief chooses the next task to issue for a joinable filter query
# @param workerID workerID of the worker this task is going to
def choose_task_JF(workerID):
    new_worker = Worker.objects.get_or_create(worker_id=workerID)[0]
    return choose_task_joinable_filter_helper(new_worker)

## @brief chooses the next task to issue for an item-wise join where all 
## find pairs tasks are evaluated first, then secondary predicate tasks
# @param workerID workerID of the worker this task is going to
# @param estimator the estimator used to determine when the second list is complete
def choose_task_IW(workerID, estimator):
    # returns task that was chosen and updated
    new_worker = Worker.objects.get_or_create(worker_id=workerID)[0]
    # find all pairs for all primary items
    prim_items_left = PrimaryItem.objects.filter(found_all_pairs=False)
    if prim_items_left.exists():
        return choose_task_find_pairs(prim_items_left, new_worker, 1)
    # then evaluate second predicate for found secondary items
    else:
        return choose_task_sec_pred(new_worker)

## @brief chooses the next task to issue for an item-wise join where one
## find pairs task is evaluated first, then a secondary predicate task (item by item)
# @param workerID workerID of the worker this task is going to
# @param estimator the estimator used to determine when the second list is complete
def choose_task_IW1(workerID, estimator):
    new_worker = Worker.objects.get_or_create(worker_id=workerID)[0]
    prim_has_sec = PrimaryItem.objects.exclude(is_done=True).filter(found_all_pairs=True)
    if prim_has_sec.exists():        
        return choose_task_sec_pred(new_worker)
        # finds pairs for one primary item
    prim_items_left = PrimaryItem.objects.filter(found_all_pairs=False).exclude(is_done=True)
    if prim_items_left.exists():
        return choose_task_find_pairs(prim_items_left, new_worker, 1)
        
## Finds all pairs, then chooses a primary item then evaluates all secondary predicates related to that item
## Then chooses another primary item (that has not yet passed the query) then repeats
def choose_task_IW2(workerID, estimator):
    new_worker = Worker.objects.get_or_create(worker_id=workerID)[0]
    prim_items_left = PrimaryItem.objects.filter(found_all_pairs=False).filter(is_done = False)
    if prim_items_left.exists():
        return choose_task_find_pairs(prim_items_left, new_worker, 1)
    else:
        prim_item = PrimaryItem.objects.filter(is_done=False).order_by('?').first()
        return choose_task_sec_pred_by_prim(new_worker,prim_item)

## Itemwise join on secondary list - all sec preds then find pairs on trues
def choose_task_IWS1(workerID, estimator):
    new_worker = Worker.objects.get_or_create(worker_id=workerID)[0]

    sec_left = SecondaryItem.objects.filter(second_pred_result=None)
    if sec_left.exists():
        return choose_task_sec_pred_before_pairs(new_worker)
    else:
        true_secs = SecondaryItem.objects.filter(second_pred_result=True)
        return choose_task_find_pairs(true_secs, new_worker, 2)

## Itemwise join on secondary list - all find pairs then secondary preds
def choose_task_IWS2(workerID, estimator):
    new_worker = Worker.objects.get_or_create(worker_id=workerID)[0]
    sec_items_need_pairs = SecondaryItem.objects.filter(found_all_pairs=False)

    if sec_items_need_pairs.exists():
        return choose_task_find_pairs(sec_items_need_pairs, new_worker, 2)

    elif PrimaryItem.objects.filter(found_all_pairs=False).exists():
        for prim in PrimaryItem.objects.all():
            prim.refresh_from_db()
            prim.found_all_pairs = True
            prim.update_state()
            prim.save()
        return choose_task_sec_pred(new_worker)
    else:
        return choose_task_sec_pred(new_worker)


## Itemwise join on secondary list - sec pred by sec pred
def choose_task_IWS3(workerID, estimator):
    new_worker = Worker.objects.get_or_create(worker_id=workerID)[0]

    true_secs_to_do = SecondaryItem.objects.filter(second_pred_result=True).filter(found_all_pairs=False)
    if true_secs_to_do.exists():
        return choose_task_find_pairs(true_secs_to_do, new_worker, 2)
    else:
        return choose_task_sec_pred_before_pairs(new_worker)

## Itemwise join on secondary list - all sec preds then find pairs on trues WITHOUT SECOND LIST
def choose_task_IWS5(workerID, estimator):
    new_worker = Worker.objects.get_or_create(worker_id=workerID)[0]
    
    if not estimator.has_2nd_list:
        prim_items_left = PrimaryItem.objects.filter(found_all_pairs=False)
        return choose_task_find_pairs(prim_items_left, new_worker, 1)

    sec_left = SecondaryItem.objects.filter(second_pred_result=None)
    if sec_left.exists():
        return choose_task_sec_pred_before_pairs(new_worker)
    else:
        true_secs = SecondaryItem.objects.filter(second_pred_result=True)
        return choose_task_find_pairs(true_secs, new_worker, 2)

## Itemwise join on secondary list - all find pairs then secondary preds WITHOUT SECOND LIST
def choose_task_IWS6(workerID, estimator):
    new_worker = Worker.objects.get_or_create(worker_id=workerID)[0]

    if not estimator.has_2nd_list:
        prim_items_left = PrimaryItem.objects.filter(found_all_pairs=False)
        return choose_task_find_pairs(prim_items_left, new_worker, 1)

    sec_items_need_pairs = SecondaryItem.objects.filter(found_all_pairs=False)

    if sec_items_need_pairs.exists():
        return choose_task_find_pairs(sec_items_need_pairs, new_worker, 2)

    elif PrimaryItem.objects.filter(found_all_pairs=False).exists():
        for prim in PrimaryItem.objects.all():
            prim.refresh_from_db()
            prim.found_all_pairs = True
            prim.update_state()
            prim.save()
        return choose_task_sec_pred(new_worker)
    else:
        return choose_task_sec_pred(new_worker)


## Itemwise join on secondary list - sec pred by sec pred WITHOUT SECOND LIST
def choose_task_IWS7(workerID, estimator):
    
    new_worker = Worker.objects.get_or_create(worker_id=workerID)[0]

    if not estimator.has_2nd_list:
        prim_items_left = PrimaryItem.objects.filter(found_all_pairs=False)
        return choose_task_find_pairs(prim_items_left, new_worker, 1)
        
    true_secs_to_do = SecondaryItem.objects.filter(second_pred_result=True).filter(found_all_pairs=False)
    if true_secs_to_do.exists():
        return choose_task_find_pairs(true_secs_to_do, new_worker, 2)
    else:
        return choose_task_sec_pred_before_pairs(new_worker)






## @brief chooses the next task to issue for a pre-join filter join
# @param workerID workerID of the worker this task is going to
# @param estimator the estimator used to determine when the second list is complete
def choose_task_PJF(workerID, estimator):
    new_worker = Worker.objects.get_or_create(worker_id=workerID)[0]
    if not estimator.has_2nd_list:
        prim_items_left = PrimaryItem.objects.filter(found_all_pairs=False)
        return choose_task_find_pairs(prim_items_left, new_worker, 1)

    elif PrimaryItem.objects.filter(pjf='false').exists() or SecondaryItem.objects.filter(pjf='false').exists():
        return choose_task_pjf_helper(new_worker)

    elif PrimaryItem.objects.filter(found_all_pairs=False).exists():
        return choose_task_join_pairs(new_worker)

    else:
        return choose_task_sec_pred(new_worker)

## @brief chooses the next task to issue for a pre-join filter join w/ secondary predicates first
# @param workerID workerID of the worker this task is going to
# @param estimator the estimator used to determine when the second list is complete
def choose_task_PJF2(workerID, estimator):
    new_worker = Worker.objects.get_or_create(worker_id=workerID)[0]
    #for join type 2.3: when we don't start w the secondary list
    if not estimator.has_2nd_list:
        prim_items_left = PrimaryItem.objects.filter(found_all_pairs = False)
        return choose_task_find_pairs(prim_items_left, new_worker, 1)
    #first do secondary predicate tasks
    elif SecondaryItem.objects.exclude(second_pred_result = False).exclude(second_pred_result = True).exists(): #all unevaluated secondary predicate tasks
        return choose_task_sec_pred_before_pairs(new_worker)
    #then do pre-join filters
    elif SecondaryItem.objects.filter(second_pred_result = True).filter(pjf = 'false').exists() or PrimaryItem.objects.filter(pjf = 'false').exists(): #unfinished pjfs
        return choose_task_pjf_helper(new_worker)
    #then do join pairs tasks
    elif PrimaryItem.objects.filter(found_all_pairs = False).exists():
        return choose_task_join_pairs2(new_worker)
    else:
        print "******************************** WHY ARE YOU HERE??? ********************************"


    
    
#_______________________ CHOOSE TASKS HELPERS _______________________#

## @brief chooses a pre join filter task based on a worker
# @param worker workerID of the worker this task is going to
def choose_task_pjf_helper(worker):
    # first does all primary item pjf tasks
    prim_items_left = PrimaryItem.objects.filter(pjf='false')
    if prim_items_left.exists():
        prim_item = prim_items_left.order_by('?').first() # random primary item
        pjf_task = PJFTask.objects.get_or_create(primary_item=prim_item)[0]
    # secondary item pjf tasks
    else:
        if toggles.JOIN_TYPE == 2.2: #TODO TOGGLES
            sec_items_left = SecondaryItem.objects.filter(pjf='false').filter(second_pred_result = True)
        else:
            sec_items_left = SecondaryItem.objects.filter(pjf='false')
        sec_item = sec_items_left.order_by('?').first() # random secondary item
        pjf_task = PJFTask.objects.get_or_create(secondary_item=sec_item)[0]
    pjf_task.workers.add(worker)
    pjf_task.save()
    return pjf_task

## @brief chooses a joinable filter task based on a worker
# @param worker workerID of the worker this task is going to
def choose_task_joinable_filter_helper(worker):
    prim_items_left = PrimaryItem.objects.exclude(is_done = True).order_by('?')
    prim_items_left_count = prim_items_left.count()
    print_statement = " - WHY WAS THIS TASK ISSUED" #for determining if weird useless tasks are issued
    while prim_items_left_count is not 0: #choose current primary item
        prim_item = prim_items_left.first() # random primary item
        joinable_filter_task = JFTask.objects.get_or_create(primary_item=prim_item)[0]
        if worker not in joinable_filter_task.workers.all():
            joinable_filter_task.workers.add(worker)
            joinable_filter_task.save()
            return joinable_filter_task
        else:
            prim_items_left.exclude(pk = prim_item.pk)
            prim_items_left_count -= 1
            print_statement = "" #for overriding the previous setting
    print "useless joinable filter task issued" + print_statement
    prim_item = PrimaryItem.objects.order_by('?').first()
    joinable_filter_task = JFTask.objects.get_or_create(primary_item=prim_item)[0]
    joinable_filter_task.workers.add(worker)
    joinable_filter_task.save()
    return joinable_filter_task


## @brief chooses a find pairs task based on a worker
# @param prim_items_list the current primary list objects available
# @param worker workerID of the worker this task is going to
def choose_task_find_pairs(items_list,worker, find_pairs_type):
    #TODO: Toggle for in_progress if-statement?
    #NOTE: IF WE DON"T WANT IN PROGRESS FOR FIND PAIRS, COMMENT OUT IF STATEMENT
    #      AND HAVE THE FUNCTION JUST BE WHAT"S INSIDE THE ELSE STATEMENT AND THE STUFF AFTER6
    if toggles.USE_IN_PROGRESS and FindPairsTask.objects.filter(in_progress=True).exists():
        #Possible bugs with concurrency (multiple tasks in progress)
        find_pairs_task = FindPairsTask.objects.get(in_progress=True)
    else:
        if find_pairs_type is 1:
            prim_item = items_list.order_by('?').first() # random primary item
            find_pairs_task = FindPairsTask.objects.get_or_create(primary_item=prim_item)[0]

            # choose new primary item if the random one has reached consensus or if worker has worked on it
            prims_left = items_list
            while find_pairs_task.consensus == True: # TODO: implement this: or worker in find_pairs_task.workers.all():
                prims_left = prims_left.exclude(pk=prim_item.pk)
                prim_item = prims_left.order_by('?').first()
                find_pairs_task = FindPairsTask.objects.get_or_create(primary_item=prim_item)[0]
        elif find_pairs_type is 2:
            sec_item = items_list.order_by('?').first()
            find_pairs_task = FindPairsTask.objects.get_or_create(secondary_item=sec_item)[0]

            secs_left = items_list
            while find_pairs_task.consensus == True: # TODO: implement this: or worker in find_pairs_task.workers.all():
                secs_left = secs_left.exclude(pk=sec_item.pk)
                sec_item = secs_left.order_by('?').first()
                find_pairs_task = FindPairsTask.objects.get_or_create(secondary_item=sec_item)[0]
        find_pairs_task.workers.add(worker)
        find_pairs_task.save()
        return find_pairs_task

## @brief chooses a join pair task based on a worker
# @param worker workerID of the worker this task is going to
# @param pjfs a list of strings representing prejoin filters
def choose_task_join_pairs(worker):
    prim_item = PrimaryItem.objects.filter(found_all_pairs=False).order_by('?').first() # random primary item
    sec_items = SecondaryItem.objects.filter(pjf=prim_item.pjf) # associated secondary items
    while not sec_items.exists(): # if this primary item has no associated secondary items
        prim_item.refresh_from_db() # update primary item accordingly
        prim_item.found_all_pairs = True
        prim_item.has_all_join_pairs = True
        prim_item.eval_result = False
        prim_item.is_done = True
        prim_item.save()
        prim_item.refresh_from_db()
        prim_item = PrimaryItem.objects.filter(found_all_pairs=False).order_by('?').first() # random primary item
        # if the last primary item has no pairs we issue a random placeholder task
        if prim_item is None:
            print "issuing placeholder task"
            prim_item = PrimaryItem.objects.all().order_by('?').first()
            sec_item = SecondaryItem.objects.all().order_by('?').first()
            join_pair_task = JoinPairTask.objects.get_or_create(primary_item=prim_item,secondary_item=sec_item)[0]
            return join_pair_task
        sec_items = SecondaryItem.objects.filter(pjf=prim_item.pjf) # associated secondary items
    sec_item = sec_items.order_by('?').first()
    join_pair_task = JoinPairTask.objects.filter(primary_item=prim_item).filter(secondary_item=sec_item)
    # set has_same_pjf to true in case join pairs task was created in find pairs
    if join_pair_task.exists():
        if join_pair_task.count() > 1:
            print "more than one:"
            for task in join_pair_task:
                print task.primary_item, task.secondary_item, task.find_pairs_task, task.result, task.has_same_pjf, task.yes_votes, task.no_votes
        join_pair_task = JoinPairTask.objects.get(primary_item=prim_item,secondary_item=sec_item)
        join_pair_task.has_same_pjf = True
        join_pair_task.save()
    else:
        join_pair_task = JoinPairTask.objects.create(primary_item=prim_item,secondary_item=sec_item,has_same_pjf=True)
    sec_items = sec_items.exclude(name=sec_item.name)
    # if the task has reached consensus, choose another random one
    while join_pair_task.result is not None:
        sec_item = sec_items.order_by('?').first()
        sec_items = sec_items.exclude(name=sec_item.name)
        join_pair_task = JoinPairTask.objects.filter(primary_item=prim_item).filter(secondary_item=sec_item)
        # set has_same_pjf to true in case join pairs task was created in find pairs
        if join_pair_task.exists():
            join_pair_task = JoinPairTask.objects.get(primary_item=prim_item,secondary_item=sec_item)
            join_pair_task.has_same_pjf = True
            join_pair_task.save()
        else:
            join_pair_task = JoinPairTask.objects.create(primary_item=prim_item,secondary_item=sec_item,has_same_pjf=True)
    join_pair_task.workers.add(worker)
    join_pair_task.save()
    return join_pair_task
        
## @brief chooses a join pair task based on a worker
# @param worker workerID of the worker this task is going to
# @param pjfs a list of strings representing prejoin filters
def choose_task_join_pairs2(worker):
    prim_item = PrimaryItem.objects.filter(found_all_pairs=False).order_by('?').first() # random primary item
    sec_items = SecondaryItem.objects.filter(pjf=prim_item.pjf).filter(second_pred_result = True) # associated secondary items
    while not sec_items.exists(): # if this primary item has no associated secondary items
        prim_item.refresh_from_db() # update primary item accordingly
        prim_item.found_all_pairs = True
        prim_item.has_all_join_pairs = True
        prim_item.eval_result = False
        prim_item.is_done = True
        prim_item.save()
        prim_item.refresh_from_db()
        prim_item = PrimaryItem.objects.filter(found_all_pairs=False).order_by('?').first() # random primary item
        # if the last primary item has no pairs we issue a random placeholder task
        if prim_item is None:
            print "issuing placeholder task"
            prim_item = PrimaryItem.objects.all().order_by('?').first()
            sec_item = SecondaryItem.objects.all().order_by('?').first()
            join_pair_task = JoinPairTask.objects.get_or_create(primary_item=prim_item,secondary_item=sec_item)[0]
            return join_pair_task
        sec_items = SecondaryItem.objects.filter(pjf=prim_item.pjf).filter(second_pred_result = True) # associated secondary items
    sec_item = sec_items.order_by('?').first()
    join_pair_task = JoinPairTask.objects.filter(primary_item=prim_item).filter(secondary_item=sec_item)
    # set has_same_pjf to true in case join pairs task was created in find pairs
    if join_pair_task.exists():
        if join_pair_task.count() > 1:
            print "more than one:"
            for task in join_pair_task:
                print task.primary_item, task.secondary_item, task.find_pairs_task, task.result, task.has_same_pjf, task.yes_votes, task.no_votes
        join_pair_task = JoinPairTask.objects.get(primary_item=prim_item,secondary_item=sec_item)
        join_pair_task.has_same_pjf = True
        join_pair_task.save()
    else:
        join_pair_task = JoinPairTask.objects.create(primary_item=prim_item,secondary_item=sec_item,has_same_pjf=True)
    sec_items = sec_items.exclude(name=sec_item.name)
    # if the task has reached consensus, choose another random one
    while join_pair_task.result is not None:
        sec_item = sec_items.order_by('?').first()
        sec_items = sec_items.exclude(name=sec_item.name)
        join_pair_task = JoinPairTask.objects.filter(primary_item=prim_item).filter(secondary_item=sec_item)
        # set has_same_pjf to true in case join pairs task was created in find pairs
        if join_pair_task.exists():
            join_pair_task = JoinPairTask.objects.get(primary_item=prim_item,secondary_item=sec_item)
            join_pair_task.has_same_pjf = True
            join_pair_task.save()
        else:
            join_pair_task = JoinPairTask.objects.create(primary_item=prim_item,secondary_item=sec_item,has_same_pjf=True)
    join_pair_task.workers.add(worker)
    join_pair_task.save()
    return join_pair_task
        

## @brief chooses a secondary predicate task based on a worker
# @param worker workerID of the worker this task is going to
def choose_task_sec_pred(worker):
    if SecPredTask.objects.filter(in_progress=True).exists():
        sec_pred_task = SecPredTask.objects.get(in_progress=True)
    else:
        # only secondary items that haven't reached consensus but match at least one primary item
        sec_items_left = SecondaryItem.objects.filter(second_pred_result=None).exclude(matches_some = False)
     
        if toggles.SEC_INFLUENTIAL is True:
            sec_item = sec_items_left.order_by('-num_prims_left').first() # item related to the most primary items
            sec_pred_task = SecPredTask.objects.get_or_create(secondary_item=sec_item)[0]
            # choose new secondary item if worker has worked on it
            while worker in sec_pred_task.workers.all():
                sec_items_left = sec_items_left.exclude(pk=sec_item.pk)
                if sec_items_left.count() is 0: #if worker has done all remaining task, give them a useless task
                    sec_items_left = SecondaryItem.objects.exclude(second_pred_result = None)
                    print "useless task issued"
                sec_item = sec_items_left.order_by('-num_prims_left').first()
                sec_pred_task = SecPredTask.objects.get_or_create(secondary_item=sec_item)[0]
        else:
            sec_items_left = sec_items_left.filter(num_prims_left__gt=0)
            sec_item = sec_items_left.order_by('?').first() # random secondary item
            sec_pred_task = SecPredTask.objects.get_or_create(secondary_item=sec_item)[0]
            # choose new secondary item if worker has worked on it
            while worker in sec_pred_task.workers.all():
                sec_items_left = sec_items_left.exclude(pk=sec_item.pk)
                if sec_items_left.count() is 0: #if worker has done all remaining task, give them a useless task
                    sec_items_left = SecondaryItem.objects.exclude(second_pred_result = None)
                    print "useless task issued"
                sec_item = sec_items_left.order_by('?').first()
                sec_pred_task = SecPredTask.objects.get_or_create(secondary_item=sec_item)[0]
    sec_pred_task.workers.add(worker)
    sec_pred_task.save()
    return sec_pred_task

def choose_task_sec_pred_by_prim(worker, prim_item):
    if SecPredTask.objects.filter(in_progress=True).exists():
        sec_pred_task = SecPredTask.objects.filter(in_progress=True).order_by('-num_tasks').first()
    else:
        for sec in prim_item.secondary_items.all():
            sec_pred_task = SecPredTask.objects.get_or_create(secondary_item=sec)[0]
    return sec_pred_task

def choose_task_sec_pred_before_pairs(worker):
    if SecPredTask.objects.filter(in_progress=True).exists():
        sec_pred_task = SecPredTask.objects.filter(in_progress=True).first()
    else:
        sec_items_left = SecondaryItem.objects.filter(second_pred_result=None)
        sec = sec_items_left.order_by('?').first()
        sec_pred_task = SecPredTask.objects.get_or_create(secondary_item=sec)[0]
        while worker in sec_pred_task.workers.all():
            sec_items_left = sec_items_left.exclude(pk=sec_item.pk)
            if sec_items_left.count() is 0: #if worker has done all remaining task, give them a useless task
                sec_items_left = SecondaryItem.objects.exclude(second_pred_result = None)
                print "useless task issued"
            sec_item = sec_items_left.order_by('?').first()
            sec_pred_task = SecPredTask.objects.get_or_create(secondary_item=sec_item)[0]        
    return sec_pred_task

#_____GATHER TASKS_____#

## @brief Generic gather_task function that updates state after a worker response is recieved
#   @param task_type An integer representing the type of task being recieved
#   @param answer A string or (0,1) representing the worker response
#   @param cost The amount of time it took the worker to complete the hit
def gather_task(task_type, answer, cost, item1_id = "None", item2_id = "None"):
    if item1_id is None and item2_id is None:
        raise Exception("no item given")
    #call correct helper for the given task_type and collect the result (if we reach consensus)
    if task_type == 0:
        finished = collect_joinable_filter(answer, cost, item1_id)
    elif task_type == 1:
        answer = parse_pairs(answer)
        finished = collect_find_pairs(answer, cost, item1_id, 1) 
    elif task_type == 2:
        finished = collect_join_pair(answer, cost, item1_id, item2_id)
    elif task_type == 3:
        finished = collect_prejoin_filter(answer, cost, item1_id, item2_id)
    elif task_type == 4:
        finished = collect_secondary_predicate(answer, cost, item2_id)
    elif task_type == 5:
        answer = parse_pairs(answer)
        finished = collect_find_pairs(answer, cost, item2_id, 2)
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
    primary_item = PrimaryItem.objects.get(name = item1_id)

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
## find_pairs_type: 1 is itemwise on primary, 2 is on secondary
def collect_find_pairs(answer, cost, item_id, find_pairs_type):
    #load primary item from db
    if find_pairs_type is 1:
        primary_item = PrimaryItem.objects.get(name = item_id)

        #use primary item to find the relevant task
        our_tasks = FindPairsTask.objects.filter(primary_item = primary_item)
        #if we have a joinable filter task with this item, it is our task.
        #otherwise, we must create a new task
        if not our_tasks.exists():
            this_task = FindPairsTask.objects.create(primary_item = primary_item)
        else:
            this_task = FindPairsTask.objects.get(primary_item = primary_item)
            this_task.refresh_from_db()

        #holds the list of secondary item (ids) we get from this task
        sec_items_list = []
        for match in answer:
            #disambiguate matches with strings
            disamb_match = disambiguate_str(match)
            if disamb_match == "":
                continue

            #find or create a secondary item that matches this name
            known_sec_items = SecondaryItem.objects.filter(name = disamb_match)
            if known_sec_items.exists():
                this_sec_item = SecondaryItem.objects.get(name = disamb_match)
            else:
                this_sec_item = SecondaryItem.objects.create(name = disamb_match)
            sec_items_list.append(this_sec_item.name)

        #call the model's function to update its state
        this_task.get_task(sec_items_list, cost)

        this_task.refresh_from_db()
    elif find_pairs_type is 2:
        sec_item = SecondaryItem.objects.get(name = item_id)

        #use primary item to find the relevant task
        our_tasks = FindPairsTask.objects.filter(secondary_item = sec_item)
        #if we have a joinable filter task with this item, it is our task.
        #otherwise, we must create a new task
        if not our_tasks.exists():
            this_task = FindPairsTask.objects.create(secondary_item = sec_item)
        else:
            this_task = FindPairsTask.objects.get(secondary_item = sec_item)

        #holds the list of secondary item (ids) we get from this task
        prim_items_list = []
        for match in answer:
            #disambiguate matches with strings
            disamb_match = disambiguate_str(match)
            if disamb_match == "":
                continue

            #find or create a primary item that matches this name
            this_prim_item = PrimaryItem.objects.get(name=disamb_match)
            prim_items_list.append(this_prim_item.name)
        #call the model's function to update its state
        this_task.get_task(prim_items_list, cost)

        this_task.refresh_from_db()
    return this_task.consensus

## takes a string of entries (separated by the string {{NEWENTRY}}) for find_pairs and parses them
def parse_pairs(pairs):
    if pairs is None or pairs is "" or pairs == 'None':
        return []
    else:
        processed = []
        for match in pairs.strip("{{NEWENTRY}}").split("{{NEWENTRY}}"):
            temp = match.strip()
            temp = temp.lower()
            processed.append(temp)
        return processed

## turns string responses into unique identifying strings
#NOTE: this function is specific to our example (hotels and hospitals)
# new functions must be written for different queries
def disambiguate_str(sec_item_str):
    #we want the (numeric) non-whitespace characters after the semicolon
    semicol_pos = sec_item_str.rfind(';')
    if ';' not in sec_item_str:
        if sec_item_str != '' and sec_item_str[0].isdigit():
            semicol_pos = -1
        elif ',' in sec_item_str:
            semicol_pos = sec_item_str.find(',')
    addr = sec_item_str[semicol_pos+1:].strip()
    for i in range(len(addr)):
        if addr[i].isspace():
            addr = addr[:i]
            break
    if addr == "" or (not addr[0].isdigit()):
        addr = ""
    return addr
    
## Collect Join Pair task
def collect_join_pair(answer, cost, item1_id, item2_id):
    #load primary item from db
    primary_item = PrimaryItem.objects.get(name = item1_id)
    #load secondary item from db
    secondary_item = SecondaryItem.objects.get(name = item2_id)

    #use primary item to find the relevant task
    our_tasks = JoinPairTask.objects.filter(primary_item = primary_item).filter(secondary_item = secondary_item)
    #if we have a join pair task with these items, it is our task.
    #otherwise, we must create a new task
    if not our_tasks.exists():
        print "creating here --- this shouldn't happen"
        this_task = JoinPairTask.objects.create(primary_item = primary_item, secondary_item = secondary_item)
    else:
        if our_tasks.count() > 1:
            print "more than one:"
            for task in our_tasks:
                print task.primary_item, task.secondary_item, task.find_pairs_task, task.result, task.has_same_pjf
        this_task = JoinPairTask.objects.get(primary_item = primary_item, secondary_item = secondary_item)
    
    #allow model functionality to update its fields accordingly
    this_task.get_task(answer, cost)

    #return the result from this_task for use
    this_task.refresh_from_db()
    return this_task.result

## Collect Prejoin Filter task
def collect_prejoin_filter(answer, cost, item1_id="None", item2_id="None"):
    # primary item task
    if item1_id is not "None":
        #load primary item from db
        primary_item = PrimaryItem.objects.get(name = item1_id)
        #use primary item to find the relevant task
        our_tasks = PJFTask.objects.filter(primary_item = primary_item)
        #if we have a prejoin filter task with these items, it is our task.
        #otherwise, we must create a new task
        if not our_tasks.exists():
            this_task = PJFTask.objects.create(primary_item = primary_item)
        else:
            this_task = PJFTask.objects.get(primary_item = primary_item)
    # secondary item task
    else:
        #load secondary item from db
        secondary_item = SecondaryItem.objects.get(name = item2_id)
        #use secondary item to find the relevant task
        our_tasks = PJFTask.objects.filter(secondary_item = secondary_item)
        #if we have a prejoin filter task with these items, it is our task.
        #otherwise, we must create a new task
        if not our_tasks.exists():
            this_task = PJFTask.objects.create(secondary_item = secondary_item)
        else:
            this_task = PJFTask.objects.get(secondary_item = secondary_item)

    # allow model functionality to update its fields accordingly
    this_task.get_task(answer, cost)

    #return the result from this_task for use
    this_task.refresh_from_db()
    return this_task.consensus

## Collect secondary predicate task
def collect_secondary_predicate(answer, cost, item2_id):
    #load secondary item from db
    secondary_item = SecondaryItem.objects.get(name = item2_id)

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




######################################################## OVERNIGHT
def choose_task_pjf_helper_overnight(worker,join_type):
    # first does all primary item pjf tasks
    prim_items_left = PrimaryItem.objects.filter(pjf='false')
    if prim_items_left.exists():
        prim_item = prim_items_left.order_by('?').first() # random primary item
        pjf_task = PJFTask.objects.get_or_create(primary_item=prim_item)[0]
    # secondary item pjf tasks
    else:
        if join_type == 2.2: 
            sec_items_left = SecondaryItem.objects.filter(pjf='false').filter(second_pred_result = True)
        else:
            sec_items_left = SecondaryItem.objects.filter(pjf='false')
        sec_item = sec_items_left.order_by('?').first() # random secondary item
        pjf_task = PJFTask.objects.get_or_create(secondary_item=sec_item)[0]
    pjf_task.workers.add(worker)
    pjf_task.save()
    return pjf_task


def choose_task_PJF2_overnight(workerID, estimator,join_type):
    new_worker = Worker.objects.get_or_create(worker_id=workerID)[0]
    #for join type 2.3: when we don't start w the secondary list
    if not estimator.has_2nd_list:
        prim_items_left = PrimaryItem.objects.filter(found_all_pairs = False)
        return choose_task_find_pairs(prim_items_left, new_worker, 1)
    #first do secondary predicate tasks
    elif SecondaryItem.objects.exclude(second_pred_result = False).exclude(second_pred_result = True).exists(): #all unevaluated secondary predicate tasks
        return choose_task_sec_pred_before_pairs(new_worker)
    #then do pre-join filters
    elif SecondaryItem.objects.filter(second_pred_result = True).filter(pjf = 'false').exists() or PrimaryItem.objects.filter(pjf = 'false').exists(): #unfinished pjfs
        return choose_task_pjf_helper_overnight(new_worker, join_type)
    #then do join pairs tasks
    elif PrimaryItem.objects.filter(found_all_pairs = False).exists():
        return choose_task_join_pairs2(new_worker)
    else:
        print "******************************** WHY ARE YOU HERE??? ********************************"

def choose_task_PJF_overnight(workerID, estimator,join_type):
    new_worker = Worker.objects.get_or_create(worker_id=workerID)[0]
    if not estimator.has_2nd_list:
        prim_items_left = PrimaryItem.objects.filter(found_all_pairs=False)
        return choose_task_find_pairs(prim_items_left, new_worker, 1)

    elif PrimaryItem.objects.filter(pjf='false').exists() or SecondaryItem.objects.filter(pjf='false').exists():
        return choose_task_pjf_helper_overnight(new_worker,join_type)

    elif PrimaryItem.objects.filter(found_all_pairs=False).exists():
        return choose_task_join_pairs(new_worker)

    else:
        return choose_task_sec_pred(new_worker)