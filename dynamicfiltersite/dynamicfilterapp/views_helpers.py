from models import Task, RestaurantPredicate, Restaurant, PredicateBranch
from scipy.special import btdtr
from random import randint, choice
from math import exp

import csv

# we need at least half of the answers to be True in order for the value of the predicate to be True
# and same for False's
DECISION_THRESHOLD = 0.5

# the uncertainty level determined by the beta distribution function needs to be less than 0.15
# for us to fix the predicate's value
UNCERTAINTY_THRESHOLD = 0.15

ALPHA = 0.9
GAMMA = 0.1

INDEX = 0
MEMORY_THRESHOLD = 0.1

WEIGHT_FACTOR = 2
ADDITIVE_FACTOR = 90
FALSE_THRESHOLD = 0.30

def aggregate_responses(predicate):
    """
    Checks if predicate needs to be answered 0 more times. If uncertainty criteria are met,
    combines worker responses into one value for the predicate. Otherwise, adds five to the 
    appropriate predicateStatus so that more answers will be collected.
    """
    # retrieves the number of yes answers and number of no answers for the 
    # predicate relative to the answers' confidence levels
    yes = Task.objects.filter(restaurantPredicate=predicate, answer = True)
    no = Task.objects.filter(restaurantPredicate=predicate, answer = False)

    # initialize the number of yes's and no's to 0
    totalYes = 0.0
    totalNo = 0.0

    # for all predicates answered yes
    for pred in yes:
        # increase total number of yes by the confidence level indicated
        totalYes += pred.confidenceLevel/100.0
        # increase total number of no by 100 - confidence level indicated
        totalNo += 1 - pred.confidenceLevel/100.0

    # for all predicates answered no
    for pred in no:
        # increase total number of no by 100 - the confidence level 
        # indicated
        totalYes += 1 - pred.confidenceLevel/100.0
        # increase total number of no by confidence level indicated
        totalNo += pred.confidenceLevel/100.0

    # How we compute the uncertaintly level changes depending on whether the answer is True or False
    uncertaintyLevelTrue = btdtr(totalYes+1, totalNo+1, DECISION_THRESHOLD)
    uncertaintyLevelFalse = btdtr(totalNo+1, totalYes+1, DECISION_THRESHOLD)

    # if more yes's than no's
    if totalYes > totalNo and uncertaintyLevelTrue < UNCERTAINTY_THRESHOLD:
        predicate.value = True

    # if more no's than yes's
    elif totalNo > totalYes and uncertaintyLevelFalse < UNCERTAINTY_THRESHOLD:
        predicate.value = False

        # flag for the Restaurant failing a predicate (and thus not passing all the predicates)
        predicateFailed = False

        # iterates through all the fields in this restaurant's model
        for field in predicate.restaurant._meta.fields:
            # verbose_name is the field's name with underscores replaced with spaces
            if field.verbose_name.startswith('predicate') and field.verbose_name.endswith('Status') and getattr(predicate.restaurant, field.verbose_name) == 0:
                predicateFailed = True
                break

        if predicateFailed:
            predicate.restaurant = markFailed(predicate)

    if predicate.value==None:
        # collect five more responses from workers when there are same 
        # number of yes and no
        predicate.restaurant = incrementStatus(predicate.index, predicate.restaurant)
    predicate.restaurant.save()
    predicate.save()

    # printResults()

    return predicate.restaurant

def printResults():
    """
    If there are no more predicates to be evaluated, print the restaurants satisfying all
    predicates to the terminal.
    """
    left = RestaurantPredicate.objects.filter(value=None)

    if len(left)==0:
        print "----------RESULTS-----------"
        print "The following restaurants satisfied all predicates"
        filtered = Restaurant.objects.exclude(hasFailed=True)

        for restaurant in filtered:
            print str(restaurant) + " " + str(restaurant.predicate0Status) + " " + str(restaurant.predicate1Status) + " " + str(restaurant.predicate2Status)
        
        print "----------------------------"

