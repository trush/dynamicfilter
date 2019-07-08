import random
import string
import csv
import numpy as np
import toggles
from models.items import *
from models.task_management_models import *
from models.estimator import *
from views_helpers import *
from django.test import *
import random
from synthetic_data import *
import matplotlib.pyplot as graph
from os import path

## @brief Functionality for testing the join algorithm on non-live data
class JoinSimulation():

    ## list holding worker IDs for the simulation
    worker_ids = []

    ## Total number of tasks issued/completed in one simulation
    num_tasks_completed = 0
    # [Joinable Filter, Find Pairs on Primaries, Join Pairs, PJF, Secondary Predicates, Find Pairs on Secondaries]
    # Index is task type
    num_tasks_breakdown = [0,0,0,0,0,0]

    ## Amount of worker-time spent during the simulation
    sim_time = 0
    # [Joinable Filter, Find Pairs on Primaries, Join Pairs, PJF, Secondary Predicates, Find Pairs on Secondaries]
    # Index is task type
    sim_time_breakdown = [0,0,0,0,0,0]

    ## For graphing # of primary items left vs. number of tasks completed
    # number of primary items left
    num_prim_left = []

    #_____ For tests that run multiple simulations _____#

    ## Total number of tasks issued/completed in each of multiple simulations
    num_tasks_completed_arr = []
    num_tasks_breakdown_arr = [[],[],[],[],[],[]]
    ## Amount of worker-time spent during each of multiple simulations
    sim_time_arr = []
    sim_time_breakdown_arr = [[],[],[],[],[],[]]

    ## Number of unnecessary tasks issued:
    num_wasted_tasks = 0 #TODO
    wasted_time = 0 #TODO
    
    
    #_____ For real data simulations only _____#

    ## Number of primary items that are correctly evaluated
    num_item_correct_eval = 0
    

    #__________________________________  Dictionaries ________________________________#

    ## Key: primary item pk <br>
    ## Value: (primary item pk, "NA", time taken list, worker response list/ground truth)
    JFTasks_Dict = dict()

    ## Key: primary item pk <br>
    ## Value: (primary item pk, "NA", time taken list, worker response list/ground truth)
    FindPairsTasks_Dict = dict() 

    ## Key: secondary item name <br>
    ## Value: ("None", secondary item name, time taken list, worker response list/ground truth)
    FindPairsSecTasks_Dict = dict() 

    ## Key: secondary item name <br>
    ## Value: ("NA", secondary item name, time taken list, worker response list/ground truth)
    SecPredTasks_Dict = dict() 

    ## Key: (primary item pk, secondary item name) <br>
    ## Value: (pjf, time taken list, worker response list/ground truth )
    JoinPairTasks_Dict = dict() 

    ## Key: secondary item name <br>
    ## Value: ("NA", secondary item name, time taken list, worker response list/ground truth)
    SecPJFTasks_Dict = dict()

    ## Key: primary item pk <br>
    ## Value: (primary item pk, "NA", time taken list, worker response list/ground truth)
    PrimPJFTasks_Dict = dict()

    ## Key: fake secondary item name <br>
    ## Value: ("NA", fake item name, time taken, ground truth)
    FakeSecPredTasks_Dict = dict()
    #_____________________ Loading Data _____________________ #
    
    ## @brief Loads primary list into database
    def load_primary_real(self):
        fn = path.join(path.dirname(__file__), PRIMARY_LIST)
        f = open( fn, 'r')
        for line in f:
            try:
                line = line.rstrip ('\n')
                item = PrimaryItem.objects.create(name = line)
            except:
                print "Error reading item "
        f.close()

    def load_real_data(self):
        if JOIN_TYPE == 0:
            fn = path.join(path.dirname(__file__), REAL_DATA_JF)
            with open(fn, mode = 'r') as csv_file:
                csv_reader = csv.reader(csv_file, delimiter = ',')
                line_count = 0
                for row in csv_reader:
                    primary_item = str(row[1][2:-1]) # to remove parentheses
                    time_taken = row[3]
                    worker_vote = row[4]
                    try:
                        primary_item_pk = PrimaryItem.objects.get(name = primary_item).pk
                        if primary_item_pk in self.JFTasks_Dict:
                            value = self.JFTasks_Dict[primary_item_pk]
                        else:
                            value = (primary_item_pk,"None",[],[]) 
                        value[2].append(float(time_taken)) #add assignment time to hit
                        value[3].append(int(worker_vote)) #add worker answer to hit
                        self.JFTasks_Dict[primary_item_pk] = value

                    except:
                        print "Error reading in row ", line_count
                    line_count += 1
        else:
            if JOIN_TYPE >= 1 and JOIN_TYPE < 3:
                fn = path.join(path.dirname(__file__), REAL_DATA_FP)
                with open(fn, mode = 'r') as csv_file:
                    csv_reader = csv.reader(csv_file, delimiter = ',')
                    line_count = 0
                    for row in csv_reader:
                        primary_item = str(row[1][2:-1]) # to remove parentheses
                        time_taken = row[3]
                        worker_vote = parse_pairs(row[4])
                    try:
                        primary_item_pk = PrimaryItem.objects.get(name = primary_item).pk
                        if primary_item_pk in self.FindPairsTasks_Dict:
                            value = self.FindPairsTasks_Dict[primary_item_pk]
                        else:
                            value = (primary_item_pk,"None",[],[])
                        value[2].append(float(time_taken)) #add assignment time to hit
                        value[3].append(worker_vote) # add worker answer to hit
                        self.FindPairsTasks_Dict[primary_item_pk] = value

                    except:
                        print "Error reading in row ", line_count
                    line_count += 1

            fn = path.join(path.dirname(__file__), REAL_DATA_SEC_PRED)
            with open(fn, mode = 'r') as csv_file:
                csv_reader = csv.reader(csv_file, delimiter = ',')
                line_count = 0
                for row in csv_reader:
                    secondary_item = row[1][2:-1] # to remove parentheses
                    time_taken = row[3]
                    worker_vote = row[4]
                    try:
                        if secondary_item in self.SecPredTasks_Dict:
                            value = self.SecPredTasks_Dict[secondary_item]   
                        else:
                            value = ("None", secondary_item,[],[])

                        value[2].append(float(time_taken)) #add assignment time to hit
                        value[3].append(int(worker_vote)) #add worker answer to hit
                        self.SecPredTasks_Dict[secondary_item] = value

                    except:
                        print "Error reading in row ", line_count
                    line_count += 1

    # ## @brief Loads the MTurk data from a csvfile and populates the answer dictionaries
    # def load_real_data(self):
    #     with open(REAL_DATA_CSV, mode = 'r') as csv_file:
    #         csv_reader = csv.reader(csv_file, delimeter = ',')
    #         line_count = 0
    #         for row in csv_reader:
    #             #csv rows are organized like this: "Hit Id, Hotel, Restaurant, Assignment Id, Assignment Status, Time Taken, workervote, feedback"
    #             primary_item = row[1]
    #             secondary_item = row[2]
    #             time_taken = row[5]
    #             worker_vote = row[6]
    #             try:
    #                 if task_type is "eval_joinable_filter":
    #                     primary_item_pk = PrimaryItem.objects.get(name = primary_item).pk 
    #                     if primary_item_pk in self.JFTasks_Dict:
    #                         value = self.JFTasks_Dict[primary_item_pk]
    #                     else:
    #                         value = (primary_item_pk,"NA",[],[]) 
    #                     value[2] += [time_taken] #add assignment time to hit
    #                     value[3] += [worker_vote] #add worker answer to hit
    #                     self.JFTasks_Dict[primary_item_pk] = value

    #                 elif task_type is "list_secondary":
    #                     primary_item_pk = PrimaryItem.objects.get(name = primary_item).pk 
    #                     if primary_item_pk in self.FindPairsTasks_Dict:
    #                         value = self.FindPairsTasks_Dict[primary_item.pk] 
    #                     else:
    #                         value = (primary_item_pk,"NA",[],[])
    #                     value[2] += [time_taken] #add assignment time to hit
    #                     value[3] += [worker_vote] #add worker answer to hit
    #                     self.FindPairsTasks_Dict[primary_item_pk] = value

    #                 elif task_type is "eval_sec_pred":
    #                     if secondary_item in self.SecPredTasks_Dict:
    #                         value = self.SecPredTasks_Dict[secondary_item]   
    #                     else:
    #                         value = ("NA", secondary_item,[],[])
    #                     value[2] += [time_taken] #add assignment time to hit
    #                     value[3] += [worker_vote] #add worker answer to hit

    #                 elif task_type is "eval_pjf":
    #                     if primary_item is not "None": #primary item pjf
    #                         primary_item_pk = PrimaryItem.objects.get(name = primary_item).pk
    #                         if primary_item_pk in self.PrimPJFTasks_Dict:
    #                             value = self.PrimPJFTasks_Dict[primary_item_pk]
    #                         else:
    #                             value = (primary_item_pk, "NA", [], [])
    #                         value[2] += [time_taken]
    #                         value[3] += [worker_vote]
    #                     else: #secondary item pjf
    #                         if secondary_item in self.SecPJFTasks_Dict:
    #                             value = self.SecPJFTasks_Dict[secondary_item]
    #                         else:
    #                             value = ("NA", secondary_item, [],[])
    #                         value[2] += [time_taken]
    #                         value[3] += [worker_vote]
    #                 elif task_type is "eval_join_cond": #for pre-join filtered join
    #                     primary_item_pk = PrimaryItem.objects.get(name = primary_item).pk
    #                     key = (primary_item_pk,secondary_item)
    #                     if key in self.JoinPairTasks_Dict:
    #                         value = self.JoinPairTasks_Dict[key]
    #                     else:
    #                         value = ("PJF", [],[]) #TODO pjf.....
    #                     value[1] += [time_taken]
    #                     value[2] += [worker_vote]
    #             except:
    #                 print "Error reading in row ", line_count
    #             line_count += 1


    #___________________ Accuracy ______________________#

    ## @brief Print accuracy for real data
    def accuracy_real_data(self):
        #___ JF Task Accuracy ___#
        total_tasks = []
        correct_tasks = 0
        for task in JFTask.objects.all():
            if task.result is not None:
                total_tasks += [task]
        for task in total_tasks:
            ground_truth = self.determine_ground_truth(self.JFTasks_Dict[task.primary_item.name][3])
            if task.result is ground_truth:
                correct_tasks += 1
        #Print Accuracy
        self.print_accuracy(len(total_tasks),correct_tasks,"joinable filter")

        #___ Secondary Predicate Task Accuracy ___#
        total_tasks = []
        correct_tasks = 0
        for task in SecPredTask.objects.all():
            if task.result is not None:
                total_tasks += [task]
        for task in total_tasks:
            ground_truth = self.determine_ground_truth(self.SecPredTasks_Dict[task.secondary_item.name][3])
            if task.result is ground_truth:
                correct_tasks += 1
        #Print Accuracy
        self.print_accuracy(len(total_tasks),correct_tasks,"secondary predicate")
        
        #___ Query Accuracy __#
        total_items = []
        correct_items = 0
        for primary_item in PrimaryItem.objects.all():
            if primary_item.is_done is True:
                total_items += [primary_item]
        for primary_item in total_items:
            ground_truth = self.determine_ground_truth(self.JFTasks_Dict[task.primary_item.name][3])
            if primary_item.eval_result is ground_truth:
                correct_items += 1
        #Print Accuracy
        self.print_accuracy(len(total_items),correct_items,"primary item evaluation")

    ## @brief Print accuracy for synthetic data
    def accuracy_syn_data(self):
        #___ JF Task Accuracy ___#
        if JOIN_TYPE == 0:
            total_tasks = []
            correct_tasks = 0
            for task in JFTask.objects.all():
                if task.result is not None:
                    total_tasks += [task]
            for task in total_tasks:
                ground_truth = self.JFTasks_Dict[task.primary_item.name][3]
                if task.result is True and ground_truth is 1:
                    correct_tasks += 1
                elif task.result is False and ground_truth is 0:
                    correct_tasks += 1
            #Print Accuracy
            self.print_accuracy(len(total_tasks),correct_tasks,"joinable filter")

            print "" #newline

        #_____ Pre-Join Filter Task Accuracy _____#
        if JOIN_TYPE == 2:
            total_tasks = []
            correct_tasks = 0
            for task in PJFTask.objects.all():
                if task.consensus is True:
                    total_tasks += [task]
            for task in total_tasks:
                if task.primary_item is not None:
                    ground_truth = self.PrimPJFTasks_Dict[task.primary_item.name][3]
                    if task.primary_item.pjf == ground_truth:
                        correct_tasks += 1
                elif task.secondary_item is not None:
                    ground_truth = self.SecPJFTasks_Dict[task.secondary_item.name][3]
                    if task.secondary_item.pjf == ground_truth:
                        correct_tasks += 1
            self.print_accuracy(len(total_tasks),correct_tasks,"pre-join filter")
            
            print "" #newline

        #___ Secondary Predicate Task Accuracy ___#
        total_tasks = []
        correct_tasks = 0
        for task in SecPredTask.objects.all():
            if task.result is not None:
                total_tasks += [task]
        for task in total_tasks:
            if int(task.secondary_item.name) < NUM_SEC_ITEMS:
                a,b,c,ground_truth = self.SecPredTasks_Dict[task.secondary_item.name]
            else:
                a,b,c,ground_truth = self.FakeSecPredTasks_Dict[task.secondary_item.name]
            if task.result is ground_truth:
                correct_tasks += 1
        #Print Accuracy
        self.print_accuracy(len(total_tasks),correct_tasks,"secondary predicate")

        #___ Find Pairs Accuracy ___#
        false_negatives = 0
        true_positives = 0
        false_positives = 0
        true_negatives =0
        if JOIN_TYPE == 1 or JOIN_TYPE == 1.5:
            for prim in PrimaryItem.objects.all():
                found_list = []
                for sec in prim.secondary_items.all():
                    sec_name = 'secondary item '+ sec.name + '; ' + sec.name + ' address'
                    found_list += [sec_name]
                true_list = parse_pairs(self.FindPairsTasks_Dict[prim.name][3])
                for item in true_list:
                    if item not in found_list:
                        false_negatives += 1
                    else:
                        true_positives += 1

                for item in found_list:
                    if item not in true_list:
                        false_positives += 1
                #true_negatives += (len(FAKE_SEC_ITEM_LIST) - false_positives)
            print ""
            print "We missed " + str(false_negatives) + " secondary items"
            print "We had " + str(false_positives) + " extra items" 
        elif JOIN_TYPE >= 3:
            for sec in SecondaryItem.objects.all():
                found_list = []
                for prim in sec.primary_items.all():
                    prim_name = "primary item " + prim.name + "; " + prim.name + " address"
                    found_list += [prim_name]
                true_list = parse_pairs(self.FindPairsSecTasks_Dict[sec.name][3])
                for item in true_list:
                    if item not in found_list:
                        false_negatives += 1
                    else:
                        true_positives += 1
                for item in found_list:
                    if item not in true_list:
                        false_positives += 1
            print ""
            print "We missed " + str(false_negatives) + " primary items"
            print "We had " + str(false_positives) + " extra items"
        
        print "" #newline

        #___ Primary Item Task Accuracy ___#
        correct_prim_items = 0
        for prim in PrimaryItem.objects.all():
            ground_truth = False #assume every primary fails the join
            if self.JFTasks_Dict[prim.name][3] is 1:
                ground_truth = True
            if prim.eval_result is ground_truth:
                correct_prim_items += 1
        self.print_accuracy(PrimaryItem.objects.all().count(),correct_prim_items, "PRIMARY ITEMS")
        # AMBER ADDED FOR TESTIING 
        prim_accuracy = float(correct_prim_items) / float(PrimaryItem.objects.all().count())
        return prim_accuracy,false_negatives, true_positives, false_positives, true_negatives



    #______ Helpers for Accuracy ______#

    ## @brief print helper for accuracy functions
    # @param total_num number of tasks that reached consensus
    # @param correct_num number of tasks that were evaluated correctly
    # @param task_string string representing type of task
    def print_accuracy(self,total_num, correct_num, task_string):
        if total_num is not 0:
            accuracy = float(correct_num)/float(total_num)*100
        else:
            accuracy = 100
        print "* " + str(correct_num) + " out of " + str(total_num) + " " + task_string + " tasks were correct."
        print "* " + task_string + " Accuracy is " + str(accuracy) + "%"

    ## @brief helper for accuracy_real_data()
    # @param answer_list list of worker responses
    def determine_ground_truth(self,answer_list):
        yes_votes = 0
        no_votes = 0
        for answer in answer_list:
            if answer is 1:
                yes_votes += 1
            elif answer is 0:
                no_votes += 1
        return yes_votes > no_votes
    
    ## @brief resets database after a simulation
    def reset_database(self):
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


        #clear dictionaries
        self.JFTasks_Dict.clear()
        self.FindPairsTasks_Dict.clear()
        self.JoinPairTasks_Dict.clear()
        self.PrimPJFTasks_Dict.clear()
        self.SecPJFTasks_Dict.clear()
        self.SecPredTasks_Dict.clear()

        self.sim_time = 0
        self.num_tasks_completed = 0
        self.num_prim_left = []
        
        self.num_tasks_breakdown = [0,0,0,0,0,0]
        self.sim_time_breakdown = [0,0,0,0,0,0]




    ## @brief generates random 13-letter worker ids and populates the list worker_ids
    def generate_worker_ids(self):
        for n in range(toggles.NUM_WORKERS):
            letters = string.ascii_letters
            worker_id = ''.join(random.choice(letters) for i in range(13))
            self.worker_ids += [worker_id]

    # optimal for comparison that runs all the true influential restaurants before the false ones ## <<< only useful in real data simulations

    ## @brief runs run_sim with the same settings NUM_SIMS times
    def run_multi_sims(self): #TODO RESET THIS
        # results_list = []
        # join_selectivity_arr = []
        # num_jf_assignments_arr = []
        # num_find_pairs_assignments_arr = []
        # num_sec_pred_assignments_arr = []
        # time_arr = []
        # total_assignments_arr = []
        # num_prim_left_arr = []
        prim_accuracy = []
        false_negatives = []
        true_positives = []
        false_positives = []
        true_negatives = []
        task_num = []

        # results list is a list of tuples in the form (join_selectivity, num_jf_tasks, num_find_pairs_tasks, num_sec_pred_tasks, self.sim_time, self.num_tasks_completed)
        for i in range(toggles.NUM_SIMS):
            print "---------------------------------------------------------------------"
            j = i+1
            print "Running simulation",j,"out of",toggles.NUM_SIMS
            results = self.run_sim()
            prim_accuracy.append(results[0])
            false_negatives.append(results[1])
            true_positives.append(results[2])
            false_positives.append(results[3])
            true_negatives.append(results[4])
            task_num.append(results[5])

            # results_list.append(results)
            # join_selectivity_arr.append(results[0])
            # num_jf_assignments_arr.append(results[1])
            # num_find_pairs_assignments_arr.append(results[2])
            # num_sec_pred_assignments_arr.append(results[3])
            # time_arr.append(results[4])
            # total_assignments_arr.append(results[5])
            # num_prim_left_arr.append(self.num_prim_left)
            
            self.reset_database()
            #more processing happens here
        print "Average Total Time:", np.mean(self.sim_time_arr)

        print ""
        print "Average Time on Joinable Filter Tasks:", np.mean(self.sim_time_breakdown_arr[0])
        print "Average Time on Find Pairs Tasks (Primary):", np.mean(self.sim_time_breakdown_arr[1])
        print "Average Time on Join Pair Tasks:", np.mean(self.sim_time_breakdown_arr[2])
        print "Average Time on PJF Tasks:", np.mean(self.sim_time_breakdown_arr[3])
        print "Average Time on Secondary Predicate Tasks:", np.mean(self.sim_time_breakdown_arr[4])
        print "Average Time on Find Pairs Tasks (Secondary):", np.mean(self.sim_time_breakdown_arr[5])
        
        print ""
        print "Average Number of Tasks:", np.mean(self.num_tasks_completed_arr)
        print ""
        print "Average Number of Joinable Filter Tasks:", np.mean(self.num_tasks_breakdown_arr[0])
        print "Average Number of Find Pairs Tasks (Primary):", np.mean(self.num_tasks_breakdown_arr[1])
        print "Average Number of Join Pair Tasks:", np.mean(self.num_tasks_breakdown_arr[2])
        print "Average Number of PJF Tasks:", np.mean(self.num_tasks_breakdown_arr[3])
        print "Average Number of Secondary Predicate Tasks:", np.mean(self.num_tasks_breakdown_arr[4])
        print "Average Number of Find Pairs Tasks (Secondary):", np.mean(self.num_tasks_breakdown_arr[5])


        
        

        print "Average Query Accuracy:", np.mean(prim_accuracy)
        # print "false_negatives", np.mean(false_negatives)
        # print "true_positives", np.mean(true_positives)
        # print "false_positives", np.mean(false_positives)
        # print "true_negatives", np.mean(true_negatives)
        # print "find pairs", np.mean(task_num)
        if JOIN_TYPE == 1 or JOIN_TYPE == 1.5 or JOIN_TYPE >= 3:
            precision = np.mean(true_positives) / (np.mean(true_positives) + np.mean(false_positives))
            recall = np.mean(true_positives) / (np.mean(true_positives) + np.mean(false_negatives))
            print ""
            print "For Itemwise Only:"
            print "Average Precision:", precision
            print "Average Recall:", recall
        # print "Times:", time_arr
        # print "Find Pairs Assignments:", num_find_pairs_assignments_arr
        # print "Sec Pred Assignments:", num_sec_pred_assignments_arr
        #more stuff happens here

        #return (join_selectivity_arr, num_jf_assignments_arr, num_find_pairs_assignments_arr, num_sec_pred_assignments_arr, time_arr, total_assignments_arr, num_prim_left_arr)

    ## @brief Main function for running a simmulation. Changes to the simmulation can be made in toggles
    def run_sim(self):
        random.seed()

        #__________________________ LOAD DATA __________________________ #
        estimator = Estimator.objects.create()
        jf_task_stats = TaskStats.objects.create(task_type=0)
        find_pairs_task_stats = TaskStats.objects.create(task_type=1)
        join_pairs_task_stats = TaskStats.objects.create(task_type=2)
        prejoin_task_stats = TaskStats.objects.create(task_type=3)
        sec_pred_task_stats = TaskStats.objects.create(task_type=4)
        find_pairs_sec_task_stats = TaskStats.objects.create(task_type=5)

        if toggles.REAL_DATA is True:
            self.load_primary_real() #load primary list
            self.load_real_data() #load worker responses into dictionaries
        else:
            syn_load_list()

            #NOTE: Added to test IW on secondaries, assuming we already have 2ndary list
            if HAVE_SEC_LIST is True:
                syn_load_second_list()
                estimator.has_2nd_list = True
                estimator.save()

            syn_load_everything(self)

        self.generate_worker_ids()

        # list of assignments in progress, to be used in timed simulations
        active_assignments = {}
        #holds the keys for the assignments
        assignment_keys = {}
        key_counter = 0

        # for printing stats at end
        num_join_pairs_assignments = 0

        while(PrimaryItem.objects.filter(is_done=False).exists()) and (not SecondaryItem.objects.all().exists() or  SecondaryItem.objects.filter(is_done=False).exists()):
            # pick worker
            worker_id = random.choice(self.worker_ids)

            self.num_prim_left += [PrimaryItem.objects.filter(is_done=False).count()]
            #__________________________  CHOOSE TASK __________________________#
            if JOIN_TYPE == 0: # joinable filter
                task = choose_task_JF(worker_id)
            elif JOIN_TYPE == 1: # item-wise join
                task = choose_task_IW(worker_id, estimator)
            elif JOIN_TYPE == 1.5: # item-wise join
                task = choose_task_IW1(worker_id, estimator)
            elif JOIN_TYPE == 2:
                task = choose_task_PJF(worker_id, estimator)
            elif JOIN_TYPE == 3.1:
                task = choose_task_IWS1(worker_id, estimator)
            elif JOIN_TYPE == 3.2:
                task = choose_task_IWS2(worker_id, estimator)
            else: #JOIN_TYPE is 3.3:
                task = choose_task_IWS3(worker_id, estimator)

    
            if type(task) is JFTask:
                task_type = 0
                my_item = task.primary_item.name
                hit = self.JFTasks_Dict[my_item]
            elif type(task) is FindPairsTask:
                if task.primary_item is not None:
                    task_type = 1
                    my_item = task.primary_item.name
                    hit = self.FindPairsTasks_Dict[my_item]
                elif task.secondary_item is not None:
                    task_type = 5
                    my_item = task.secondary_item.name
                    hit = self.FindPairsSecTasks_Dict[my_item]
            elif type(task) is JoinPairTask:
                task_type = 2
                my_prim_item = task.primary_item.name
                my_sec_item = task.secondary_item.name
                hit = self.JoinPairTasks_Dict[(my_prim_item, my_sec_item)]
                num_join_pairs_assignments += 1
            elif type(task) is PJFTask:
                task_type = 3
                if task.primary_item is not None:
                    #TODO unstr
                    my_item = task.primary_item.name
                    hit = self.PrimPJFTasks_Dict[my_item]
                else:
                    my_item = task.secondary_item.name
                    hit = self.SecPJFTasks_Dict[my_item]
            elif type(task) is SecPredTask:
                task_type = 4
                my_item = task.secondary_item.name
                # Check for fake items
                if REAL_DATA is False and int(my_item) >= NUM_SEC_ITEMS:
                    print "-----------------------A FAKE ITEM REACHED CONSENSUS-----------------------"
                    hit = self.FakeSecPredTasks_Dict[my_item]
                else:
                    hit = self.SecPredTasks_Dict[my_item]

            #__________________________  ISSUE TASK __________________________#
            #choose a (matching) time and response for the task
            if task_type is not 2:
                (prim,sec,time,answer) = hit
            else:
                (pjf,time,answer) = hit
                prim = my_prim_item
                sec = my_sec_item
            
            if toggles.REAL_DATA:
                ind = random.randint(0, len(time)-1) # for some reason this is inclusive
                task_time = time[ind]
                task_answer = answer[ind]
            else:
                if task_type is 4:
                    task_answer,task_time = syn_answer_sec_pred_task(hit)
                elif task_type is 3:
                    task_answer,task_time = syn_answer_pjf_task(hit)
                elif task_type is 2:
                    task_answer,task_time = syn_answer_join_pair_task(hit)
                elif task_type is 1 or task_type is 5:
                    task_answer,task_time = syn_answer_find_pairs_task(hit)
                elif task_type is 0:
                    task_answer,task_time = syn_answer_joinable_filter_task(hit)

            if sec is not "None":
                sec = SecondaryItem.objects.get(name=sec).name
            else:
                sec = None

            
            #__________________________ UPDATE STATE AFTER TASK __________________________ #
            if toggles.SIMULATE_TIME:
                fin_list = []
                for key in active_assignments:
                    active_assignments[key] -= toggles.TIME_STEP
                    if active_assignments[key] < 0:
                        fin_list.append(key)
                assignment_keys[key_counter] = (task_type,task_answer,task_time,prim,sec)
                active_assignments[key_counter] = task_time
                key_counter += 1
                for key in fin_list:
                    assignment = assignment_keys[key]
                    gather_task(assignment[0],assignment[1],assignment[2],assignment[3],assignment[4])
                    active_assignments.pop(key)
                    self.num_tasks_completed += 1
                    self.num_tasks_breakdown[task_type] += 1
                    self.sim_time += task_time
                    self.sim_time_breakdown[task_type] += float(task_time)
                    
            else:
                gather_task(task_type,task_answer,task_time,prim,sec)
                
                self.sim_time += float(task_time)
                self.sim_time_breakdown[task_type] += float(task_time)
                self.num_tasks_completed += 1
                self.num_tasks_breakdown[task_type] += 1

            #update chao estimator
            estimator.refresh_from_db()
            estimator.chao_estimator()

        if JOIN_TYPE > 3.0:
            for prim in PrimaryItem.objects.all():
                prim.refresh_from_db()
                prim.found_all_pairs = True
                prim.update_state()
                prim.save()

        #simulate time cleanup loop, gets rid of ungathered tasks
        if toggles.SIMULATE_TIME:
            fin_list = []
            print active_assignments
            for key in active_assignments:
                fin_list.append(key)
            for key in fin_list:
                active_assignments.pop(key)
                self.num_tasks_completed += 1
                self.sim_time += task_time
        
        self.sim_time_arr += [self.sim_time]
        self.num_tasks_completed_arr += [self.num_tasks_completed]

        for i in range(6):               
            self.sim_time_breakdown_arr[i].append(self.sim_time_breakdown[i])
            self.num_tasks_breakdown_arr[i].append(self.num_tasks_breakdown[i])


        #__________________________ RESULTS __________________________#
        print "Finished simulation, printing results....."

        for item in PrimaryItem.objects.all():
            item.refresh_from_db()
        
        # if JOIN_TYPE is 1:
        #     overlap_list = []
        #     for item in SecondaryItem.objects.all():
        #         item.refresh_from_db()
        #         overlap_list += [item.num_prim_items]
        #     if overlap_list is []:
        #         print "NO SECONDARY ITEMS"
        #     else:
        #         i = max(overlap_list)
        #         while i >= 0:
        #             num_i_prims = SecondaryItem.objects.filter(num_prim_items = i).count()
        #             print "*", num_i_prims, "secondary item(s) were associated with", i, "primary items"
        #             i -= 1

        #         print ""
        #         print "Mean primary per secondary:", np.mean(overlap_list)
        #         print "Standard deviation primary per secondary:", np.std(overlap_list)
        #         print ""

        num_prim_pass = PrimaryItem.objects.filter(eval_result = True).count()
        num_prim_fail = PrimaryItem.objects.filter(eval_result = False).count()
        join_selectivity = float(num_prim_pass)/float(PrimaryItem.objects.all().count())
        num_jf_tasks = JFTask.objects.all().count()
        num_find_pairs_tasks = FindPairsTask.objects.all().count()
        # NOTE: this only works for a static algorithm
        num_join_pairs_tasks = JoinPairTask.objects.filter(has_same_pjf=True).count()
        num_sec_pred_tasks = SecPredTask.objects.all().count()

        num_jf_assignments = 0
        for jftask in JFTask.objects.all():
            num_jf_assignments += jftask.num_tasks
        num_find_pairs_assignments = 0
        for fptask in FindPairsTask.objects.all():
            num_find_pairs_assignments += fptask.num_tasks
        num_sec_pred_assignments = 0
        for sptask in SecPredTask.objects.all():
            num_sec_pred_assignments += sptask.num_tasks



        print "*", num_prim_pass, "items passed the query"
        print "*", num_prim_fail, "items failed the query"
        print "* Query selectivity:", join_selectivity
        print "* Worker time spent:", self.sim_time
        print "* Total number of tasks processed:", self.num_tasks_completed
        print "* # of joinable-filter tasks:", num_jf_tasks, "# of joinable-filter assignments:", num_jf_assignments
        print "* # of find pairs tasks:", num_find_pairs_tasks, "# of find pairs assignments:", num_find_pairs_assignments
        print "* # of join pairs tasks:", num_join_pairs_tasks, "# of join pairs assignments:", num_join_pairs_assignments
        print "* # of secondary predicate tasks:", num_sec_pred_tasks, "# secondary predicate assignments:", num_sec_pred_assignments
        print "* # of finished secondary predicate tasks:", SecPredTask.objects.exclude(result = None).count()
        print "* # of secondary items found:", SecondaryItem.objects.all().count(), " out of ", toggles.NUM_SEC_ITEMS, " total secondary items"
        print ""
        if REAL_DATA is True:
            self.accuracy_real_data() #does its own printing
        else:
            #self.accuracy_syn_data() #does its own printing
            accuracy_info = self.accuracy_syn_data() #does its own printing
        #return (join_selectivity, num_jf_assignments, num_find_pairs_assignments, num_sec_pred_assignments, self.sim_time[0], self.num_tasks_completed)
        return accuracy_info[0],accuracy_info[1],accuracy_info[2], accuracy_info[3],accuracy_info[4],num_find_pairs_assignments
