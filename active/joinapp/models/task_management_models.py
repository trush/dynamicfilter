from django.db import models
from django.utils.encoding import python_2_unicode_compatible

import items
from .. import find_consensus
from .. import toggles

## @brief Model representing a worker on MTurk
@python_2_unicode_compatible
class Worker(models.Model):
    ## MTurk worker ID
    worker_id = models.CharField(max_length=20)
    ## ToString method
    def __str__(self):
        return "Worker ID: " + str(worker_id)
 
## @brief Model representing types of tasks and the statistics we need to store for each type
@python_2_unicode_compatible
class TaskStats(models.Model):
    ## 0 = joinable filter task <br>
    # 1 = find pairs task <br>
    # 2 = join pairs task <br>
    # 3 = pre-join filter task <br>
    # 4 = secondary predicate task
    task_type = models.IntegerField(default=0)
    

    ## the amount of time it takes to complete a task
    cost = models.FloatField(default=0)

    ## when ambiguity is 0, workers answer correctly 100% of time and randomly 0% of time <br>
    ## when ambiguity is 0.5, workers answer correctly 50% of time and randomly 50% of time
    ambiguity = models.FloatField(default=0)

    ## when selectivity is 0, no items pass <br>
    ## when selectivity is 1, all items pass
    selectivity = models.FloatField(default=0)

    ## for item-wise join - average number of pairs per primary item
    avg_num_pairs = models.IntegerField(default=0)

    ## number of assignments processed for a task
    num_processed = models.IntegerField(default=0)

    ## @brief To-string method
    def __str__(self):
        return "Task stats for task type ", self.task_type   

    ## @brief Sets task type
    # @param typeOfTask An integer representing the type of task this is
    def set_type_of_task(self, typeOfTask):
        self.task_type = typeOfTask

    ## @brief Updates the selectivity and cost of a task
    # @param cost The cost of the incoming response
    # @param answer The answer of the incoming response (a 1 or 0 for tasks 0,3,and 4; a string for tasks 1 and 2)
    def update_stats(self, cost, answer):
        # update num_processed, cost, selectivity
        self.cost = ((self.cost*self.num_processed) + cost)/(self.num_processed + 1)
        # filter-type tasks
        if self.task_type is 0 or self.task_type is 3 or self.task_type is 4:
            if answer:
                self.selectivity = ((self.selectivity*self.num_processed) + 1)/(self.num_processed + 1)
            else:
                self.selectivity = (self.selectivity*self.num_processed)/(self.num_processed + 1)
            self.ambiguity = (1-self.selectivity)*2
        # IW task
        elif self.task_type is 1:
            self.avg_num_pairs = ((self.avg_num_pairs*self.num_processed) + len(answer))/(self.num_processed + 1)
        # TODO: prejoin filter stats
        self.num_processed += 1
        self.save()

## @brief Model representing a joinable-filter task for a primary item
@python_2_unicode_compatible
class JFTask(models.Model):
    ## workers who have worked or are working on this task
    workers = models.ManyToManyField(Worker,related_name="joinable_filter_task")
    ## primary item this task is associated with
    primary_item = models.ForeignKey('PrimaryItem', default=None, null=True)
    
    ## number of assignments processed for a task
    num_tasks = models.IntegerField(default=0)
    
    ## total worker time spent processing this task
    time = models.FloatField(default=0)

    # result: 
    ## True if the task passes with consensus <br>
    ## False if the task doesn't pass <br>
    ## None consensus is not reached
    result = models.NullBooleanField(default=None)
    yes_votes = models.IntegerField(default=0)
    no_votes = models.IntegerField(default=0)
    

    ## @brief ToString method
    def __str__(self):
        return "Joinable Filter for item ", self.primary_item 

    ## @brief Calls find_consensus to update the result of the task if possible
    def update_result(self):
        self.result = find_consensus.find_consensus(self)
        if self.result is True or self.result is False:
            self.primary_item.is_done = True
            self.primary_item.eval_result = self.result
        self.primary_item.save()
        self.save()
        self.refresh_from_db()

    ## @brief Updates state after an assignment for this task is completed
    # @param answer response from the assignment (0 or 1)
    # @param time How long it took to execute the incoming assignment
    def get_task(self, answer, time):
        #update yes_votes or no_votes based on answer
        if answer is 1:
            self.yes_votes += 1
        elif answer is 0:
            self.no_votes += 1

        #update average time
        self.time = (self.time * self.num_tasks + time) / (self.num_tasks + 1)

        #update number of tasks so far
        self.num_tasks += 1

        #check whether we've reached consensus
        self.update_result()
        self.save()