def markFailed(predicate):
    """
    Set all predicate status fields to -1 to indicate that it needs no further evaluation (because
    it has failed a predicate)
    """
    predicate.restaurant.hasFailed = True
    predicate.restaurant.queueIndex = -1

    return predicate.restaurant

def updateCounts(pB, task):
    """
    updates the predicate branch's total and "No!" counts relative to the confidence levels
    """
    if task.answer==True:
        pB.returnedTotal += float(task.confidenceLevel)/100.0
    elif task.answer==False:
        pB.returnedTotal += float(task.confidenceLevel)/100.0
        pB.returnedNo += float(task.confidenceLevel)/100.0
    # print "PB counts updated to: total: " + str(pB.returnedTotal) + " and no: " + str(pB.returnedNo) 
    pB.save()

# def findNumPredicates():
#     # all fields for a restaurant referenced by an incomplete predicate
#     restaurantFields = RestaurantPredicate.objects.all()[0].restaurant._meta.fields

#     # finds number of predicate statuses
#     numOfPredicateStatuses = 0
#     for field in restaurantFields:
#         if field.verbose_name.startswith('predicate') and field.verbose_name.endswith('Status'):
#             numOfPredicateStatuses += 1

#     return numOfPredicateStatuses

def eddy(ID, numOfPredicates):
    """
    Uses a random lottery system to determine which eligible predicate should be
    evaluated next.
    """
    # find all the tasks this worker has completed
    completedTasks = Task.objects.filter(workerID=ID)
    # find all the predicates matching these completed tasks
    completedPredicates = RestaurantPredicate.objects.filter(
        id__in=completedTasks.values('restaurantPredicate_id'))
    
    # excludes all completed predicates from all restaurant predicates to get only incompleted ones
    incompletePredicates1 = RestaurantPredicate.objects.exclude(id__in=completedPredicates)

    incompletePredicates = incompletePredicates1.filter(restaurant__hasFailed=False).filter(value=None)
    # # print "incompletePredicates: "
    # for ip in incompletePredicates:
    #     print ip
    # finds eligible predicate branches
    eligiblePredicateBranches = []
    # print "numOfPredicates: " + str(numOfPredicates)
    for i in range(numOfPredicates):
        for pred in incompletePredicates:
            if pred.index==i:
                eligiblePredicateBranches.append(PredicateBranch.objects.filter(index=i)[0])
                break
    # print "Eligible predicate branches: " + str(eligiblePredicateBranches)
    if (len(eligiblePredicateBranches) != 0):
        chosenBranch = runLotteryWeighted(eligiblePredicateBranches)
    else:
        return None

    # generates the restaurant with the highest priority for the specified 
    # predicate branch
    chosenRestaurant = findRestaurant(chosenBranch, ID)

    # mark chosenRestaurant as being in chosenBranch
    chosenRestaurant.evaluator = chosenBranch.index

    # Find the RestaurantPredicate corresponding to this Restaurant and 
    # PredicateBranch
    chosenPredicate = RestaurantPredicate.objects.filter(restaurant = chosenRestaurant, question = chosenBranch.question)[0]

    return chosenPredicate

