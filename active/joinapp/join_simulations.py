
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
                    elif task_tupe is "eval_pjf": #note that this name might be incorrect
                        self.PJFTasks_Dict[key]= value 
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
    def run_sim(self):




    ## represent simulation results ##