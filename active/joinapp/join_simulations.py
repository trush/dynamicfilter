
import csv

class JoinSimulation(TransactionTestCase):
    """
    Tests join algorithm on non-live data
    """

    ##################################################
	#_________________ DATA MEMBERS _________________#
    ##################################################

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


    ###############################################
    #_________________ FUNCTIONS _________________#
    ###############################################

    #_____ Loading Data _____#
        ### real data ###
        ### synthetic data ###
    
    def load_primary_real(self):
        """
        Loads in real data from files into the database
        """
        
        PRIMARY_LIST = #TODO path info
        ID = 0

        f = open( PRIMARY_LIST, 'r') #TODO path
        for line in f:
            line = line.rstrip ('\n')
            item = Primary_Item(item_id = ID, name = line)
            
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

        REAL_DATA_CSV = #TODO path info

        with open(REAL_DATA_CSV, mode = 'r') as csv_file:
            csv_reader = csv.reader(csv_file, delimeter = ',')
            line_count = 0
            for row in csv_reader:
                try:
                    question = row["QUESTIONS COL"]
                    prim_item = row["PRIMARY ITEM COL"]
                    time_taken = row["TIME DURATION COL"]
                    worker_vote = row["WORKER RESPONSE COL"]
                    
                    if question == "eval_joinable_filter":
                        item_task = IT_Pair(item_ID = prim_item, )
                    elif question == "eval_sec_pred":
                        #TODO
                    elif question == "eval_join_cond":
                        #TODO
                    elif question == "list_secondary":
                        #TODO
                except:
                    print "There was an error reading in line", line_count 




    ## ground truth determination ##
    # way to compare results from simulation with ground truth


    ## give task real and give task synthetic 
        """ creates a task based on the current state of the simmulation of one of the possible task model types"""


    ## reset database for multiple runs ##
    ## reset completely ##


    ## optimal for comparison that runs all the true influential restaurants before the false ones ## <<< only useful in real data simulations
    ## run simulation ##



    ## represent simulation results ##