def eddy2(ID, numOfPredicates, fast_track):
    """
    Picks a  Restaurant, then uses a lottery system to determine the next PredicateBranch to send the Restaurant to. 
    If the Restaurant is likely to be False for one particular PredicateBranch, it may be "fast-tracked" to that PB rather
    than choosing via the lottery.
    """
    # find the first Restaurant in the queue that isn't finished
    sortedRestaurants = Restaurant.objects.exclude(queueIndex=-1).order_by('queueIndex')

    # return if there are no unfinished Restaurants, otherwise take the first one in the queue
    if len(sortedRestaurants)==0:
        return [None, fast_track]
    else:
        rest = sortedRestaurants[0]

    # find all the Tasks this worker has completed
    completedTasks = Task.objects.filter(workerID=ID)
    
    # find all the RestaurantPredicates matching these completed Tasks
    completedPredicates = RestaurantPredicate.objects.filter(
        id__in=completedTasks.values('restaurantPredicate_id'))

    # get only incomplete RestaurantPredicates matching this Restaurant and eligible to this worker
    incompletePredicates = RestaurantPredicate.objects.exclude(id__in=completedPredicates).filter(restaurant__hasFailed=False).filter(value=None, restaurant=rest)
 
    # check for RestaurantPredicates that are likely to evaluate to False (meeting the specified uncertainty threshold)
    almostFalsePredicates = []

    # finds all the predicates that are almost False, less than 30% uncertain
    for pred in incompletePredicates:
        numYes = len(Task.objects.filter(restaurantPredicate=pred, answer=True))
        numNo = len(Task.objects.filter(restaurantPredicate=pred, answer=False))
        uncertainty = btdtr(numNo+1,numYes+1,0.50)

        if uncertainty < FALSE_THRESHOLD:
            almostFalsePredicates.append( (uncertainty, pred) )

    if len(almostFalsePredicates) > 0:
        # sort according to uncertainty, ascendingly, and return the predicate
        # which is the second item of the first tuple
        almostFalsePredicates.sort()

        fast_track += 1

        return [almostFalsePredicates[0][1], fast_track]

    # If we've failed to find a predicate to prioritize, run the lottery on all eligible PBs
    # finds eligible predicate branches
    eligiblePredicateBranches = []
    for i in range(numOfPredicates):
        for pred in incompletePredicates:
            if pred.index == i:
                eligiblePredicateBranches.append( PredicateBranch.objects.filter(index=i)[0])
                break

    # finds predicate branch using weighted lottery
    if (len(eligiblePredicateBranches) != 0):
        chosenBranch = runLotteryWeighted(eligiblePredicateBranches)
    else:
        return [None, fast_track]

    # Find the RestaurantPredicate corresponding to this Restaurant and 
    # PredicateBranch
    chosenPredicate = RestaurantPredicate.objects.filter(restaurant=rest, question=chosenBranch.question)[0]

    return [chosenPredicate, fast_track]
    
def eddy2(ID, numOfPredicates):
    """
    Picks a  Restaurant, then uses a lottery system to determine the next PredicateBranch to send the Restaurant to. 
    If the Restaurant is likely to be False for one particular PredicateBranch, it may be "fast-tracked" to that PB rather
    than choosing via the lottery.
    """
    # find the first Restaurant in the queue that isn't finished
    sortedRestaurants = Restaurant.objects.exclude(queueIndex=-1).order_by('queueIndex')

    # return if there are no unfinished Restaurants, otherwise take the first one in the queue
    if len(sortedRestaurants)==0:
        return None
    else:
        rest = sortedRestaurants[0]

    # find all the Tasks this worker has completed
    completedTasks = Task.objects.filter(workerID=ID)
    
    # find all the RestaurantPredicates matching these completed Tasks
    completedPredicates = RestaurantPredicate.objects.filter(
        id__in=completedTasks.values('restaurantPredicate_id'))

    # get only incomplete RestaurantPredicates matching this Restaurant and eligible to this worker
    incompletePredicates = RestaurantPredicate.objects.exclude(id__in=completedPredicates).filter(restaurant__hasFailed=False).filter(value=None, restaurant=rest)
 
    # check for RestaurantPredicates that are likely to evaluate to False (meeting the specified uncertainty threshold)
    almostFalsePredicates = []

    # finds all the predicates that are almost False, less than 30% uncertain
    for pred in incompletePredicates:
        numYes = len(Task.objects.filter(restaurantPredicate=pred, answer=True))
        numNo = len(Task.objects.filter(restaurantPredicate=pred, answer=False))
        uncertainty = btdtr(numNo+1,numYes+1,0.50)

        if uncertainty < FALSE_THRESHOLD:
            almostFalsePredicates.append( (uncertainty, pred) )

    if len(almostFalsePredicates) > 0:
        # sort according to uncertainty, ascendingly, and return the predicate
        # which is the second item of the first tuple
        almostFalsePredicates.sort()

        return almostFalsePredicates[0][1]

    # If we've failed to find a predicate to prioritize, run the lottery on all eligible PBs
    # finds eligible predicate branches
    eligiblePredicateBranches = []
    for i in range(numOfPredicates):
        for pred in incompletePredicates:
            if pred.index == i:
                eligiblePredicateBranches.append( PredicateBranch.objects.filter(index=i)[0])
                break

    # finds predicate branch using weighted lottery
    if (len(eligiblePredicateBranches) != 0):
        chosenBranch = runLotteryWeighted(eligiblePredicateBranches)
    else:
        return None

    # Find the RestaurantPredicate corresponding to this Restaurant and 
    # PredicateBranch
    chosenPredicate = RestaurantPredicate.objects.filter(restaurant=rest, question=chosenBranch.question)[0]

    return chosenPredicate

