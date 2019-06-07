from items import *


@python_2_unicode_compatible
class Worker(models.Model):
    """
    Model representing a worker on the MTurk.
    """
    worker_id = models.CharField(max_length=20)
 

@python_2_unicode_compatible
class TaskStats(models.Model):
    """
    Model representing types of tasks and the stats we need to store for each type.
    """
    task_type = models.IntegerField(default=0)
    # 0 = joinable filter task
    # 1 = find pairs task
    # 2 = join pairs task
    # 3 = pre-join filter task
    # 4 = secondary predicate task

    # cost is measured by time it takes to complete task
    cost = models.FloatField(default=0)

    # when ambiguity is 0, workers answer correctly 100% of time and randomly 0% of time
    # when ambiguity is 0.5, workers answer correctly 50% of time and randomly 50% of time
    ambiguity = models.FloatField(default=0)

    # when selectivity is 0, no items pass
    # when selectivity is 1, all items pass
    selectivity = models.FloatField(default=0)

    # for IW join - average number of pairs per primary item
    avg_num_pairs = models.IntegerField(default=0)

    # number of items processed
    num_processed = models.IntegerField(default=0)

    def __str__(self):
        return "Task stats for task type ", self.task_type   

    def set_type_of_task(self, typeOfTask):
        self.task_type = typeOfTask

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

@python_2_unicode_compatible
class JFTask(models.Model):
    """
    Model representing pairs of items and joinable filter tasks.
    """
    # workers who have worked or are working on this task
    workers = models.ManyToManyField(Worker,related_name="joinable_filter_task")

    primary_item = models.ForeignKey(PrimaryItem, default=None, null=True)
    # keep track of number of tasks
    num_tasks = models.IntegerField(default=0)
    # total time
    time = models.FloatField(default=0)

    # result: 
    # True if the IT pair passes with consensus
    # False if the IT pair doesn't pass
    # None consensus is not reached
    yes_votes = models.IntegerField(default=0)
    no_votes = models.IntegerField(default=0)
    result = models.NullBooleanField(default=None)

    def __str__(self):
        return "Joinable Filter for item ", self.primary_item 

    def update_result(self):
        self.result = views_helpers.find_consensus(self)

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

@python_2_unicode_compatible
class FindPairsTask(models.Model):
    """
    Model representing pairs of items and item-wise join tasks.
    """
    # workers who have worked or are working on this task
    workers = models.ManyToManyField(Worker,related_name="find_pairs_task")
     
    primary_item = models.ForeignKey(PrimaryItem, default=None, null=True)
    # keep track of number of tasks
    num_tasks = models.IntegerField(default=0)
    # total time
    time = models.FloatField(default=0)

    # consensus: 
    # True if the IT pair reaches consensus
    # False if consensus is not reached
    consensus = models.NullBooleanField(default=False)

    def __str__(self):
        return "Find Pairs for item " + str(self.primary_item)   

    def update_consensus(self):
        join_pair_tasks = JoinPairTask.objects.filter(find_pairs_task = self, result = None)
        if not join_pair_tasks.exists():
            self.consensus = True
            self.save()
        else:
            self.consensus = False
            self.save()

    #expects a list of secondary item ids (the answer) and the cost returned from a find_pairs task
    def get_task(self, answer, cost):
        #update average time
        self.time = (self.time * self.num_tasks + time) / (self.num_tasks + 1)

        #get join pairs from this task
        join_pair_tasks = JoinPairTask.objects.filter(find_pairs_task = self, result = None)

        # Find join pair tasks that match each match we found, creating new ones if necessary
        for match in answer:
            sec_item = SecondaryItem.get(id = match)
            matching_join_pairs = join_pair_tasks.filter(secondary_item = sec_item, primary_item = self.primary_item)

            #create a new join pair task if it does not exist in our list of join pair tasks
            #NOTE: We may at some point need to address adding join pair tasks that exist to our list
            if not matching_join_pairs.exists():
                JoinPairTask.objects.create(primary_item = self.primary_item, secondary_item = sec_item, find_pairs_task = self, no_votes = num_tasks)

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

        self.num_tasks += 1
        self.update_consensus()
        self.save()


