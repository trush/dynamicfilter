import datetime as DT
from math import *
from random import *
import numpy

class Join:
    """A join class for each instance of a join that occurs (perhaps across many predicates) """

    ##############################
    ## CONSTRUCTOR           #####
    ##############################

    def __init__(self, in_list, in_list2 = None):

        ## INPUTS ########################################

        self.list1 = in_list

        if in_list2 == None:
            self.list2 = []
        else:
            self.list2 = in_list2

        ## Settings #######################################

        self.JOIN_SELECTIVITY = 0.1
        self.TIME_TO_GENERATE_TASK = 10.0

            ## PJFjoin in particular
        self.PJF_SELECTIVITY = 0.3
        self.PAIRWISE_TIME_PER_TASK = 40.0 # TODO: RENAME
        self.TIME_TO_EVAL_PJF = 100.0

            ## PWJoin in particular
        self.BASE_FIND_MATCHES = 60.0     #Basic requirement to find some matches
        self.FIND_SINGLE_MATCH_TIME = 5.0 #cost per match found
        self.AVG_MATCHES = 2.0 #average matches per item
        self.STDDEV_MATCHES = .5 #standard deviation of matches

            ## small predicate in particular
        self.SMALL_P_SELECTIVITY = 0.5
        self.TIME_TO_EVAL_SMALL_P = 30.0


        ## Estimates ######################################

        self.PJF_selectivity_est = 0.5
        self.join_selectivity_est = 0.5
        self.PJF_cost_est = 0.0
        self.join_cost_est = 0.0
        self.PW_cost_est = 0.0
        self.small_p_cost_est = 0.0
        self.small_p_selectivity_est = 0.0

        ## Results ########################################

        self.results_from_pjf_join = []
        self.results_from_pw_join = [] # TODO: why did we want these seperate again?
        self.evaluated_with_PJF = { }
        self.evaluated_with_smallP = [] # all things that evaluated to True
        self.failed_by_smallP = [] # all things that evaluated to False
        self.processed_by_pw = 0
        self.processed_by_PJF = 0
        self.processed_by_smallP = 0

        ## Other Variables ################################

        self.has_2nd_list = False
        self.total_num_ips_processed = 0
        self.enumerator_est = False # TODO: read more about this and use in our code

        ## TOGGLES ########################################
        self.DEBUG = True

    # TODO: 

    #########################
    ## PJF Join         #####
    ######################### 

    def PJF_join(self, i, j):
        """ Assuming that we have two items of a join tuple that need to be evaluated, 
        this function mimicks human join with predetermined costs and selectivity specified.
        This retruns information about selectivity and cost."""

        #### INITIALIZE VARIABLES TO USE ####
        cost_of_PJF, PJF = generate_PJF() # TODO: what are we going to do with the cost_of_PJF? Move somewhere else?

        #### CONTROL GROUP: COMPLETELY USING PJF THEN PW JOIN ####
        timer_val = 0
        if(not i in self.evaluated_with_PJF):
            # save results of PJF to avoid repeated work
            self.evaluated_with_PJF[i],PJF_cost = evaluate(PJF,i)
            self.processed_by_PJF += 1 # TODO: check that these are correct for what we are trying to record
            # if the item evaluated True for the PFJ then adjust selectivity
            self.PJF_selectivity_est = (self.PJF_selectivity_est*(self.processed_by_PJF-1)+self.evaluated_with_PJF[i])/self.processed_by_PJF
            # adjust our cost estimates for evaluating PJF
            self.PJF_cost_est = (self.PJF_cost_est*len(self.evaluated_with_PJF-1)+PJF_cost)/self.processed_by_PJF
            timer_val += self.TIME_TO_EVAL_PJF

        if (not j in self.evaluated_with_PJF):
            # save results of PJF to avoid repeated work
            self.evaluated_with_PJF[j],PJF_cost = evaluate(PJF,j)
            self.processed_by_PJF += 1 # TODO: check that these are correct for what we are trying to record
            # if the item evaluated True for the PFJ then adjust selectivity
            self.PJF_selectivity_est = (self.PJF_selectivity_est*(self.processed_by_PJF-1)+self.evaluated_with_PJF[j])/self.processed_by_PJF
            # adjust our cost estimates for evaluating PJF
            self.PJF_cost_est = (self.PJF_cost_est*len(self.evaluated_with_PJF-1)+PJF_cost)/self.processed_by_PJF
            timer_val += self.TIME_TO_EVAL_PJF

        if(self.evaluated_with_PJF[i] and self.evaluated_with_PJF[j]):
            # Generate task of current pair
            timer_val += self.TIME_TO_GENERATE_TASK
            # Choose whether to add to results_from_join
            timer_val += self.PAIRWISE_TIME_PER_TASK
            # Adjust join cost with these two time costs
            self.join_cost_est = (self.join_cost_est*len(results_from_join)+self.TIME_TO_GENERATE_TASK+self.PAIRWISE_TIME_PER_TASK)/(len(results_from_join)+1)

        #### DEBUGGING ####
        if self.DEBUG:
            print "PJF JOIN -----------------"
            print "TIMER VALUE: " + str(timer_val)
            print "--------------------------"

        if(random() < self.JOIN_SELECTIVITY):
            return True
        return False


    #########################
    ## PJF Join Helpers #####
    #########################
    def generate_PJF(self):
        """ Generates the PJF, returns the cost of finding the PJF and selectivity fo the PJF"""
        return (15,self.PJF_SELECTIVITY)

    def evaluate(self, prejoin, item):
        """ Evaluates the PJF and returns whether it evaluate to true and how long it took to evluate it"""
        return random()<sqrt(self.PJF_SELECTIVITY),self.TIME_TO_EVAL_PJF

    #########################
    ## PW Join          #####
    #########################

    def PW_join(self, i, itemlist):
        '''Creates a join by taking one item at a time and finding matches
        with input from the crowd '''
        
        #Metadata/debug information
        avg_cost = 0
        num_items = 0

        timer_val = 0
        # Generate task with item
        timer_val += self.TIME_TO_GENERATE_TASK
        #Get results of that task
        matches, timer_val = self.get_matches(i, timer_val)
        timer_val += self.BASE_FIND_MATCHES
        #recalculate average cost
        self.PW_cost_est = (self.PW_cost_est*self.processed_by_pw + timer_val)/(self.processed_by_pw+1)
        self.processed_by_pw += 1
        #remove processed item from itemlist
        itemlist.remove(i)
        if self.DEBUG:
            print "RAN PAIRWISE JOIN ----------"
            print "PW AVERAGE COST: " + str(self.PW_cost_est)
            print "PW TOTAL COST: " + str(self.PW_cost_est*self.processed_by_pw)
            print "----------------------------"
        return matches

    #########################
    ## PW Join Helpers  #####
    #########################

    def get_matches(self, item, timer):
        '''gets matches for an item, eventually from the crowd, currently random'''
        #assumes a normal distribution
        num_matches = int(round(numpy.random.normal(self.AVG_MATCHES, self.STDDEV_MATCHES, None)))
        matches = []
        #add num_matches pairs
        for i in range(num_matches):
            matches.append((item, i))
            timer += self.FIND_SINGLE_MATCH_TIME
        if self.DEBUG:
            print "MATCHES ---------------"
            print "Number of matches: " + str(num_matches)
            print "Time taken to find matches: " + str(timer)
            print "-----------------------"
        return matches, timer

    #########################
    ## Main Join        #####
    #########################

    def main_join(self, predicate, item):
        """ This is the main join function. It calls PW_join(), PJF_join(), and small_pred(). Uses 
        cost estimates to determine which function to call item by item."""

        if not self.has_2nd_list:
            matches = PW_join(item, self.list1)
            self.results_from_pw_join.append(matches)
            self.results_from_pjf_join.append(matches)
            if self.enumerator_est:
                if self.DEBUG:
                    print "ESTIMATOR HIT------------"
                    print "Size of list 1: " + str(len(self.list1))
                    print "Size of list 2: " + str(len(self.list2))
                    print "-------------------------"
                self.has_2nd_list = True
        
        else:
            costs = find_costs()
            if self.DEBUG:
                print "COSTS CALCULATED ---------------"
                print "Cost1: " + str(cost_1)
                print "Cost2: " + str(cost_2)
                print "Cost3: " + str(cost_3)
                print "Cost4: " + str(cost_4)
                print "Cost5: " + str(cost_5)
                print "--------------------------------"
            if self.total_num_ips_processed < 0.15*len(self.list1)*len(self.list2): # if still in buffer region TODO: think more about this metric
                if random(0,1) < 0.5: # 50% chance of going to 1 or 2
                    for i in self.list2:
                        if cost[0] < cost[1]: # Choose the fastest between 1 amd 2
                            if small_pred(i):
                                if PJF_join(i, item):
                                    self.results_from_pjf_join.append([item, i])
                        else:
                            if PJF_join(i, item):
                                if small_pred(i):
                                    self.results_from_pjf_join([item, i])
                else: # 50% chance of going to 3 or 4
                    if cost[2]<cost[3]:
                        i = self.list2[0]
                        if cost[2] < cost[4]:
                            matches = PW_join(i, self.list2) # assuming self.list2 is not empty
                            if small_pred(i):
                                self.results_from_pw_join.append(matches)
                                self.results_from_pjf_join.append(matches)
                        else:
                            if small_pred(i):
                                matches = PW_join(i, self.list2)
                                self.results_from_pw_join.append(matches)
                                self.results_from_pjf_join.append(matches)
                    elif cost[3]<cost[4]:
                        matches = PW_join(item, self.list1)
                        for i in matches:
                            if small_pred(i[1]):
                                self.results_from_pw_join.append(i)
                                self.results_from_pjf_join.append(i)
                    else:
                        i = self.list2[0]
                        if small_pred(i):
                            matches = PW_join(i, self.list2)
                            self.results_from_pw_join.append(matches)
                            self.results_from_pjf_join.append(matches)



    #########################
    ## Main Join Helpers ####
    #########################

    def find_costs(self):
        """ Finds the cost of the quickest path and returns the path number associated with that 
        path. Path 1 = PJF w/ small predicate applied early. Path 2 = PJF w/ small predicate
        applied later. Path 3 = PW on list 2. Path 4 = PW on list 1."""
        # COST 1 CALCULATION - equation explained in written work TODO: explain eq
        cost_1 = self.small_p_cost_est*len(self.list2) + \
                self.PJF_cost_est*(self.small_p_selectivity_est *(len(self.list2)-len(self.evaluated_with_smallP))+(len(self.list1))) + \
                self.join_cost_est*len(self.list2)*len(self.list1)*self.small_p_selectivity_est*self.PJF_selectivity_est
        # COST 2 CALCULATION - equation explained in written work TODO: explain eq
        cost_2 = self.PJF_cost_est*(len(self.list2)+len(self.list1)) + \
                self.join_cost_est*len(self.list2)*len(self.list1)*self.PJF_selectivity_est+ \
                self.small_p_cost_est*self.join_selectivity_est*len(self.list1)*len(self.list2)
        # COST 3 CALCULATION - equation explained in written work TODO: explain eq
        cost_3 = self.PW_cost_est*len(self.list2) + \
                self.join_selectivity_est*len(self.list1)*len(self.list2)*self.small_p_cost_est
        # COST 4 CALCULATION - equation explained in written work TODO: explain eq
        cost_4 = self.PW_cost_est*len(self.list1)+ \
                self.small_p_cost_est*self.join_selectivity_est*len(self.list1)*len(self.list2)
        # COST 5 CALCULATION - equation explained in written work TODO: explain eq
        cost_5 = self.small_p_cost_est*len(self.list2)+self.small_p_selectivity_est*len(self.list2)*self.PW_cost_est

        #### DEBUGGING ####
        if self.DEBUG:
            print "FIND COSTS -----------------"
            print "COST 1 = " + str(cost_1)
            print "COST 2 = " + str(cost_2)
            print "COST 3 = " + str(cost_3)
            print "COST 4 = " + str(cost_4)
            print "COST 5 = " + str(cost_5)
            print "----------------------------"

        return [cost_1, cost_2, cost_3, cost_4, cost_5]


    ###param item: the item to be evaluated
    ##return val whether the item evaluates to true, the cost of this run of small_pred
    def small_pred(self, item):
        """ Evaluates the small predicate, adding the results of that into a global dictionary. 
        Also adjusts the global estimates for the cost and selectivity of the small predicate."""
        #first, check if we've already evaluated this item as true
        if item in self.evaluated_with_smallP:
            return True
        elif item in self.failed_by_smallP:
            return False
        #if not, evaluate it with the small predicate
        else:
            #increment the number of items 
            self.processed_by_smallP += 1
            # Update the cost
            self.small_p_cost_est = (self.small_p_cost_est*(self.processed_by_smallP-1)+self.TIME_TO_EVAL_SMALL_P)/self.processed_by_smallP
            #for preliminary testing, we randomly choose whether or not an item passes
            eval_results = random() < self.SMALL_P_SELECTIVITY
            # Update the selectivity
            self.small_p_selectivity_est = (self.small_p_selectivity_est*(self.processed_by_smallP-1)+eval_results)/self.processed_by_smallP
            #if the item does not pass, we remove it from the list entirely
            if not eval_results:
                self.failed_by_smallP.append(item)
                self.list2.remove(item)
            #if the item does pass, we add it to the list of things already evaluated
            else:
                self.evaluated_with_smallP.append(item)
            if self.DEBUG:
                print "SMALL P JUST RUN---------"
                print "small p cost estimate: " + str(self.small_p_cost_est)
                print "small p selectivity: " + str(self.small_p_selectivity_est)
                print "-------------------------"
            return eval_results

my_j = Join([1,2,3],[0,1,2,3,4])
print my_j.PW_join(1, my_j.list1)
print my_j.PW_join(2, my_j.list1)
print my_j.PW_join(3, my_j.list1)
print my_j.find_costs()