def decrementStatus(index, restaurant):
    """
    decrease the status by 1 once an answer has been submitted for that predicate
    """
    check = 'predicate' + str(index)

    # iterates through all the fields in restaurant
    for field in restaurant._meta.fields:
        if field.verbose_name.startswith(check) and field.verbose_name.endswith('Status'):
            # gets the number times the predicate still needs to be asked to this restaurant
            currentLeftToAsk = getattr(restaurant, field.verbose_name)
            #sets the field to currentLeftToAsk-1
            setattr(restaurant, field.verbose_name, currentLeftToAsk-1)

    restaurant.save()

def incrementStatus(index, restaurant):
    """
    Increases the number of responses needed for an item-predicate pair by 2.
    """
    statusName = 'predicate' + str(index) + 'Status'

    if getattr(restaurant, statusName)==0:
        setattr(restaurant, statusName, 2)

    restaurant.save()

    return restaurant

def findTotalTickets(pbSet):
    """
    Find the total number of "tickets" held by a set of PredicateBranches, multiplying their
    selectivities by 1000 and casting them to integers.
    """
    totalTickets = 0

    # award tickets based on computed selectivity
    for pb in pbSet:
        selectivity = float(pb.returnedNo)/float(pb.returnedTotal)
        totalTickets += int(selectivity*1000)

    return int(totalTickets)

def runLottery(pbSet):
    """
    Runs a ticket-based lottery to choose a PredicateBranch.
    """
    #retrieves total num of tickets in valid predicates branches
    totalTickets = findTotalTickets(pbSet)
    if totalTickets==0:
        return None

    # generate random number between 1 and totalTickets
    rand = randint(1, totalTickets)

    # check if rand falls in the range corresponding to each predicate
    lowBound = 0
    selectivity = float(pbSet[0].returnedNo)/pbSet[0].returnedTotal
    highBound = selectivity*1000
    
    # an empty PredicateBranch object NOT saved in the database
    chosenBranch = PredicateBranch()

    # loops through all valid predicate branches
    for j in range(len(pbSet)):

        # if rand is in this range, then go to this predicateBranch
        if lowBound <= rand <= highBound:
            chosenBranch = pbSet[j]
            break
        else:
            # move on to next range of predicateBranch
            lowBound = highBound
            nextPredicateBranch = pbSet[j+1]
            nextSelectivity = float(nextPredicateBranch.returnedNo)/nextPredicateBranch.returnedTotal
            highBound += nextSelectivity*1000

    return chosenBranch