@python_2_unicode_compatible
class JoinPairTask(models.Model):
    """
    Model representing pairs of items and join pair tasks.
    """
    # workers who have worked or are working on this task
    workers = models.ManyToManyField(Worker,related_name="join_pair_task")
    
    primary_item = models.ForeignKey(PrimaryItem, default=None, null=True)
    secondary_item = models.ForeignKey(SecondaryItem, default=None, null=True)
    # keep track of number of tasks
    num_tasks = models.IntegerField(default=0)
    # total time
    time = models.FloatField(default=0)

    # many to one relationship for finding consensus for find pairs task
    find_pairs_task = models.ForeignKey(FindPairsTask)

    # result: 
    # True if the IT pair passes with consensus
    # False if the IT pair doesn't pass
    # None consensus is not reached
    yes_votes = models.IntegerField(default=0)
    no_votes = models.IntegerField(default=0)
    result = models.NullBooleanField(default=None)

    consensus = models.BooleanField(default=False)
    def __str__(self):
        return "Join Pair task for items " + str(self.primary_item) + ", " + str(self.secondary_item)

    def update_result(self):
        #have we reached consensus?
        self.result = views_helpers.find_consensus(self)
        self.save()

        #if we have reached consensus and the result is a match, add our secondary item to the
        #primary item's list of matches
        #Running this multiple times is fine, the relationship is not duplicated
        if self.result is True:
            self.primary_item.add_secondary_item(self.secondary_item)

    
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

@python_2_unicode_compatible
class PJFTask(models.Model):
    """
    Model representing pairs of items and pre-join filter tasks.
    """
    # workers who have worked or are working on this task
    workers = models.ManyToManyField(Worker,related_name="pre_join_task")
    
    primary_item = models.ForeignKey(PrimaryItem, default=None, null=True)
    secondary_item = models.ForeignKey(SecondaryItem, default=None, null=True)
    # keep track of number of tasks
    num_tasks = models.IntegerField(default=0)
    # total time
    time = models.FloatField(default=0)

    # consensus: 
    # True if the IT pair passes with consensus
    # False if the IT pair doesn't pass
    # None consensus is not reached
    consensus = models.NullBooleanField(default=None)

    def __str__(self):
        if self.primary_item is not None:
            return "Pre-Join Filter for item " + str(self.primary_item)
        elif self.secondary_item is not None:
            return "Pre-Join Filter for item " + str(self.secondary_item)
        else:
            raise Exception("No item")

@python_2_unicode_compatible
class SecPredTask(models.Model):
    """
    Model representing pairs of items and secondary predicate tasks.
    """
    # workers who have worked or are working on this task
    workers = models.ManyToManyField(Worker,related_name="secondary_pred_task")
    
    secondary_item = models.ForeignKey(SecondaryItem, default=None, null=True)
    # keep track of number of tasks
    num_tasks = models.IntegerField(default=0)
    # total time
    time = models.FloatField(default=0)

    # result: 
    # True if the IT pair passes with consensus
    # False if the IT pair doesn't pass
    # None consensus is not reached
    yes_votes = models.IntegerField(default=0)
    no_votes = models.IntegerField(default=0)
    result = models.NullBooleanField(default=None)

    def __str__(self):
        return "Secondary Predicate Filter for item " + str(self.secondary_item)

    def update_result(self):
        self.result = views_helpers.find_consensus(self)

    
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

    def when_done(self):
        """
        Checks if consensus is reached and updates variables accordingly
        """
        if self.result == True:
            primary_set = self.secondary_item.primary_items.all()
            for primary_item in primary_set:
                primary_item.eval_result = True
                primary_item.save()
            self.secondary_item.second_pred_result = True
        
        #Mark hotels done, remove restaurant
        elif self.result == False:            
            #Decrement counter of related primary items by 1
            primary_set = self.secondary_item.primary_items.all()

            for primary_item in primary_set:
                primary_item.num_sec_items -= 1
                primary_item.save()
            
            #Removes all relationships with this item
            self.secondary_item.primary_items.clear()
            self.secondary_item.second_pred_result = False


