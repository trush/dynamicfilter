
import csv
from models import *

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
        Loads in real data from files into the database
        """

        ID = 0

        f = open( PRIMARY_LIST, 'r')
        for line in f:
            line = line.rstrip ('\n')
            item = Primary_Item.objects.create(item_id = ID, name = line)
            
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
        with open(REAL_DATA_CSV, mode = 'r') as csv_file:
            csv_reader = csv.reader(csv_file, delimeter = ',')
            line_count = 0
            for row in csv_reader:
                try:
                    task_type = row["TASK TYPE COL"]
                    prim_item = row["PRIMARY ITEM COL"]
                    sec_item = row["SECONDARY ITEM COL"]
                    time_taken = row["TIME DURATION COL"]
                    worker_vote = row["WORKER RESPONSE COL"]
                    
                    if question in ("eval_joinable_filter", "eval_sec_pred", "eval_join_cond"): #Yes/No Questions
                        #TODO implement time taken (dependent on IT_Task model)
                        item_task, created = IT_Pair.objects.get_or_create(task_type = task_type, primary_item = prim_item, secondary_item = sec_item)
                        if worker_vote is "1":
                            item_task.yes_votes += 1
                        elif worker_vote is "0":
                            item_task.no_votes += 1
                        else:
                            print "Error evaluating worker vote on line", line_count
                    elif question is "list_secondary": #List enumeration Queston
                        #TODO implement this: it depends on how we are parsing

                        #find secondary item
                        #get or create the IT_Pair
                        #update votes according to whether or not it was created and how many times it has seen this primary item
                        
                except:
                    print "There was an error reading line", line_count 
                
                line_count += 1




    ## ground truth determination ##
    # way to compare results from simulation with ground truth


    ## give task real and give task synthetic 
        """ creates a task based on the current state of the simmulation of one of the possible task model types"""


    ## reset database for multiple runs ##
    ## reset completely ##


    ## optimal for comparison that runs all the true influential restaurants before the false ones ## <<< only useful in real data simulations
    ## run simulation ##



    ## represent simulation results ##