def runLotteryWeighted(pbSet):
    """
    Runs a ticket-based lottery to choose a PredicateBranch. Doubles the tickets of the most selective
    PredicateBranch in order to favor it more strongly.
    """
    totalTickets = 0
    tickets = {}
    highestBranch = pbSet[0]

    # assigns tickets to each branch and finds the most selective one
    for branch in pbSet:
        t = (float(branch.returnedNo)/branch.returnedTotal)*1000
        tickets[branch] = t
        totalTickets += t

        if t > (float(highestBranch.returnedNo)/highestBranch.returnedTotal)*1000:
            highestBranch = branch
            highestSelectivity = float(highestBranch.returnedNo)/highestBranch.returnedTotal

    # favors most selective branch
    if True:
        tickets[highestBranch] *= WEIGHT_FACTOR
        totalTickets += tickets[highestBranch]*(WEIGHT_FACTOR-1)/WEIGHT_FACTOR
    else:
        tickets[highestBranch] += ADDITIVE_FACTOR
        totalTickets += ADDITIVE_FACTOR

    # generate random number between 1 and totalTickets
    rand = randint(1, int(totalTickets))
    # check if rand falls in the range corresponding to each predicate
    
    lowBound = 0
    highBound = tickets[pbSet[0]]
    # an empty PredicateBranch object NOT saved in the database
    chosenBranch = PredicateBranch()
    # loops through all valid predicate branches
    for j in range(len(pbSet)):
        # if rand is in this range, then go to this predicateBranch
        if lowBound <= rand <= highBound:
            chosenBranch = pbSet[j]
            break
        else:
            # move on to next range of predicateBranch
            lowBound = highBound
            nextPredicateBranch = pbSet[j+1]
            highBound += tickets[nextPredicateBranch]

    return chosenBranch

def runLotteryWeightedWithMemory(pbSet):
    """
    Runs a ticket-based lottery to choose a PredicateBranch. Doubles the tickets of the most selective
    PredicateBranch in order to favor it more strongly. Remembers which PredicateBranch had the highest selectivity
    in the last run of the lottery, and requires that another PredicateBranch have a selectivity that is higher by a certain 
    threshold in order to become the new favored PredicateBranch. This is done so that the choice of which PredicateBranch is
    weighted (favored) changes less often. (This lottery is kept for possible future exploration but not currently
    in use.)
    """
    global INDEX

    changeBranch = True
    pastBranchExists = False

    totalTickets = 0
    tickets = {}
    highestBranch = pbSet[0]

    highestSelectivity = 0
    otherSelectivities = 0

    # checks if highest predicate branch from last time still exists in pbSet
    for pb in pbSet:
        if pb.index == INDEX:
            pastBranchExists = True
            predBranch = pb
            break

    # assigns tickets to each predicate branch and finds branch with highest selectivity
    for branch in pbSet:
        # print branch.question
        t = (float(branch.returnedNo)/branch.returnedTotal)*1000
        tickets[branch] = t
        totalTickets += t

        if t > (float(highestBranch.returnedNo)/highestBranch.returnedTotal)*1000:
            highestBranch = branch
            highestSelectivity = float(highestBranch.returnedNo)/highestBranch.returnedTotal

    # an empty PredicateBranch object NOT saved in the database
    chosenBranch = PredicateBranch()

    # if the branch picked before still exists, check if new branch surpasses threshold
    if pastBranchExists:
        # TODO: should not change branch more often as tasks increase aka memory threshold should increase
        if float(highestBranch.returnedNo)/float(highestBranch.returnedTotal) - float(
            predBranch.returnedNo)/float(predBranch.returnedTotal) < MEMORY_THRESHOLD: 
            changeBranch = False

    # favors the most selective one if it surpasses the threshold
    # TODO: should have an additive option
    if changeBranch:
        tickets[highestBranch] *= WEIGHT_FACTOR
        totalTickets += tickets[highestBranch]/WEIGHT_FACTOR*(WEIGHT_FACTOR-1)
    else:
        tickets[predBranch] *= WEIGHT_FACTOR
        totalTickets += tickets[predBranch]/WEIGHT_FACTOR*(WEIGHT_FACTOR-1)

    # generate random number between 1 and totalTickets
    rand = randint(1, int(totalTickets))
    # check if rand falls in the range corresponding to each predicate
    
    lowBound = 0
    highBound = tickets[pbSet[0]]
    # an empty PredicateBranch object NOT saved in the database
    chosenBranch = PredicateBranch()
    # loops through all valid predicate branches
    for j in range(len(pbSet)):
        # if rand is in this range, then go to this predicateBranch
        if lowBound <= rand <= highBound:
            chosenBranch = pbSet[j]
            break
        else:
            # move on to next range of predicateBranch
            lowBound = highBound
            nextPredicateBranch = pbSet[j+1]
            highBound += tickets[nextPredicateBranch]

    INDEX = chosenBranch.index

    return chosenBranch