## @brief Model representing a find-pairs task for a primary item
@python_2_unicode_compatible
class FindPairsTask(models.Model):
    ## workers who have worked or are working on this task
    workers = models.ManyToManyField(Worker,related_name="find_pairs_task")
    ## primary item this task is associated with
    primary_item = models.ForeignKey('PrimaryItem', default=None, null=True)
    ## number of assignments processed for this task
    num_tasks = models.IntegerField(default=0)
    ## total worker time spent processing this task
    time = models.FloatField(default=0)

    # consensus: 
    ## True if the task pair reaches consensus <br>
    ## False if consensus is not reached
    consensus = models.NullBooleanField(default=False)

    ## @brief ToString method
    def __str__(self):
        return "Find Pairs for item " + str(self.primary_item)   

    ## @brief Updates whether or not consensus has been reached
    def update_consensus(self):
        join_pair_tasks = JoinPairTask.objects.filter(find_pairs_task = self)
        if not join_pair_tasks.exists():
            self.primary_item.refresh_from_db()
            if self.num_tasks >= toggles.NUM_CERTAIN_VOTES:
                self.consensus = True
                self.primary_item.found_all_pairs = True
                self.primary_item.update_state()
                self.primary_item.save()
                self.save()
            else:
                self.consensus = False
                self.save()
        else:
            join_pair_tasks = join_pair_tasks.filter(result = None)
            if not join_pair_tasks.exists():
                self.consensus = True
                self.primary_item.refresh_from_db()
                self.primary_item.found_all_pairs = True
                self.primary_item.update_state()
                self.primary_item.save()
                self.save()
            else:
                self.consensus = False
                self.save()

    ## @brief Updates state after an assignment for this task is completed
    # @param answer A list of secondary items
    # @param time How long it took to execute the incoming assignment
    def get_task(self, answer, time):
        from estimator import *
        #update average time
        self.time = (self.time * self.num_tasks + time) / (self.num_tasks + 1)

        #get join pairs from this task
        join_pair_tasks = JoinPairTask.objects.filter(find_pairs_task = self, result = None)

        # Find join pair tasks that match each match we found, creating new ones if necessary
        for match in answer:
            sec_item = items.SecondaryItem.objects.get(pk = match)
            matching_join_pairs = join_pair_tasks.filter(secondary_item = sec_item, primary_item = self.primary_item)

            #create a new join pair task if it does not exist in our list of join pair tasks
            #NOTE: We may at some point need to address adding join pair tasks that exist to our list
            if not matching_join_pairs.exists():
                JoinPairTask.objects.create(primary_item = self.primary_item, secondary_item = sec_item, find_pairs_task = self, no_votes = self.num_tasks)

        #get join pairs from this task (again)
        join_pair_tasks = JoinPairTask.objects.filter(find_pairs_task = self, result = None)

        #add votes as necessary, update consensus for each join pair task
        for join_pair_task in join_pair_tasks:
            #update votes
            if join_pair_task.secondary_item.id in answer:
                join_pair_task.yes_votes += 1
            else:
                join_pair_task.no_votes += 1
            join_pair_task.save(update_fields = ["yes_votes","no_votes"])

            #check consensus
            join_pair_task.update_result()

            estimator = Estimator.objects.all().first()
            #update estimator
            estimator.update_chao_estimator_variables(join_pair_task)
        self.num_tasks += 1
        self.update_consensus()
        self.save()

