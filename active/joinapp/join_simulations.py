
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
    


    ### settings ###


    #####################################################################################
	#____________________________________ FUNCTIONS ____________________________________#
    #####################################################################################

    #_____________________ Loading Data _____________________ #
    
    def load_primary_real(self):
        """
        Loads in primary list
        """

        ID = 0

        f = open( PRIMARY_LIST, 'r')
        for line in f:
            line = line.rstrip ('\n')
            item = PrimaryItem.objects.create(item_id = ID, name = line)
            
            try:
                item.save()
            except:
                print "Error reading item ", ID
            ID += 1 
        f.close()
    
    def load_real_data(self):
        """
        Loads the MTurk data from a csvfile
        """
        #TODO implement time taken (dependent on IT_Task model)
        with open(REAL_DATA_CSV, mode = 'r') as csv_file:
            csv_reader = csv.reader(csv_file, delimeter = ',')
            line_count = 0
            for row in csv_reader:
                try:
                    task_type = row["TASK TYPE COL"]
                    prim_item = row["PRIMARY ITEM COL"]
                    sec_item = row["SECONDARY ITEM COL"]
                    time_taken = row["TIME DURATION COL"]
                    worker_response = row["WORKER RESPONSE COL"]
                    
                    if question is "eval_joinable_filter":
                        item_task, created = JFTask.objects.get_or_create( primary_item = prim_item)
                        item_task. #increment number of tasks
                        item_task. #increment total time
                        binary_worker_vote(item_task, worker_response, line_count)
                    elif question is "eval_sec_pred":
                        item_task, created = SecPredTask.objects.get_or_create(secondary_item = sec_item)
                        item_task. #increment number of tasks
                        item_task. #increment total time
                        binary_worker_vote(item_task, worker_response, line_count)
                    elif question is "eval_join_cond":
                        item_task, created = JoinPairTask.objects.get_or_create(primary_item = prim_item, secondary_item = sec_item)
                        item_task. #increment number of tasks
                        item_task. #increment total time
                        binary_worker_vote(item_task, worker_response, line_count)
                    elif question is "list_secondary": 
                        #TODO implement this: it depends on how we are parsing
                        item_task, created = FindPairsTask.objects.get_or_create( primary_item = prim_item)

                        secondary_items = worker_response.split("{{NEWENTRY}}")
                        for secondary_item in secondary_items:
                            item_task, created = 

                        #find secondary item
                        #get or create the IT_Pair
                        #update votes according to whether or not it was created and how many times it has seen this primary item       
                except:
                    print "There was an error reading line", line_count 
                
                line_count += 1

        def binary_worker_vote(item_task, worker_response, line_count):
            """
            Helper function for load_real_data: updates yes/no votes for a task given a worker response
            """
            if worker_response is "1":
                item_task.yes_votes += 1
            elif worker_response is "0":
                item_task.no_votes += 1
            else:
                print "Error evaluating worker vote on line", line_count

        def get_secondary_items(row):
            """
            Helper function for load_real_data: gets list of secondary items from a list_secondary type of task
            """
            secondary_items = row.split("{{NEWENTRY}}")


    ## ground truth determination ##
    # way to compare results from simulation with ground truth


    ## give task real and give task synthetic 
        """ creates a task based on the current state of the simmulation of one of the possible task model types"""


    ## reset database for multiple runs ##
    ## reset completely ##


    ## optimal for comparison that runs all the true influential restaurants before the false ones ## <<< only useful in real data simulations
    ## run simulation ##



    ## represent simulation results ##