def runLotteryDynamicallyWeighted(pbSet):
    """
    Runs a ticket-based lottery to choose a PredicateBranch. Increases the tickets of the most selective
    PredicateBranch in order to favor it more strongly. The weighting factor increases with the number of
    tasks done, up to a maximum of 2. (This lottery is kept for possible future exploration but not currently
    in use.)
    """
    totalTickets = 0
    tickets = {}
    highestBranch = pbSet[0]
    for branch in pbSet:
        t = (float(branch.returnedNo)/branch.returnedTotal)*1000
        tickets[branch] = t
        totalTickets += t
        if t > (float(highestBranch.returnedNo)/highestBranch.returnedTotal)*1000:
            highestBranch = branch

    # TODO: how quickly should weighting increase? When should it stop increasing? Up to what weight should it increase?
    if len(Task.objects.all()) < 100:
        tickets[highestBranch] *= (1+len(Task.objects.all())/25*.25)
    else:
        tickets[highestBranch] *= 2

    # generate random number between 1 and totalTickets
    rand = randint(1, int(totalTickets))

    # check if rand falls in the range corresponding to each predicate
    lowBound = 0
    highBound = tickets[pbSet[0]]
    
    # an empty PredicateBranch object NOT saved in the database
    chosenBranch = PredicateBranch()
    # loops through all valid predicate branches
    for j in range(len(pbSet)):

        # if rand is in this range, then go to this predicateBranch
        if lowBound <= rand <= highBound:
            chosenBranch = pbSet[j]
            break
        else:
            # move on to next range of predicateBranch
            lowBound = highBound
            nextPredicateBranch = pbSet[j+1]
            highBound += tickets[nextPredicateBranch]

    return chosenBranch

def runLotteryWithUniform(pbSet):
    """
    Runs a ticket-based lottery to choose a PredicateBranch. Averages the selectivity distribution with a uniform distribution
    to favor "exploration" of different PredicateBranches more strongly. (This lottery is kept for possible future exploration but not currently
    in use.)
    """
    totalTickets = 0.0
    rangeRand = 0.0
    tickets = {}
    highestBranch = pbSet[0]

    # TODO: find optimal alpha/gamma values. Don't even know if this is implemented correctly.
    for branch in pbSet:
        totalTickets += float((1+ALPHA)**(branch.returnedNo))

    for branch in pbSet:
        tickets[branch] = ( (float(1+ALPHA)**(branch.returnedNo))/totalTickets*(1-GAMMA) + GAMMA/len(PredicateBranch.objects.all()) ) * 1000
        rangeRand+= tickets[branch]

    # generate random number between 1 and totalTickets
    rand = randint(1, int(rangeRand))

    # check if rand falls in the range corresponding to each predicate
    
    lowBound = 0
    highBound = tickets[pbSet[0]]
    
    # an empty PredicateBranch object NOT saved in the database
    chosenBranch = PredicateBranch()
    # loops through all valid predicate branches
    for j in range(len(pbSet)):

        # if rand is in this range, then go to this predicateBranch
        if lowBound <= rand <= highBound:
            chosenBranch = pbSet[j]
            break
        else:
            # move on to next range of predicateBranch
            lowBound = highBound
            nextPredicateBranch = pbSet[j+1]
            highBound += tickets[nextPredicateBranch]

    return chosenBranch
    