## @brief Model representing a join condition task for a primary-secondary item pair
@python_2_unicode_compatible
class JoinPairTask(models.Model):
    ## workers who have worked or are working on this task
    workers = models.ManyToManyField(Worker,related_name="join_pair_task")
    ## primary item associated with this join
    primary_item = models.ForeignKey('PrimaryItem', default=None, null=True)
    ## secondary item associated with this join
    secondary_item = models.ForeignKey('SecondaryItem', default=None, null=True)
    ## number of assignments processed for a task
    num_tasks = models.IntegerField(default=0)
    ## total worker time spent processing this task
    time = models.FloatField(default=0)

    ## many to one relationship used for finding consensus for find pairs task
    find_pairs_task = models.ForeignKey(FindPairsTask)

    # result: 
    ## True if the task passes with consensus <br>
    ## False if the task doesn't pass <br>
    ## None consensus is not reached
    result = models.NullBooleanField(db_index=True, default=None)
    yes_votes = models.IntegerField(default=0)
    no_votes = models.IntegerField(default=0)
    
    ## @brief ToString method
    def __str__(self):
        return "Join Pair task for items " + str(self.primary_item) + ", " + str(self.secondary_item)

    ## checks and updates whether or not consensus has been reached
    def update_result(self):
        #have we reached consensus?
        self.result = find_consensus.find_consensus(self)
        self.save()

        #if we have reached consensus and the result is a match, add our secondary item to the 
        # primary item's list of matches <br>
        #Running this multiple times is fine, the relationship is not duplicated
        if self.result is True:
            if self.secondary_item.second_pred_result is None:
                self.primary_item.add_secondary_item(self.secondary_item)
                self.primary_item.refresh_from_db()
                self.secondary_item.refresh_from_db()
                self.secondary_item.matches_some = True
                self.secondary_item.save()
            else:
                self.primary_item.add_secondary_item(self.secondary_item)
                self.primary_item.update_state()
                
            self.secondary_item.save()


    ## @brief Updates state after an assignment for this task is completed
    # @param answer Worker answer (Boolean)
    # @param time How long it took to execute the incoming assignment
    def get_task(self, answer, time):
        #update yes_votes or no_votes based on answer
        if answer:
            self.yes_votes += 1
        else:
            self.no_votes += 1

        #update average time
        self.time = (self.time * self.num_tasks + time) / (self.num_tasks + 1)

        #update number of tasks so far
        self.num_tasks += 1

        #check whether we've reached consensus
        self.update_result()
        self.save()

## @brief Model representing a pre join filter
@python_2_unicode_compatible
class PJFTask(models.Model):
    """
    Model representing pairs of items and pre-join filter tasks.
    """
    ## workers who have worked or are working on this task
    workers = models.ManyToManyField(Worker,related_name="pre_join_task")
    
    ## primary item associated with this join
    primary_item = models.ForeignKey('PrimaryItem', default=None, null=True)
    ## secondary item associated with this join
    secondary_item = models.ForeignKey('SecondaryItem', default=None, null=True)
    ## number of assignments processed for this task
    num_tasks = models.IntegerField(default=0)
    ## worker time spent processing this task
    time = models.FloatField(default=0)

    # consensus: 
    ## True if the prejoin filter reaches consensus <br>
    ## False if the prejoin filter hasn't reached consensus
    consensus = models.BooleanField(default=None)

    ## @brief ToString method
    def __str__(self):
        if self.primary_item is not None:
            return "Pre-Join Filter for item " + str(self.primary_item)
        elif self.secondary_item is not None:
            return "Pre-Join Filter for item " + str(self.secondary_item)
        else:
            raise Exception("No item")
    
    ## @brief Updates whether or not consensus has been reached
    def update_consensus(self):
        # all item pjf pairs with this item 
        item_pjf_pairs = ItemPJFPair.objects.filter(pjf_task = self)
        item_pjf_pairs = item_pjf_pairs.filter(consensus = True)
        # if there is a pjf that has reached consensus, update consensus to true
        if item_pjf_pairs.exists():
            self.consensus = True
            ItemPJFPair.objects.filter(pjf_task = self)
            self.save()
        else:
            self.consensus = False
            self.save()

    ## @brief Updates state after an assignment for this task is completed
    # @param answer A string containing the pjf
    # @param time How long it took to execute the incoming assignment
    def get_task(self, answer, time):
        # primary item task
        if self.primary_item is not None:
            pair = ItemPJFPair.objects.filter(primary_item=self,pjf=answer)
            #create a new item pjf pair if it does not exist
            if not pair.exists():
                ItemPJFPair.objects.create(primary_item=self.primary_item,pjf=answer,pjf_task = self,no_votes = self.num_tasks)
            item_pjf_pairs = ItemPJFPair.objects.filter(primary_item=self.primary_item)
        # secondary item task
        elif self.secondary_item is not None:
            pair = ItemPJFPair.objects.filter(secondary_item=self,pjf=answer)
            #create a new item pjf pair if it does not exist
            if not pair.exists():
                ItemPJFPair.objects.create(secondary_item=self.secondary_item,pjf=answer,pjf_task = self,no_votes = self.num_tasks)
            item_pjf_pairs = ItemPJFPair.objects.filter(secondary_item=self.secondary_item)
        # get_task for each item pjf pair associated with this 
        for item in item_pjf_pairs:
            item.get_task(answer)

        #update average time
        self.time = (self.time * self.num_tasks + time) / (self.num_tasks + 1)

        #update number of tasks so far
        self.num_tasks += 1

        #check whether we've reached consensus
        self.update_consensus()
        self.save()


