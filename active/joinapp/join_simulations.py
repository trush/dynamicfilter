import random
import string
import csv
import toggles
from models.items import *
from models.task_management_models import *
from models.estimator import *
from views_helpers import *
from django.test import *
import random
from synthetic_data import *

## @brief Functionality for testing the join algorithm on non-live data
class JoinSimulation():

    ## list holding worker IDs for the simulation
    worker_ids = []

    ## Total number of tasks issued/completed in one simulation
    num_tasks_completed = 0

    ## Amount of worker-time spent during the simulation
    sim_time = 0


    #_____ For tests that run multiple simulations _____#

    ## Total number of tasks issued/completed in each of multiple simulations
    num_tasks_completed_arr = []

    ## Amount of worker-time spent during each of multiple simulations
    sim_time_arr = []

    
    
    #_____ For real data simulations only _____#

    ## Number of primary items that are correctly evaluated
    num_item_correct_eval = 0
    

    #__________________________________  Dictionaries ________________________________#

    ## Key: primary item pk <br>
    ## Value: (primary item pk, "NA", time taken list, worker response list)
    JFTasks_Dict = dict()

    ## Key: primary item pk <br>
    ## Value: (primary item pk, "NA", time taken list, worker response list)
    FindPairsTasks_Dict = dict() 

    ## Key: not implemented <br>
    ## Value: not implemented
    PJFTasks_Dict = dict()

    ## Key: secondary item name <br>
    ## Value: ("NA", secondary item name, time taken list, worker response list)
    SecPredTasks_Dict = dict() 

    ## Key: not implemented (might not need to) <br>
    ## Value: not implemented (might not need to)
    JoinPairTasks_Dict = dict() 

    #_____________________ Loading Data _____________________ #
    
    ## @brief Loads primary list into database
    def load_primary_real(self):
        f = open( PRIMARY_LIST, 'r')
        for line in f:
            try:
                line = line.rstrip ('\n')
                item = PrimaryItem.objects.create(name = line)
            except:
                print "Error reading item "
        f.close()

    ## @brief Loads the MTurk data from a csvfile and populates the answer dictionaries
    def load_real_data(self):
        with open(REAL_DATA_CSV, mode = 'r') as csv_file:
            csv_reader = csv.reader(csv_file, delimeter = ',')
            line_count = 0
            for row in csv_reader:
                #csv rows are organized like this: "Hit Id, Hotel, Restaurant, Assignment Id, Assignment Status, Time Taken, workervote, feedback"
                primary_item = row[1]
                secondary_item = row[2]
                time_taken = row[5]
                worker_vote = row[6]
                try:
                    if task_type is "eval_joinable_filter":
                        primary_item_pk = PrimaryItem.objects.filter(primary_item).pk 
                        if primary_item_pk in self.JFTasks_Dict:
                            value = self.JFTasks_Dict[primary_item_pk]
                        else:
                            value = (primary_item_pk,"NA",[],[]) 
                        value[2] += time_taken #add assignment time to hit
                        value[3] += worker_vote #add worker answer to hit
                        self.JFTasks_Dict[primary_item_pk] = value

                    elif task_type is "list_secondary":
                        primary_item_pk = PrimaryItem.objects.filter(primary_item).pk 
                        if primary_item_pk in self.FindPairsTasks_Dict:
                            value = self.FindPairsTasks_Dict[primary_item.pk] 
                        else:
                            value = (primary_item_pk,"NA",[],[])
                        value[2] += time_taken #add assignment time to hit
                        value[3] += worker_vote #add worker answer to hit
                        self.FindPairsTasks_Dict[primary_item_pk] = value

                    elif task_type is "eval_sec_pred":
                        if secondary_item in self.SecPredTasks_Dict:
                            value = self.SecPredTasks_Dict[secondary_item]   
                        else:
                            value = ("NA", secondary_item,[],[])
                        value[2] += time_taken #add assignment time to hit
                        value[3] += worker_vote #add worker answer to hit

                    elif task_type is "eval_pjf":
                        return "pjf"
                        #TODO implement pjf
                    elif task_type is "eval_join_cond":
                        return "eval_join"
                        #TODO implement join_condition (if necessary)
                except:
                    print "Error reading in row ", line_count
                line_count += 1


    #___________________ Accuracy ______________________#
    #TODO make this better

    ## @brief Print accuracy for real data
    def accuracy_real_data(self):
        #___ JF Task Accuracy ___#
        total_tasks = []
        correct_tasks = []
        for JFTask in JFTask.objects.all():
            if JFTask.result is not None:
                total_tasks += JFTask
        for task in total_tasks:
            ground_truth = self.determine_ground_truth(JFTasks_Dict[task.primary_item.pk][3])
            if task.result is ground_truth:
                correct_tasks += task
        #Print Accuracy
        self.print_accuracy(len(total_tasks),len(correct_tasks),"joinable filter")

        #___ Secondary Predicate Task Accuracy ___#
        total_tasks = []
        correct_tasks = []
        for task in SecPredTask.objects.all():
            if task.result is not None:
                total_tasks += task
        for task in total_tasks:
            ground_truth = self.determine_ground_truth(SecPredTasks_Dict[task.secondary_item.name][3])
            if task.result is ground_truth:
                correct_tasks += task
        #Print Accuracy
        self.print_accuracy(len(total_tasks),len(correct_tasks),"secondary predicate")
        
        #___ Query Accuracy __#
        total_items = []
        correct_items = []
        for primary_item in PrimaryItem.objects.all():
            if primary_item.is_done is True:
                total_items += primary_item
        for primary_item in total_items:
            ground_truth = self.determine_ground_truth(JFTasks_Dict[task.primary_item.pk][3])
            if primary_item.eval_result is ground_truth:
                correct_items += primary_item
        #Print Accuracy
        self.print_accuracy(len(total_items),len(correct_items),"primary item evaluation")

    ## @brief Print accuracy for synthetic data
    def accuracy_syn_data(self):
        #___ JF Task Accuracy ___#
        total_tasks = []
        correct_tasks = []
        for JFTask in JFTask.objects.all():
            if JFTask.result is not None:
                total_tasks += JFTask
        for task in total_tasks:
            ground_truth = JFTasks_Dict[task.primary_item.pk][3]
            if task.result is ground_truth:
                correct_tasks += task
        #Print Accuracy
        self.print_accuracy(len(total_tasks),len(correct_tasks),"joinable filter")

        #___ Secondary Predicate Task Accuracy ___#
        total_tasks = []
        correct_tasks = []
        for task in SecPredTask.objects.all():
            if task.result is not None:
                total_tasks += task
        for task in total_tasks:
            ground_truth = SecPredTasks_Dict[task.secondary_item.name][3]
            if task.result is ground_truth:
                correct_tasks += task
        #Print Accuracy
        self.print_accuracy(len(total_tasks),len(correct_tasks),"secondary predicate")

    #______ Helpers for Accuracy ______#

    ## @brief print helper for accuracy functions
    # @param total_num number of tasks that reached consensus
    # @param correct_num number of tasks that were evaluated correctly
    # @param task_string string representing type of task
    def print_accuracy(self,total_num, correct_num, task_string):
        if total_num is not 0:
            accuracy = correct_num/total_num*100
        else:
            accuracy = 100
        print str(correct_num) + " out of " + str(total_num) + " " + task_string + " tasks were correct."
        print task_string + " Accuracy is " + str(accuracy)

    ## @brief helper for accuracy_real_data()
    # @param answer_list list of worker responses
    def determine_ground_truth(self,answer_list):
        yes_votes = 0
        no_votes = 0
        for answer in answer_list:
            if answer is 1:
                yes_votes += 1
            elif answer is 0:
                no_votes += 0
        return yes_votes > no_votes
    
    ## @brief resets database after a simulation
    def reset_database(self):
        # TODO finish this
        #empty models
        PrimaryItem.objects.all().delete()
        SecondaryItem.objects.all().delete()
        Worker.objects.all().delete()
        TaskStats.objects.all().delete()
        JFTask.objects.all().delete()
        FindPairsTask.objects.all().delete()
        JoinPairTask.objects.all().delete()
        PJFTask.objects.all().delete()
        SecPredTask.objects.all().delete()
        
        # Get data we want from these models before calling reset_database
        Estimator.objects.all().delete()
        TaskStats.objects.all().delete()
        FStatistic.objects.all().delete()
        JFTask.objects.all().delete()
        FindPairsTask.objects.all().delete()
        JoinPairTask.objects.all().delete()
        PJFTask.objects.all().delete()
        SecPredTask.objects.all().delete()


        #clear dictionaries #TODO is this necessary since they're within the class
        JFTasks_Dict.clear()
        FindPairsTask.clear()
        JoinPairTasks_Dict.clear()
        PJFTasks_Dict.clear()
        SecPredTasks_Dict.clear()

        self.sim_time = 0
        self.num_tasks_completed = 0




    ## @brief generates random 13-letter worker ids and populates the list worker_ids
    def generate_worker_ids(self):
        for n in range(toggles.NUM_WORKERS):
            letters = string.ascii_letters
            worker_id = ''.join(random.choice(letters) for i in range(13))
            self.worker_ids += [worker_id]

    # optimal for comparison that runs all the true influential restaurants before the false ones ## <<< only useful in real data simulations

    ## @brief runs run_sim with the same settings NUM_SIMS times
    def run_multi_sims(self):
        results_list = []
        for i in range(toggles.NUM_SIMS):
            results_list.append(self.run_sim())
            self.reset_database()
            #more processing happens here
        #more stuff happens here

    ## @brief Main function for running a simmulation. Changes to the simmulation can be made in toggles
    def run_sim(self):
        random.seed()

        # LOAD DATA
        estimator = Estimator.objects.create()
        jf_task_stats = TaskStats.objects.create(task_type=0)
        find_pairs_task_stats = TaskStats.objects.create(task_type=1)
        join_pairs_task_stats = TaskStats.objects.create(task_type=2)
        prejoin_task_stats = TaskStats.objects.create(task_type=3)
        sec_pred_task_stats = TaskStats.objects.create(task_type=4)

        if toggles.REAL_DATA is True:
            self.load_primary_real() #load primary list
            self.load_real_data() #load worker responses into dictionaries
        else:
            syn_load_list() #load primary list
            if JOIN_TYPE == 0: # joinable filter join
                syn_load_joinable_filter_tasks(self.JFTasks_Dict)
            elif JOIN_TYPE == 1: # item-wise join
                syn_load_find_pairs_tasks(self.FindPairsTasks_Dict)
                syn_load_sec_pred_tasks(self.SecPredTasks_Dict)
            elif JOIN_TYPE == 2: # pre-join filtered join
                #TODO load secondary list
                #TODO load prejoin filter tasks
                syn_load_join_pair_tasks(self.JoinPairTasks_Dict)
                syn_load_sec_pred_tasks(self.SecPredTasks_Dict)

        self.generate_worker_ids()
        
        while(PrimaryItem.objects.filter(is_done=False).exists()): #TODO is this the while loop we want to use?
            
            # pick worker
            worker_id = random.choice(self.worker_ids)

            # CHOOSE TASK
            task = choose_task(worker_id, estimator)
            if type(task) is JFTask:
                task_type = 0
                my_item = task.primary_item.pk
                (prim, sec, times, responses) = self.JFTasks_Dict[my_item]
            elif type(task) is FindPairsTask:
                task_type = 1
                my_item = task.primary_item.pk
                (prim, sec, times, responses) = self.FindPairsTasks_Dict[my_item]
            elif type(task) is JoinPairTask:
                task_type = 2
                # my_item = task.primary_item.pk
                # my_item = task.secondary_item.name
                # (prim, sec, times, responses) = self.JoinPairTasks_Dict[my_item]
                (prim, sec, times, responses) = ("these", "are", "placeholder", "values")
            elif type(task) is PJFTask:
                task_type = 3
                # my_item = task.primary_item.pk
                # (prim, sec, times, responses) = self.PJFTasks_Dict[my_item]
                (prim, sec, times, responses) = ("these", "are", "placeholder", "values")
            elif type(task) is SecPredTask:
                task_type = 4
                print(task)
                my_item = task.secondary_item.name
                print task.secondary_item
                (prim, sec, times, responses) = self.SecPredTasks_Dict[my_item]

            # ISSUE TASK
            #choose a (matching) time and response for the task
            if toggles.REAL_DATA:
                ind = random.randint(0, len(times))
                task_time = times[ind]
                task_answer = responses[ind]
            else:
                task_time = times
                task_answer = responses

            if sec is not "NA":
                sec = SecondaryItem.objects.get(name=sec).pk
            else:
                sec = None
            

            # UPDATE STATE AFTER TASK
            gather_task(task_type,task_answer,task_time,prim,sec)
            
            self.sim_time += task_time
            self.num_tasks_completed += 1

        
        self.sim_time_arr += [self.sim_time]
        self.num_tasks_completed_arr += [self.num_tasks_completed]

        #when finished: 
            # compare results to ground truth to determine accuracy
            # print and return cost statistics (return so we can run multiple sims and keep track of their results)
            # somehow use above data to add to generate graphs

        #statistics to export: accuracy, worker-time-cost, task-number-cost

    # represent simulation results ##