def findRestaurant(predicateBranch,ID):
    """
    Finds the restaurant with the highest priority for a specified predicate such that the relevant worker
    has not answered the relevant question about the restaurant.
    """
    # find all the tasks this worker has completed
    completedTasks = Task.objects.filter(workerID=ID)

    # find all the predicates for this branch that have been done by the worker
    completedPredicates = RestaurantPredicate.objects.filter(question=predicateBranch.question).filter(
        id__in=completedTasks.values('restaurantPredicate_id')).filter(value=None)

    # get the Restaurants NOT associated with the completed predicates
    rSet = Restaurant.objects.exclude(id__in=completedPredicates.values('restaurant_id')).exclude(hasFailed=True)

    # order the eligible restaurants by priority
    orderByThisStatus = '-predicate' + str(predicateBranch.index) + 'Status'
    prioritized = rSet.order_by(orderByThisStatus)

    return prioritized[0]

# def findRestaurant(predicateBranch,ID):
#     """
#     Finds a random eligible restaurant.
#     """
#     # find all the tasks this worker has completed
#     completedTasks = Task.objects.filter(workerID=ID)

#     # find all the predicates for this branch that have been done by the worker
#     completedPredicates = RestaurantPredicate.objects.filter(question=predicateBranch.question).filter(
#         id__in=completedTasks.values('restaurantPredicate_id')).filter(value=None)

#     # get the Restaurants NOT associated with the completed predicates
#     rSet = Restaurant.objects.exclude(id__in=completedPredicates.values('restaurant_id')).exclude(hasFailed=True).order_by('?')

#     return rSet[0]

#------------------------------------------------------------------------------------------------------------------------------------#
  
    #     if status > 0:
    #         lowestStat = status
    #         break

    # lowestUncertainty = 1.0
    # predicate = RestaurantPredicate.objects.filter(question=predicateBranch.question)[0]
    # for restaurant in prioritized:
    #     status = getattr(restaurant, predStatus)

    #     if status > lowestStat:
    #         break

    #     if status == lowestStat:

    #         yes = Task.objects.filter(restaurantPredicate=predicate, answer = True)
    #         no = Task.objects.filter(restaurantPredicate=predicate, answer = False)

    #         totalYes = 0.0
    #         totalNo = 0.0

    #         for pred in yes:
    #             totalYes += pred.confidenceLevel/100.0
    #             totalNo += 1 - pred.confidenceLevel/100.0

    #         for pred in no:
    #             totalYes += 1 - pred.confidenceLevel/100.0
    #             totalNo += pred.confidenceLevel/100.0

    #         uncertaintyLevelFalse = btdtr(totalNo+1, totalYes+1, DECISION_THRESHOLD)

    #         if uncertaintyLevelFalse < lowestUncertainty:
    #             chosenRestaurant = restaurant
    #             lowestUncertainty = uncertaintyLevelFalse

    # return chosenRestaurant

#--------------------------------------------------------------------------------------------------------------------------------------#

def randomAlgorithm(ID, numOfPredicates):
    """
    Randomly selects the next predicate from the available choices. Does not use lottery or queue.
    """
    # get all the tasks this worker has done
    completedTasks = Task.objects.filter(workerID=ID)

    # find all the predicates that haven't been done by this worker
    notCompletedPredicates = RestaurantPredicate.objects.exclude(id__in=completedTasks.values('restaurantPredicate_id')).filter(value=None).exclude(restaurant__hasFailed=True)

    if len(notCompletedPredicates) == 0:
        return None
    else:
        chosenPredicate = choice(notCompletedPredicates)
         # mark chosenRestaurant as being in chosenBranch
        chosenPredicate.restaurant.evaluator = chosenPredicate.index

        return chosenPredicate