## @brief Model representing an item and pre-join filter pair
## Used for reaching consensus on a pre-join filter for PJFTask
@python_2_unicode_compatible
class ItemPJFPair(models.Model):
    """
    Model representing pairs of items and pre-join filter tasks.
    """
    ## primary item associated with this join
    primary_item = models.ForeignKey('PrimaryItem', default=None, null=True)
    ## secondary item associated with this join
    secondary_item = models.ForeignKey('SecondaryItem', default=None, null=True)
    
    ## prejoin filter associated with this join
    pjf = models.CharField(max_length=10)

    ## many to one relationship used for finding consensus
    pjf_task = models.ForeignKey(PJFTask)

    # consensus: 
    ## True if the pjf reaches consensus <br>
    ## False if the pjf doesn't reach consensus
    consensus = models.BooleanField(db_index=True, default=False)
    yes_votes = models.IntegerField(default=0)
    no_votes = models.IntegerField(default=0)

    ## @brief ToString method
    def __str__(self):
        if self.primary_item is not None:
            return "Pre-Join Filter for item " + str(self.primary_item) + " is " + self.pjf
        elif self.secondary_item is not None:
            return "Pre-Join Filter for item " + str(self.secondary_item) + " is " + self.pjf
        else:
            raise Exception("No item")

    ## checks and updates whether or not consensus has been reached
    def update_consensus(self):
        #have we reached consensus?
        self.consensus = find_consensus.find_consensus(self)
        self.save()

        #if we have reached consensus, then set the item's pjf
        if self.consensus is True:
            if self.primary_item is not None:
                self.primary_item.pjf = self.pjf
                self.primary_item.save()
            elif self.secondary_item is not None:
                self.secondary_item.pjf = self.pjf
                self.secondary_item.save()

    ## @brief Updates state after an assignment for PJFTask is completed
    # @param answer A string containing the pjf
    def get_task(self, answer):
        #update yes_votes or no_votes based on answer
        if answer is self.pjf:
            self.yes_votes += 1
        else:
            self.no_votes += 1

        #check whether we've reached consensus
        self.update_consensus()
        self.save()

## @brief Model representing a secondary predicate task
@python_2_unicode_compatible
class SecPredTask(models.Model):
    ## workers who have worked or are working on this task
    workers = models.ManyToManyField(Worker,related_name="secondary_pred_task")
    
    ## secondary item associates with this task
    secondary_item = models.ForeignKey('SecondaryItem', default=None, null=True)
    ## total number of assingments processed for this task
    num_tasks = models.IntegerField(default=0)
    ## total worker time spent processing this task
    time = models.FloatField(default=0)

    # result: 
    ## True if the IT pair passes with consensus <br>
    ## False if the IT pair doesn't pass <br>
    ## None consensus is not reached
    result = models.NullBooleanField(db_index=True, default=None)
    yes_votes = models.IntegerField(default=0)
    no_votes = models.IntegerField(default=0)
    
    ## @brief ToString method
    def __str__(self):
        return "Secondary Predicate Filter for item " + str(self.secondary_item)

    ## @brief Checks if consensus has been reached to update result attribute
    def update_result(self):
        self.result = find_consensus.find_consensus(self)
        self.secondary_item.second_pred_result = self.result
        self.secondary_item.save()
        self.save()
        for prim_item in self.secondary_item.primary_items.all():
            prim_item.refresh_from_db()
            prim_item.update_state()

    ## @brief Updates state based on an incoming worker answer
    # @param answer worker answer (0 or 1)
    # @param time amount of time taken for the worker to complete the task
    def get_task(self, answer, time):
        #update yes_votes or no_votes based on answer
        if answer is 1:
            self.yes_votes += 1
        elif answer is 0:
            self.no_votes += 1
        else:
            print "weird answer"

        #update average time
        self.time = (self.time * self.num_tasks + time) / (self.num_tasks + 1)

        #update number of tasks so far
        self.num_tasks += 1

        #check whether we've reached consensus
        self.update_result()
        self.save()


