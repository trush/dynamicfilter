
#Relevant Toggles:
"""
__________ General __________
# of primary items
# of secondary items


__________ Item-wise ___________



"""

#___________ Load Synthetic Data ___________#

def syn_load_lists():
    """
    Load/create instances of the primary and secondary lists
    """
    for i in range(toggles.NUM_PRIM_ITEMS){
        Primary_Item.objects.create(item_ID = i, name = "primary item" + str(i))
    }
    for i in range(toggles.NUM_SEC_ITEMS){
        Secondary_Item.objects.create(item_ID = i, name = "secondary item" + str(i))

    }

def syn_load_PS_pairs():
    """
    Load/create instances of primary-secondary pairs
    """
    for primary in Primary_Item.objects.all():
        for secondary in Secondary_Item.objects.all():
            PS_Pair.objects.create(prim_item = primary, sec_item = secondary)



#___________ Initialize Synthetic Data: Give True Answers ___________#

# Need to assign secondary list items to primary list items and choose if they are true/false based on global variables
def syn_assign_true_sec_pred():
    """
    Assign a "ground truth" to whether or not secondary items pass the secondary predicate
    """
    for secondary in Secondary_Item.objects.all():
        secondary.give_true_answer() """ write this function in Secondary_Item model and create true answer attribute """

def syn_assugb_true_PS_pair():
    """
    Assign a "ground truth" to whether or not PS pairs pass the join condition
    """
    for ps_pair in PS_Pair.objects.all():
        ps_pair.give_true_answer() """ write this function in Secondary_Item model and create true answer attribute """


#___________ Give a Worker Answer _____________#
def syn_answer_joinable_filter():
    """
    returns a worker answer to the joinable filter based on global variables
    """
    return None

def syn_answer_join_cond():
    """
    returns a worker answer to the join condition based on global variables
    """
    return None

def syn_answer_sec_pred(item):
    """
    returns a worker answer to the secondary predicate based on global variables
    """
    
    return None

def syn_answer_pjf():
    """
    returns a worker answer to the pre join filter based on global variables
    """
    return None




## Original code:
def syn_answer(chosenIP, switch, numTasks):
	"""
	make up a fake answer based on global variables
	"""

	# SIN tuple is of the form (SIN, amp, period, samplingFrac, trans)
	#TODO: If trans is 0, it starts at the selectvity of the previous timestep

	timeStepInfo = toggles.switch_list[switch]
	#Cost multiplier multiplies work time for tasks, is a basic proxy for difficulty
	cost_multiplier = 1
	if len(timeStepInfo[chosenIP.predicate.pk]) > 2:
		cost_multiplier = timeStepInfo[chosenIP.predicate.pk][2]

	for predNum in toggles.CHOSEN_PREDS:

		pred = Predicate.objects.get(pk=predNum+1)
		predInfo = timeStepInfo[predNum+1]

		if isinstance(predInfo[0], tuple):
			selSinInfo = predInfo[0]
			samplingFrac = selSinInfo[3]
			period = selSinInfo[2]
			if((numTasks % (samplingFrac*period)) == 0):
				pred.setTrueSelectivity(getSinValue(selSinInfo, numTasks))
				print "right after sin call: ", str(pred.trueSelectivity)
		else:
			pred.setTrueSelectivity(predInfo[0])

		if isinstance(predInfo[1], tuple):
			ambSinInfo = predInfo[1]
			samplingFrac = ambSinInfo[3]
			period = ambSinInfo[2]
			if((numTasks % (samplingFrac*period)) == 0):
				pred.setTrueAmbiguity(getSinValue(ambSinInfo, numTasks))
		else:
			pred.setTrueAmbiguity(predInfo[1])

	# if this is the first time we've seen this pair, it needs a true answer
	if ((chosenIP.num_no == 0) and (chosenIP.num_yes == 0)) and not (toggles.EDDY_SYS == 12 or toggles.EDDY_SYS == 13):
		chosenIP.give_true_answer()
		chosenIP.refresh_from_db(fields=["true_answer"])

	# decide if the answer is going to lean towards true or false
	# lean towards true
	if chosenIP.true_answer:
		# decide if the answer is going to be true or false
		value = decision(chosenIP.predicate.trueAmbiguity)
	# lean towards false
	else:
		value = decision(1 - chosenIP.predicate.trueAmbiguity)

	return value, cost_multiplier
