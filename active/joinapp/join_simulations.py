#########
#########


class JoinSimulation(TransactionTestCase):
    """
    Tests join algorithm on non-live data
    """

    ################
	# DATA MEMBERS #
	################

    # Total number of tasks issued/completed in the simulation
    num_tasks_completed = 0

    # Number of tasks issued/completed that did not contribute to consensus
    num_wasted_tasks = 0

    # Amount of worker-time spent during the simulation
    sim_time = 0


    #### For tests that run multiple simulations ###

    # Total number of tasks issued/completed in each simulation
    num_tasks_completed_arr = []

    # Number of tasks issued/completed that did not contribute to consensus in each simulation
    num_wasted_tasks_arr = []

    # Amount of worker-time spent during each simulation
    sim_time_arr = []

    
    
    #### For real data simulations only ###

    # Number of primary items that are correctly evaluated
    num_item_correct_eval = 0

    #
    sim_accuracy_arr = []
    


    ### settings ###



    #### FUNCTIONS ####

    ## Loading Data
        ### real data ###
        ### synthetic data ###


    ## ground truth determination ##
    # way to compare results from simulation with ground truth


    ## give task real and give task synthetic 
        """ creates a task based on the current state of the simmulation of one of the possible task model types"""


    ## reset database for multiple runs ##
    ## reset completely ##


    ## optimal for comparison that runs all the true influential restaurants before the false ones ## <<< only useful in real data simulations
    ## run simulation ##



    ## represent simulation results ##