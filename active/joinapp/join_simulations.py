
import csv
from models.items import *
from models.task_management_models import *

class JoinSimulation(TransactionTestCase):
    """
    Tests join algorithm on non-live data
    """

    ####################################################################################
	#__________________________________ DATA MEMBERS __________________________________#
    ####################################################################################

    # Total number of tasks issued/completed in the simulation
    num_tasks_completed = 0

    # Number of tasks issued/completed that did not contribute to consensus
    num_wasted_tasks = 0

    # Amount of worker-time spent during the simulation
    sim_time = 0


    #_____ For tests that run multiple simulations _____#

    # Total number of tasks issued/completed in each simulation
    num_tasks_completed_arr = []

    # Number of tasks issued/completed that did not contribute to consensus in each simulation
    num_wasted_tasks_arr = []

    # Amount of worker-time spent during each simulation
    sim_time_arr = []

    
    
    #_____ For real data simulations only _____#

    # Number of primary items that are correctly evaluated
    num_item_correct_eval = 0

    #
    sim_accuracy_arr = []
    

    #_________________ Dictionaries _______________#
    """
    Keys: (HitID,assignmentID)
    Values: (primary item id, secondary item id, time taken, worker response)
    """
    JFTasks_Dict = dict() 
    FindPairsTasks_Dict = dict() 
    PJFTasks_Dict = dict()
    SecPredTasks_Dict = dict() 
    JoinPairTasks_Dict = dict() 

    


    ### settings ###


    #####################################################################################
	#____________________________________ FUNCTIONS ____________________________________#
    #####################################################################################

    #_____________________ Loading Data _____________________ #
    
    def load_primary_real(self):
        """
        Loads in primary list
        """

        f = open( PRIMARY_LIST, 'r')
        for line in f:
            try:
                line = line.rstrip ('\n')
                item = PrimaryItem.objects.create(name = line)
            except:
                print "Error reading item "
        f.close()


    def load_real_data(self):
        """
        Loads the MTurk data from a csvfile and populates the answer dictionaries
        """
        with open(REAL_DATA_CSV, mode = 'r') as csv_file:
            csv_reader = csv.reader(csv_file, delimeter = ',')
            line_count = 0
            for row in csv_reader:
                try:
                    key = (row["HIT ID COL"],row["WORKER ID COL"] #TODO update column #s
                    value = (row["PRIMARY ITEM COL"], row["SECONDARY ITEM PK COL"], row["TIME TAKEN COL"], row["WORKER RESPONSE COL"]) #TODO update column #s

                    task_type = row["TASK TYPE COL"] #TODO update column #s
                    
                    if task_type is "eval_joinable_filter":
                        self.JFTasks_Dict[key] = value
                    elif task_type is "eval_sec_pred":
                        self.SecPredTasks_Dict[key] = value
                    elif task_type is "eval_join_cond":
                        self.JoinPairTasks_Dict[key] = value
                    elif task_type is "list_secondary": 
                        self.FindPairsTasks_Dict[key] = value   
                    elif task_type is "eval_pjf": #note that this name might be incorrect
                        self.PJFTasks_Dict[key]= value 
                except:
                    print "There was an error reading line", line_count 
                
                line_count += 1


    ## ground truth determination ##
    # way to compare results from simulation with ground truth

    ## reset database
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

        #clear dictionaries #TODO is this necessary since they're within the class
        JFTasks_Dict.clear()
        FindPairsTask.clear()
        JoinPairTasks_Dict.clear()
        PJFTasks_Dict.clear()
        SecPredTasks_Dict.clear()



        
    ## reset completely ##


    ## optimal for comparison that runs all the true influential restaurants before the false ones ## <<< only useful in real data simulations
    ## run simulation ##
    def run_sim(self):

        # LOAD DATA
        #TODO add task stats and estimator
        if REAL_DATA is True:
            self.load_primary_real() #load primary list
            self.load_real_data() #load worker responses into dictionaries
        else:
            syn_load_data() #load primary list
            if JOIN_TYPE = 0: # joinable filter join
                syn_load_joinable_filter_tasks(JFTasks_Dict)
            elif JOIN_TYPE = 1: # item-wise join
                syn_load_find_pairs_tasks(FindPairsTasks_Dict)
                syn_load_sec_pred_tasks(SecPredTasks_Dict)
            elif JOIN_TYPE = 2: # pre-join filtered join
                #TODO load secondary list
                #TODO load prejoin filter tasks
                syn_load_join_pair_tasks(JoinPairTasks_Dict)
                syn_load_sec_pred_tasks(SecPredTasks_Dict)
        
        while(PrimaryItem.objects.filter(is_done=False).count() is not 0)
            
            # TODO pick worker

            # CHOOSE TASK
            task = chooseTask()
            if type(task) is JFTask:
                task_type = 0
            elif type(task) is FindPairsTask:
                task_type = 1
            elif type(task) is JoinPairTask:
                task_type = 2
            elif type(task) is PJFTask:
                task_type = 3
            elif type(task) is SecPredTask:
                task_type = 4

            # ISSUE TASK
            # TODO how do we sample from the dictionaries to get worker response??
            task_answer = ""
            task_time = 0

            # UPDATE STATE AFTER TASK
            gather_task(task_type,task_answer,task_time)
        
        #when finished: 
            # compare results to ground truth to determine accuracy
            # print and return cost statistics (return so we can run multiple sims and keep track of their results)
            # somehow use above data to add to generate graphs

        #statistics to export: accuracy, worker-time-cost, task-number-cost

    ## represent simulation results ##