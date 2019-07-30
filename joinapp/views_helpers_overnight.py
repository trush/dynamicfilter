from views_helpers import *

######################################################## OVERNIGHT
##### Copies of everything so that we don't mess things up for the overnight sims
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
        return choose_task_pjf_helper_overnight(new_worker,join_type)
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