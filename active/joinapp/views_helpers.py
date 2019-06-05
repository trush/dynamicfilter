from models import *





#_____SECOND LIST COMPLETE_____#

## TODO: rewrite this to match functionality of our implementation

## @remarks Called in chao_estimator(). If the difference between the size of list2 and the size of the 
# estimate is less than this fraction of the size of the estimate then chao_estimator() will return True.
self.THRESHOLD = toggles.THRESHOLD

# Enumeration Vars #

## @remarks Used in the enumeration estimate in chao_estimator()
self.total_sample_size = 0
## @remarks Used in the enumeration estimate in chao_estimator()
self.f_dictionary = { }
# both variables updated in PW join in join class
if itemlist == self.list1:
    if not self.has_2nd_list:
        for match in consensus_matches:
            # add to list 2
            if match[1] not in self.list2 and match[1] not in self.failed_by_smallP:
                self.list2 += [match[1]]
                print "we are here adding to list2, which is now" + str(self.list2)
            # add to f_dictionary
            if not any(self.f_dictionary):
                self.f_dictionary[1] = [match[1]] # <------- updated here
            else:
                been_added = False
                entry = 1 # known first key
                # try to add it to the dictionary
                while not been_added:
                    if match[1] in self.f_dictionary[entry]:
                        self.f_dictionary[entry].remove(match[1]) # <------- updated here
                        if entry+1 in self.f_dictionary:
                            self.f_dictionary[entry+1] += [match[1]] # <------ updated here
                            been_added = True
                        else:
                            self.f_dictionary[entry+1] = [match[1]] # <------ updated here
                            been_added = True
                    entry += 1
                    if not entry in self.f_dictionary:
                        break
                if not been_added:
                    self.f_dictionary[1] += [match[1]] # <------
    self.total_sample_size += len(consensus_matches) # <------ updated here

## @param self
# @return true if the current size of the list is within a certain threshold of the total size of the list (according to the chao estimator)
#   and false otherwise.
# @remarks Uses the Chao92 equation to estimate population size during enumeration.
#	To understand the math computed in this function see: http://www.cs.albany.edu/~jhh/courses/readings/trushkowsky.icde13.enumeration.pdf 
def chao_estimator():
    # prepping variables
    if self.total_sample_size <= 0:
        return False
    c_hat = 1-float(len(self.f_dictionary[1]))/self.total_sample_size
    sum_fis = 0
    for i in self.f_dictionary:
        sum_fis += i*(i-1)*len(self.f_dictionary[i])
    gamma_2 = max((len(self.list2)/c_hat*sum_fis)/\ 
                (self.total_sample_size*(self.total_sample_size-1)) -1, 0) # replace len(self.list2) with # of secondary items
    # final equation
    N_chao = len(self.list2)/c_hat + self.total_sample_size*(1-c_hat)/(c_hat)*gamma_2
    #if we are comfortably within a small margin of the total set, we call it close enough
    if N_chao > 0 and abs(N_chao - len(self.list2)) < self.THRESHOLD * N_chao:
        return True
    return False





#_____GIVE TASKS_____#

## Function that gives tasks to workers
# @param workerID The ID for the worker that is being assigned a task

# giving a task

# for joinable filters
# task:
# iterate thru the list of primary items
# ask for an answer y/n

# for itemwise join
# task:
# iterate thru list of primary items until second list is complete

# if second list is complete
# then make pairs of primary and secondary list items
# task:
# iterate thru list of secondary items for secondary predicate

# if consensus on secondary predicate for all secondary items
# secondary items that pass which have highest # of num_prim_items chosen first
# task:
# go thru each primary item w/ relation to that secondary item 
# mark true if secondary predicate true
# delete relation if secondary predicate false

# for prejoin filters
# task:
# iterate thru list of primary items
# ask for prejoin filter

# task:
# 1st task from IW join

# if primary list done
# task:
# iterate thru list of secondary items
# ask for prejoin filter

# if both are completed
# 2nd and 3rd tasks from IW join





#_____FIND CONSENSUS_____#

