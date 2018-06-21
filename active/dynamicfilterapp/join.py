import datetime as DT
from math import *
from random import *
import numpy

class Join:
    """A join class for each instance of a join that occurs (perhaps across many predicates) """

    #-----------------------######
    ## CONSTRUCTOR           #####
    #-----------------------######

    def __init__(self, in_list, in_list2 = None):

        ## INPUTS #-----------------------################

        self.list1 = in_list

        if in_list2 == None:
            self.list2 = []
        else:
            self.list2 = in_list2

        ## Settings #-----------------------###############

        self.JOIN_SELECTIVITY = 0.1

            ## PJFjoin in particular
        self.PJF_SELECTIVITY = 0.3
        self.PAIRWISE_TIME_PER_TASK = 40.0 # TODO: RENAME
        self.TIME_TO_EVAL_PJF = 100.0

            ## PWJoin in particular
        self.BASE_FIND_MATCHES = 60.0     #Basic requirement to find some matches
        self.FIND_SINGLE_MATCH_TIME = 7.0 #cost per match found
        self.AVG_MATCHES = 10.0 #average matches per item
        self.STDDEV_MATCHES = 2.0 #standard deviation of matches

            ## small predicate in particular
        self.SMALL_P_SELECTIVITY = 0.5
        self.TIME_TO_EVAL_SMALL_P = 30.0

            ## Other private variables used for simulations
        self.private_list2 = [ "Red", "Blue", "Green", "Yellow", "Orange", "Purple", "Mauve", "Peridot", "Periwinkle", "Gold", "Gray", "Burgundy", "Silver", "Taupe", "Brown", "Ochre", "Jasper", "Lavender", "Violet", "Pink", "Magenta" ] 


        ## Estimates #-----------------------##############

        self.PJF_selectivity_est = 0.5
        self.join_selectivity_est = 0.5
        self.PJF_cost_est = 0.0
        self.join_cost_est = 0.0
        self.PW_cost_est_1 = [] # TODO: make sure that this is a list everywhere that it is used # TODO: rethink name
        self.PW_cost_est_2 = []
        self.small_p_cost_est = 0.0
        self.small_p_selectivity_est = 0.0
        self.num_matches_per_item_1 = []
        self.num_matches_per_item_2 = []

            ## Enumeration estimator variables
        self.f_dictionary = { }
        self.total_sample_size = 0

        ## Results #-----------------------################

        self.results_from_pjf_join = []
        self.results_from_all_join = [] # TODO: why did we want these seperate again?
        self.evaluated_with_PJF = { }
        self.evaluated_with_smallP = [] # all things that evaluated to True
        self.failed_by_smallP = [] # all things that evaluated to False
        self.processed_by_PJF = 0
        self.processed_by_smallP = 0
        self.processed_by_join = 0

        ## Other Variables #-----------------------########

        self.has_2nd_list = False
        self.total_num_ips_processed = 0
        self.enumerator_est = False # TODO: read more about this and use in our code
        self.THRESHOLD = 0.1

        ## TOGGLES #-----------------------################
        self.DEBUG = True

    # TODO: 

    #-----------------------#
    ## PJF Join         #####
    #-----------------------# 

    def prejoin_filter(self, item):
        timer_val = 0
        if(not item in self.evaluated_with_PJF):
            # save results of PJF to avoid repeated work
            self.evaluated_with_PJF[item],PJF_cost = self.evaluate(PJF,item)
            self.processed_by_PJF += 1 # TODO: check that these are correct for what we are trying to record
            # if the item evaluated True for the PFJ then adjust selectivity
            self.PJF_selectivity_est = (self.PJF_selectivity_est*(self.processed_by_PJF-1)+self.evaluated_with_PJF[i])/self.processed_by_PJF
            # adjust our cost estimates for evaluating PJF
            self.PJF_cost_est = (self.PJF_cost_est*(len(self.evaluated_with_PJF)-1)+PJF_cost)/self.processed_by_PJF
            timer_val += self.TIME_TO_EVAL_PJF
            self.full_timer += self.TIME_TO_EVAL_PJF

        if self.DEBUG:
            print "************** PJF CHECKING ITEM ****************"
        return evaluated_with_PJF[item], timer_val

    def join_items(self, i, j):
        timer_val = 0
        if (i,j) in self.results_from_all_join:
            return True, 0
        if(self.evaluated_with_PJF[i] and self.evaluated_with_PJF[j]):
            # Generate task of current pair
            # Choose whether to add to results_from_pjf_join
            timer_val += self.PAIRWISE_TIME_PER_TASK
            self.full_timer += self.PAIRWISE_TIME_PER_TASK
            ### If it is accepted in join process
            if(random() < self.JOIN_SELECTIVITY):
                self.join_selectivity_est = (self.join_selectivity_est*self.processed_by_join+1)/(self.processed_by_join+1)
                self.processed_by_join += 1
                self.total_num_ips_processed += 1 # TODO: this is messed up by concurrency
                # Adjust join cost estimates
                self.join_cost_est = (self.join_cost_est*len(self.results_from_pjf_join)+self.PAIRWISE_TIME_PER_TASK)/(len(self.results_from_pjf_join)+1)
                
                #### DEBUGGING ####
                if self.DEBUG:
                    print "ACCEPTED BY JOIN----------"
                    print "TIMER VALUE: " + str(timer_val)
                    print "PJF selectivity estimate: " + str(self.PJF_selectivity_est)
                    print "PJF cost estimate: " + str(self.PJF_cost_est)
                    print "Join selectivity estimate: " + str(self.join_selectivity_est)
                    print "Join cost estimate: " + str(self.join_cost_est)
                    print "--------------------------"
                
                return True, timer_val
        ### If it is not accepted in join process
        self.join_selectivity_est = (self.join_selectivity_est*self.processed_by_join)/(self.processed_by_join+1)
        self.join_cost_est = (self.join_cost_est*len(self.results_from_pjf_join)+self.PAIRWISE_TIME_PER_TASK)/(len(self.results_from_pjf_join)+1)
        
        #### DEBUGGING ####
        if self.DEBUG:
            print "MATCHED BUT REJECTED BY JOIN------------"
            print "TIMER VALUE: " + str(timer_val)
            print "PJF selectivity estimate: " + str(self.PJF_selectivity_est)
            print "PJF cost estimate: " + str(self.PJF_cost_est)
            print "Join selectivity estimate: " + str(self.join_selectivity_est)
            print "Join cost estimate: " + str(self.join_cost_est)
            print "----------------------------------------"

        return False, timer_val
            

    def PJF_join(self, i, j):
        """ Assuming that we have two items of a join tuple that need to be evaluated, 
        this function mimicks human join with predetermined costs and selectivity specified.
        This retruns information about selectivity and cost."""

        if (i,j) in self.results_from_all_join:
            return true
        #TODO: fix PJF join to not repeat work (with other concurrent tasks)

        #### INITIALIZE VARIABLES TO USE ####
        cost_of_PJF, PJF = self.generate_PJF() # TODO: what are we going to do with the cost_of_PJF? Move somewhere else?

        #### CONTROL GROUP: COMPLETELY USING PJF THEN PW JOIN ####
        timer_val = 0
        if(not i in self.evaluated_with_PJF):
            # save results of PJF to avoid repeated work
            self.evaluated_with_PJF[i],PJF_cost = self.evaluate(PJF,i)
            self.processed_by_PJF += 1 # TODO: check that these are correct for what we are trying to record
            # if the item evaluated True for the PFJ then adjust selectivity
            self.PJF_selectivity_est = (self.PJF_selectivity_est*(self.processed_by_PJF-1)+self.evaluated_with_PJF[i])/self.processed_by_PJF
            # adjust our cost estimates for evaluating PJF
            self.PJF_cost_est = (self.PJF_cost_est*(len(self.evaluated_with_PJF)-1)+PJF_cost)/self.processed_by_PJF
            timer_val += self.TIME_TO_EVAL_PJF
            self.full_timer += self.TIME_TO_EVAL_PJF

            if self.DEBUG:
                print "************** PJF: CHECKING FIRST ITEM ****************"

        if (not j in self.evaluated_with_PJF):
            # save results of PJF to avoid repeated work
            self.evaluated_with_PJF[j],PJF_cost = self.evaluate(PJF,j)
            self.processed_by_PJF += 1 # TODO: check that these are correct for what we are trying to record
            # if the item evaluated True for the PFJ then adjust selectivity
            self.PJF_selectivity_est = (self.PJF_selectivity_est*(self.processed_by_PJF-1)+self.evaluated_with_PJF[j])/self.processed_by_PJF
            # adjust our cost estimates for evaluating PJF
            self.PJF_cost_est = (self.PJF_cost_est*(len(self.evaluated_with_PJF)-1)+PJF_cost)/self.processed_by_PJF
            timer_val += self.TIME_TO_EVAL_PJF
            self.full_timer += self.TIME_TO_EVAL_PJF

            if self.DEBUG:
                print "************* PJF: CHECKING SECOND ITEM **************"

        if(self.evaluated_with_PJF[i] and self.evaluated_with_PJF[j]):
            # Generate task of current pair
            # Choose whether to add to results_from_pjf_join
            timer_val += self.PAIRWISE_TIME_PER_TASK
            self.full_timer += self.PAIRWISE_TIME_PER_TASK
            ### If it is accepted in join process
            if(random() < self.JOIN_SELECTIVITY):
                self.join_selectivity_est = (self.join_selectivity_est*self.processed_by_join+1)/(self.processed_by_join+1)
                self.processed_by_join += 1
                self.total_num_ips_processed += 1 # TODO: this is messed up by concurrency
                # Adjust join cost estimates
                self.join_cost_est = (self.join_cost_est*len(self.results_from_pjf_join)+self.PAIRWISE_TIME_PER_TASK)/(len(self.results_from_pjf_join)+1)
                
                 #### DEBUGGING ####
                if self.DEBUG:
                    print "ACCEPTED BY JOIN----------"
                    print "TIMER VALUE: " + str(timer_val)
                    print "PJF selectivity estimate: " + str(self.PJF_selectivity_est)
                    print "PJF cost estimate: " + str(self.PJF_cost_est)
                    print "Join selectivity estimate: " + str(self.join_selectivity_est)
                    print "Join cost estimate: " + str(self.join_cost_est)
                    print "--------------------------"
                
                return True
            ### If it is not accepted in join process
            self.join_selectivity_est = (self.join_selectivity_est*self.processed_by_join)/(self.processed_by_join+1)
            self.join_cost_est = (self.join_cost_est*len(self.results_from_pjf_join)+self.PAIRWISE_TIME_PER_TASK)/(len(self.results_from_pjf_join)+1)
            
            #### DEBUGGING ####
            if self.DEBUG:
                print "MATCHED BUT REJECTED BY JOIN------------"
                print "TIMER VALUE: " + str(timer_val)
                print "PJF selectivity estimate: " + str(self.PJF_selectivity_est)
                print "PJF cost estimate: " + str(self.PJF_cost_est)
                print "Join selectivity estimate: " + str(self.join_selectivity_est)
                print "Join cost estimate: " + str(self.join_cost_est)
                print "----------------------------------------"

            return False
        return False

    #-----------------------#
    ## PJF Join Helpers #####
    #-----------------------#
    def generate_PJF(self):
        """ Generates the PJF, returns the cost of finding the PJF and selectivity fo the PJF"""
        return (15,self.PJF_SELECTIVITY)

    def evaluate(self, prejoin, item):
        """ Evaluates the PJF and returns whether it evaluate to true and how long it took to evluate it"""
        return random()<sqrt(self.PJF_SELECTIVITY),self.TIME_TO_EVAL_PJF

    #-----------------------#
    ## PW Join          #####
    #-----------------------#

    def PW_join(self, i, itemlist):
        '''Creates a join by taking one item at a time and finding matches
        with input from the crowd '''
        
        if i in self.failed_by_smallP:
            raise Exception("Improper removal/addition of " + str(i) + " occurred")
        #Metadata/debug information
        avg_cost = 0
        num_items = 0

        timer_val = 0
        #Get results of that task
        if itemlist == self.list1:
            matches, timer_val = self.get_matches(i, timer_val)
        else:
            matches, timer_val = self.get_matches_l2(i, timer_val)
        timer_val += self.BASE_FIND_MATCHES
        self.full_timer += self.BASE_FIND_MATCHES
        #recalculate average cost
        
        if itemlist == self.list1:
            self.PW_cost_est_1 += [timer_val]
            self.num_matches_per_item_1 += [len(matches)]
        else:
            self.PW_cost_est_2 += [timer_val]
            self.num_matches_per_item_2 += [len(matches)]
        #remove processed item from itemlist

        if itemlist == self.list1 and i in itemlist:
            self.list1.remove(i)
        elif i in itemlist:
            self.list2.remove(i)
            self.evaluated_with_smallP.remove(i)
        if self.DEBUG:
            print "RAN PAIRWISE JOIN ----------"
            print "PW AVERAGE COST FOR L1: " + str(numpy.mean(self.PW_cost_est_1))
            print "PW TOTAL COST FOR L1: " + str(numpy.sum(self.PW_cost_est_1))
            print "PW AVERAGE COST FOR L2: " + str(numpy.mean(self.PW_cost_est_2))
            print "PW TOTAL COST FOR L2: " + str(numpy.sum(self.PW_cost_est_2))
            print "----------------------------"
        # we want to add the new items to list2 and keep track of the sample size
        if itemlist == self.list1:
            if not self.has_2nd_list:
                for match in matches:
                    # add to list 2
                    if match[1] not in self.list2 and match[1] not in self.failed_by_smallP:
                        self.list2 += [match[1]]
                    # add to f_dictionary
                    if not any(self.f_dictionary):
                        self.f_dictionary[1] = [match[1]]
                    else:
                        been_added = False
                        entry = 1 # known first key
                        # try to add it to the dictionary
                        while not been_added:
                            if match[1] in self.f_dictionary[entry]:
                                self.f_dictionary[entry].remove(match[1])
                                if entry+1 in self.f_dictionary:
                                    self.f_dictionary[entry+1] += [match[1]]
                                    been_added = True
                                else:
                                    self.f_dictionary[entry+1] = [match[1]]
                                    been_added = True
                            entry += 1
                            if not entry in self.f_dictionary:
                                break
                        if not been_added:
                            self.f_dictionary[1] += [match[1]]
                
            self.total_sample_size += len(matches)
            self.total_num_ips_processed += len(matches)
        # get_matches() returns (list2, list1) if itemlist is list2, so reverse them. 
        else:
            for i in range(len(matches)):
                matches[i] = (matches[i][1],matches[i][0])
            self.total_num_ips_processed += len(matches)
        return matches

    #-----------------------#
    ## PW Join Helpers  #####
    #-----------------------#

    def get_matches(self, item, timer):
        '''gets matches for an item, eventually from the crowd, currently random'''
        #assumes a normal distribution
        num_matches = int(round(numpy.random.normal(self.AVG_MATCHES, self.STDDEV_MATCHES, None)))
        matches = []
        if num_matches < len(self.private_list2):
            sample = numpy.random.choice(self.private_list2, num_matches, False)
        else:
            sample = self.list2
        
        #add num_matches pairs
        for i in range(len(sample)):
            item2 = sample[i]
            matches.append((item, item2))
            timer += self.FIND_SINGLE_MATCH_TIME
            self.full_timer += self.FIND_SINGLE_MATCH_TIME
        if self.DEBUG:
            print "MATCHES ---------------"
            print "Number of matches: " + str(num_matches)
            print "Time taken to find matches: " + str(timer)
            print "-----------------------"
        return matches, timer

    #gets matches for an item in list2
    def get_matches_l2(self, item, timer):
        '''gets matches for an item, eventually from the crowd, currently random'''
        #assumes a normal distribution
        num_matches = int(round(numpy.random.normal(self.AVG_MATCHES * (len(self.list1)/len(self.private_list2)), self.STDDEV_MATCHES * (len(self.list1)/len(self.private_list2)), None)))
        matches = []
        if num_matches < len(self.list1):
            sample = numpy.random.choice(self.list1, num_matches, False)
        else:
            sample = self.list1
        
        #add num_matches pairs
        for i in range(len(sample)):
            item2 = sample[i]
            matches.append((item, item2))
            timer += self.FIND_SINGLE_MATCH_TIME
            self.full_timer += self.FIND_SINGLE_MATCH_TIME
        if self.DEBUG:
            print "MATCHES ---------------"
            print "Number of matches: " + str(num_matches)
            print "Time taken to find matches: " + str(timer)
            print "-----------------------"
        return matches, timer

    #-----------------------#
    ## Main Join        #####
    #-----------------------#

    def main_join(self, predicate, item):
        """ This is the main join function. It calls PW_join(), PJF_join(), and small_pred(). Uses 
        cost estimates to determine which function to call item by item."""

        #if we have already finished the join, return results and drop lists, refusing to continue
        if not self.list1 or self.has_2nd_list and not self.list2:
            print "All matches made"
            self.list1 = []
            self.list2 = []
            return [], self.results_from_all_join

        #captures times for each task in this run of main_join
        taskList = []

        buffer = len(self.results_from_all_join) <= 0.15*len(self.list1)*len(self.list2)
        buf1 = len(self.results_from_all_join) < .1*len(self.list1)
        print "BUF1 = " + str(buf1)
        #reconsider these a bit 

        # PW join on list1, no list2 yet
        if not self.has_2nd_list:
            
            matches = self.PW_join(item, self.list1)
            if self.full_timer != 0:
                taskList += [self.full_timer]
            self.full_timer = 0.0
            for match in matches:
                if self.small_pred(match[1]):
                    if self.full_timer != 0:
                        taskList += [self.full_timer]
                    self.full_timer = 0.0
                    self.results_from_all_join.append(match)
                else:
                    if self.full_timer != 0:
                        taskList += [self.full_timer]
                    self.full_timer = 0.0
            if not buf1 and self.chao_estimator():
                if self.DEBUG:
                    print "ESTIMATOR HIT------------"
                    print "Size of list 1: " + str(len(self.list1))
                    print "Size of list 2: " + str(len(self.list2))
                    print "failed by small predicate: "
                    print str(len(self.failed_by_smallP))
                    print "-------------------------"

                self.has_2nd_list = True
        else:
            cost = self.find_costs()
            if buffer: # if still in buffer region TODO: think more about this metric
                if random() < 0.5: # 50% chance of going to 1 or 2
                    for i in self.list2:
                        if cost[0] < cost[1]: # Choose the fastest between 1 amd 2
                            if self.DEBUG:
                                    print "************** BUFFER DOWN PATH 1 ****************"
                            if self.small_pred(i):
                                if self.full_timer != 0:
                                    taskList += [self.full_timer]
                                self.full_timer = 0.0
                                if self.PJF_join(i, item):
                                    if self.full_timer != 0:
                                        taskList += [self.full_timer]
                                    self.full_timer = 0.0
                                    self.results_from_pjf_join.append([item, i])
                                    self.results_from_all_join.append([item, i])
                                else:
                                    if self.full_timer != 0:
                                        taskList += [self.full_timer]
                                    self.full_timer = 0.0
                            else:
                                if self.full_timer != 0:
                                    taskList += [self.full_timer]
                                self.full_timer = 0.0
                        else:
                            if self.DEBUG:
                                    print "************** BUFFER DOWN PATH 2 ****************"
                            if self.PJF_join(i, item):
                                if self.full_timer != 0:
                                    taskList += [self.full_timer]
                                self.full_timer = 0.0
                                if self.small_pred(i):
                                    if self.full_timer != 0:
                                        taskList += [self.full_timer]
                                    self.full_timer = 0.0
                                    self.results_from_pjf_join.append([item, i])
                                    self.results_from_all_join.append([item, i])
                                else:
                                    if self.full_timer != 0:
                                        taskList += [self.full_timer]
                                    self.full_timer = 0.0
                            else:
                                if self.full_timer != 0:
                                    taskList += [self.full_timer]
                                self.full_timer = 0.0
                        #we assume (and feel justified doing so) no repeats in primary list
                    print item
                    print self.list1
                    self.list1.remove(item)
                else: # 50% chance of going to 3 or 4 or 5
                    if cost[2]<cost[3]:
                        i = self.list2[0]
                        if cost[2] < cost[4]:
                            if self.DEBUG:
                                print "************** BUFFER DOWN PATH 3 ****************"
                            matches = self.PW_join(i, self.list2) # assuming self.list2 is not empty
                            if self.full_timer != 0:
                                taskList += [self.full_timer]
                            self.full_timer = 0.0
                            if self.small_pred(i):
                                if self.full_timer != 0:
                                    taskList += [self.full_timer]
                                self.full_timer = 0.0
                                self.results_from_all_join+=(matches)
                            else:
                                if self.full_timer != 0:
                                    taskList += [self.full_timer]
                                self.full_timer = 0.0
                        else:
                            if self.DEBUG:
                                    print "************** BUFFER DOWN PATH 5 ****************"
                                    print "length of list 2: "
                                    print len(self.list2)
                            if self.small_pred(i):
                                if self.full_timer != 0:
                                    taskList += [self.full_timer]
                                self.full_timer = 0.0
                                matches = self.PW_join(i, self.list2)
                                if self.full_timer != 0:
                                    taskList += [self.full_timer]
                                self.full_timer = 0.0
                                self.results_from_all_join+= matches
                            else:
                                if self.full_timer != 0:
                                    taskList += [self.full_timer]
                                self.full_timer = 0.0
                    elif cost[3]<cost[4]:
                        if self.DEBUG:
                            print "************** BUFFER DOWN PATH 4 ****************"
                        matches = self.PW_join(item, self.list1)
                        if self.full_timer != 0:
                            taskList += [self.full_timer]
                        self.full_timer = 0.0
                        for i in matches:
                            if self.small_pred(i[1]):
                                if self.full_timer != 0:
                                    taskList += [self.full_timer]
                                self.full_timer = 0.0
                                self.results_from_all_join.append(i)
                            else:
                                if self.full_timer != 0:
                                    taskList += [self.full_timer]
                                self.full_timer = 0.0
                    else:
                        if self.DEBUG:
                            print "************** BUFFER DOWN PATH 5 ****************"
                        i = self.list2[0]
                        if self.small_pred(i):
                            if self.full_timer != 0:
                                taskList += [self.full_timer]
                            self.full_timer = 0.0
                            matches = self.PW_join(i, self.list2)
                            if self.full_timer != 0:
                                taskList += [self.full_timer]
                            self.full_timer = 0.0
                            self.results_from_all_join+= matches
                        else:
                            if self.full_timer != 0:
                                taskList += [self.full_timer]
                            self.full_timer = 0.0
            else: #having escaped the buffer zone
                minimum = min(cost)
                if(cost[0] == minimum):
                    for i in self.list2:
                        if self.DEBUG:
                            print "************** GOING DOWN PATH 1 ****************"
                        if self.small_pred(i):
                            if self.full_timer != 0:
                                taskList += [self.full_timer]
                            self.full_timer = 0.0
                            if self.PJF_join(i, item):
                                if self.full_timer != 0:
                                    taskList += [self.full_timer]
                                self.full_timer = 0.0
                                self.results_from_pjf_join.append([item, i])
                                self.results_from_all_join.append([item, i])
                            else:
                                if self.full_timer != 0:
                                    taskList += [self.full_timer]
                                self.full_timer = 0.0
                        else:
                            if self.full_timer != 0:
                                taskList += [self.full_timer]
                            self.full_timer = 0.0
                    self.list1.remove(item)
                elif(cost[1] == minimum):
                    for i in self.list2:
                        if self.DEBUG:
                            print "************** GOING DOWN PATH 2 ****************"
                        if self.PJF_join(i, item):
                            if self.full_timer != 0:
                                taskList += [self.full_timer]
                            self.full_timer = 0.0
                            if self.small_pred(i):
                                if self.full_timer != 0:
                                    taskList += [self.full_timer]
                                self.full_timer = 0.0
                                self.results_from_pjf_join.append([item, i])
                                self.results_from_all_join.append([item, i])
                            else:
                                if self.full_timer != 0:
                                    taskList += [self.full_timer]
                                self.full_timer = 0.0
                        else:
                            if self.full_timer != 0:
                                taskList += [self.full_timer]
                            self.full_timer = 0.0
                    self.list1.remove(item)
                elif(cost[2] == minimum):
                    if self.DEBUG:
                        print "************** GOING DOWN PATH 3 ****************"
                    i = self.list2[0]
                    matches = self.PW_join(i, self.list2) # assuming self.list2 is not empty
                    if self.full_timer != 0:
                        taskList += [self.full_timer]
                    self.full_timer = 0.0
                    if self.small_pred(i):
                        if self.full_timer != 0:
                            taskList += [self.full_timer]
                        self.full_timer = 0.0
                        self.results_from_all_join+= matches
                    else:
                        if self.full_timer != 0:
                            taskList += [self.full_timer]
                        self.full_timer = 0.0
                elif(cost[3] == minimum):
                    if self.DEBUG:
                        print "************** GOING DOWN PATH 4 ****************"
                    matches = self.PW_join(item, self.list1)
                    if self.full_timer != 0:
                        taskList += [self.full_timer]
                    self.full_timer = 0.0
                    for i in matches:
                        if self.small_pred(i[1]):
                            if self.full_timer != 0:
                                taskList += [self.full_timer]
                            self.full_timer = 0.0
                            self.results_from_all_join.append(i)
                        else:
                            if self.full_timer != 0:
                                taskList += [self.full_timer]
                            self.full_timer = 0.0
                else:
                    if self.DEBUG:
                        print "************** GOING DOWN PATH 5 ****************"
                    i = self.list2[0]
                    print i
                    if self.small_pred(i):
                        if self.full_timer != 0:
                            taskList += [self.full_timer]
                        self.full_timer = 0.0
                        matches = self.PW_join(i, self.list2)
                        if self.full_timer != 0:
                            taskList += [self.full_timer]
                        self.full_timer = 0.0
                        self.results_from_all_join+= matches
                    else:
                        if self.full_timer != 0:
                            taskList += [self.full_timer]
                        self.full_timer = 0.0
        return taskList




    #-----------------------#
    ## Main Join Helpers ####
    #-----------------------#

    ## @param self
    # @return list of cost estimates of 5 paths
    # @remarks Finds the cost estimates of the 5 paths available to go down using the instance variables for estimating different task times. 
    #   Path 1 = PJF w/ small predicate applied early. 
    #   Path 2 = PJF w/ small predicate applied later. Path 3 = PW on list 2. Path 4 = PW on list 1. Path 5 = small p then PW on list 2.
    #   Helper for assign_join_tasks()
    def find_costs(self):
        #losp - "likelihood of some pairs" odds of a list2 item matching with at least one item from list1
        losp = 1 - (1 - self.join_selectivity_est)**(len(self.list1))
        # COST 1 CALCULATION - small pred then PJF
        cost_1 = self.small_p_cost_est*(len(self.list2)-len(self.evaluated_with_smallP)) + \
                self.PJF_cost_est*(self.small_p_selectivity_est *len(self.list2)+(len(self.list1))) + \
                self.join_cost_est*len(self.list2)*len(self.list1)*self.small_p_selectivity_est*self.PJF_selectivity_est
        # COST 2 CALCULATION - PJF then small pred
        cost_2 = self.PJF_cost_est*(len(self.list2)+len(self.list1)) + \
                self.join_cost_est*len(self.list2)*len(self.list1)*self.PJF_selectivity_est+ \
                self.small_p_cost_est*losp*len(self.list2)
        # COST 3 CALCULATION - pairwise of second list and then small pred
        match_cost_est, base_cost_est = numpy.polyfit(self.num_matches_per_item_1+self.num_matches_per_item_2, self.PW_cost_est_1+self.PW_cost_est_2,1)
        avg_matches_est_2 = numpy.mean(self.num_matches_per_item_2)
        cost_3 = base_cost_est*len(self.list2) + \
                match_cost_est*avg_matches_est_2*len(self.list2)  + \
                losp*len(self.list2)*self.small_p_cost_est
        # COST 4 CALCULATION - pairwise join on first list and then small pred
        avg_matches_est_1 = numpy.mean(self.num_matches_per_item_1)
        cost_4 = base_cost_est*len(self.list1)+ \
                match_cost_est*avg_matches_est_1*len(self.list1) + \
                self.small_p_cost_est*losp*len(self.list2)
        # COST 5 CALCULATION - small pred then pairwise join on second list
        cost_5 = self.small_p_cost_est*(len(self.list2)-len(self.evaluated_with_smallP))+ \
                self.small_p_selectivity_est*len(self.list2)* (base_cost_est + \
                match_cost_est*avg_matches_est_2)
        
        #### DEBUGGING ####
        if self.DEBUG:
            print "FIND COSTS ESTIMATES -------"
            print "COST 1 = " + str(cost_1)
            print "COST 2 = " + str(cost_2)
            print "COST 3 = " + str(cost_3)
            print "COST 4 = " + str(cost_4)
            print "COST 5 = " + str(cost_5)
            self.find_real_costs()
            print "----------------------------"

        return [cost_1, cost_2, cost_3, cost_4, cost_5]

    ## @param self
    # @return list of real costs of 5 paths
    # @remarks Finds the real costs of the 5 paths available to go down. Path 1 = PJF w/ small predicate applied early. 
    #    Path 2 = PJF w/ small predicate applied later. Path 3 = PW on list 2. Path 4 = PW on list 1. Path 5 = small p then PW on list 2
    def find_real_costs(self):
        real_losp = 1 - (1-self.JOIN_SELECTIVITY)**(len(self.list1))
        # COST 1 CALCULATION - small pred then PJF
        cost_1 = self.TIME_TO_EVAL_SMALL_P*(len(self.list2)-len(self.evaluated_with_smallP)) + \
            self.TIME_TO_EVAL_PJF*(self.SMALL_P_SELECTIVITY *len(self.list2)+(len(self.list1))) + \
            self.PAIRWISE_TIME_PER_TASK*len(self.list2)*len(self.list1)*self.SMALL_P_SELECTIVITY*self.PJF_SELECTIVITY
        # COST 2 CALCULATION - PJF then small pred
        cost_2 = self.TIME_TO_EVAL_PJF*(len(self.list2)+len(self.list1)) + \
            self.PAIRWISE_TIME_PER_TASK*len(self.list2)*len(self.list1)*self.PJF_SELECTIVITY+ \
            self.TIME_TO_EVAL_SMALL_P*real_losp*len(self.list2)
        # COST 3 CALCULATION - pairwise of second list and then small pred
        cost_3 = (self.BASE_FIND_MATCHES+self.AVG_MATCHES * (len(self.list1)/len(self.private_list2))*self.FIND_SINGLE_MATCH_TIME)*len(self.list2) + \
            real_losp*len(self.list2)*self.TIME_TO_EVAL_SMALL_P
        # COST 4 CALCULATION - pairwise join on first list and then small pred
        cost_4 = (self.BASE_FIND_MATCHES+self.AVG_MATCHES*self.FIND_SINGLE_MATCH_TIME)*len(self.list1)+ \
            self.TIME_TO_EVAL_SMALL_P*real_losp*len(self.list2)
        # COST 5 CALCULATION - small pred then pairwise join on second list
        cost_5 = self.TIME_TO_EVAL_SMALL_P*(len(self.list2)-len(self.evaluated_with_smallP))+ self.SMALL_P_SELECTIVITY*len(self.list2)*(self.BASE_FIND_MATCHES+ \
            self.AVG_MATCHES*len(self.list1)/len(self.private_list2)*self.FIND_SINGLE_MATCH_TIME)
        
        #### DEBUGGING ####
        if self.DEBUG:
            print "REAL COST 1 = " + str(cost_1)
            print "REAL COST 2 = " + str(cost_2)
            print "REAL COST 3 = " + str(cost_3)
            print "REAL COST 4 = " + str(cost_4)
            print "REAL COST 5 = " + str(cost_5)
        return [cost_1, cost_2, cost_3, cost_4, cost_5]


    ## @param item: the item to be evaluated
    # @param self
    # @return eval_results : a boolean for whether or not the item passes the small predicate (the predicate that
    #   applies to the secondary item list in a join, remnants of the otherall predicate which was broken up into a join)
    # @return timer_val : this is the amount of time (time units) that it took to evaluate the small predicate
    # @remarks Evaluates the small predicate, adding the results of that into a global dictionary. 
    #   Also adjusts the global estimates for the cost and selectivity of the small predicate.
    def small_pred(self, item):
        #first, check if we've already evaluated this item
        timer_val = 0
        if item in self.evaluated_with_smallP:
            return True, timer_val
        elif item in self.failed_by_smallP:
            return False, timer_val
        #if not, evaluate it with the small predicate
        else:
            # Update the cost
            self.small_p_cost_est = (self.small_p_cost_est*(self.processed_by_smallP)+self.TIME_TO_EVAL_SMALL_P)/(self.processed_by_smallP+1)
            timer_val += self.TIME_TO_EVAL_SMALL_P
            #for preliminary testing, we randomly choose whether or not an item passes
            eval_results = random() < self.SMALL_P_SELECTIVITY
            # Update the selectivity
            self.small_p_selectivity_est = (self.small_p_selectivity_est*(self.processed_by_smallP)+eval_results)/(self.processed_by_smallP+1)
            #increment the number of items 
            self.processed_by_smallP += 1
            #if the item does not pass, we remove it from the list entirely
            if not eval_results:
                self.list2.remove(item)
                self.failed_by_smallP.append(item)
                print item + " eliminated"
            #if the item does pass, we add it to the list of things already evaluated
            else:
                self.evaluated_with_smallP.append(item)
            if self.DEBUG:
                print "SMALL P JUST RUN---------"
                print "small p cost estimate: " + str(self.small_p_cost_est)
                print "small p selectivity: " + str(self.small_p_selectivity_est)
                print "-------------------------"
            return eval_results, timer_val

    ## @param self
    # @return true if the current size of the list is within a certain threshold of the total size of the list (according to the chao estimator)
    #   and false otherwise.
    # @remarks To understand the math computed in this function see: http://www.cs.albany.edu/~jhh/courses/readings/trushkowsky.icde13.enumeration.pdf 
    def chao_estimator(self):
        """ Uses the Chao92 equation to estimate population size during enumeration """
        # prepping variables
        c_hat = 1-float(len(self.f_dictionary[1]))/self.total_sample_size
        sum_fis = 0
        for i in self.f_dictionary:
            sum_fis += i*(i-1)*len(self.f_dictionary[i])
        gamma_2 = max((len(self.list2)/c_hat*sum_fis)/\
                    (self.total_sample_size*(self.total_sample_size-1)) -1, 0)
        # final equation
        N_chao = len(self.list2)/c_hat + self.total_sample_size*(1-c_hat)/(c_hat)*gamma_2
        #if we are comfortably within a small margin of the total set, we call it close enough
        if N_chao > 0 and abs(N_chao - len(self.list2)) < self.THRESHOLD * N_chao:
            return True
        return False

inputL = []
for i in range(3000):
    inputL += [i]

my_j = Join(inputL)
j = 0
while len(my_j.list1) != 0:
    print str(j) + " STARTING MAIN"
    my_j.main_join("predicate :)", my_j.list1[0])
    j+=1
print my_j.find_costs()
