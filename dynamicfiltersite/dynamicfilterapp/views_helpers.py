from models import Task, RestaurantPredicate, Restaurant, PredicateBranch
from scipy.special import btdtr
from random import randint

# we need at least half of the answers to be True in order for the value of the predicate to be True
# and same for False's
DECISION_THRESHOLD = 0.5

# the uncertainty level determined by the beta distribution function needs to be less than 0.15
# for us to fix the predicate's value
UNCERTAINTY_THRESHOLD = 0.15

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
        #print "predicate value set to true"
        predicate.value = True

    # if more no's than yes's
    elif totalNo > totalYes and uncertaintyLevelFalse < UNCERTAINTY_THRESHOLD:
        predicate.value = False
        #print "predicate value set to false"

        # flag for the Restaurant failing a predicate (and thus not passing all the predicates)
        predicateFailed = False

        # iterates through all the fields in this restaurant's model
        for field in predicate.restaurant._meta.fields:
            #print "Field " + str(field)
            # verbose_name is the field's name with underscores replaced with spaces
            if field.verbose_name.startswith('predicate') and field.verbose_name.endswith('Status') and getattr(predicate.restaurant, field.verbose_name) == 0:
                predicateFailed = True
                #print "PREDICATE FAILED :("
                break

        if predicateFailed:
            predicate = setFieldsToNegOne(predicate)

    if predicate.value==None:
        # collect five more responses from workers when there are same 
        # number of yes and no
        predicate.restaurant = incrementStatusByFive(predicate.index, predicate.restaurant)
    predicate.restaurant.save()
    predicate.save()
    #print predicate.restaurant.predicate0Status 
    printResults()

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

def setFieldsToNegOne(predicate):
    """
    Set all predicate status fields to -1 to indicate that it needs no further evaluation (because
    it has failed a predicate)
    """
    #print "Setting fields to -1"
    for field in predicate.restaurant._meta.fields:
        if field.verbose_name.startswith('predicate') and field.verbose_name.endswith('Status'):
            #print "actually setting to -1 now"
            predicate.restaurant.hasFailed = True
    predicate.save()
    return predicate

def updateCounts(pB, task):
    """
    updates the predicate branch's total and "No!" counts relative to the confidence levels
    """
    if task.answer==True:
        pB.returnedTotal += float(task.confidenceLevel)/100.0
    elif task.answer==False:
        print type(task.confidenceLevel)
        pB.returnedTotal += float(task.confidenceLevel)/100.0
        pB.returnedNo += float(task.confidenceLevel)/100.0
    pB.save()

def eddy(ID):
    """
    Uses a random lottery system to determine which eligible predicate should be
    evaluated next.
    """
    debug = True
    #if debug: print "------FINDING ELIGIBLE BRANCHES FOR LOTTERY-----"

    # find all the tasks this worker has completed
    completedTasks = Task.objects.filter(workerID=ID)
    #print "Completed Tasks: " + str(completedTasks)

    # find all the predicates matching these completed tasks
    completedPredicates = RestaurantPredicate.objects.filter(
        id__in=completedTasks.values('restaurantPredicate_id'))
    #print "Completed Predicates: " + str(completedTasks)

    # all fields for a restaurant referenced by an incomplete predicate
    restaurantFields = RestaurantPredicate.objects.all()[0].restaurant._meta.fields

    # finds number of predicate statuses
    numOfPredicateStatuses = 0
    for field in restaurantFields:
        if field.verbose_name.startswith('predicate') and field.verbose_name.endswith('Status'):
            numOfPredicateStatuses += 1

    # excludes all completed predicates from all restaurant predicates to get only incompleted ones
    incompletePredicates1 = RestaurantPredicate.objects.exclude(id__in=completedPredicates)
    #print "incompletePredicates1: " + str(incompletePredicates1)
    incompletePredicates = incompletePredicates1.filter(restaurant__hasFailed=False).filter(value=None)
    #print "incompletePredicates: " + str(incompletePredicates)

    #finds eligible predicate branches
    eligiblePredicateBranches = []
    for i in range(numOfPredicateStatuses):
        for pred in incompletePredicates:
            if pred.index == i:
                eligiblePredicateBranches.append(PredicateBranch.objects.filter(index=i)[0])
                break

    # Find all PredicateBranches with open space and that haven't been completed
    # by this worker
    # allPredicateBranches = PredicateBranch.objects.exclude(
    #     question__in=completedPredicates.values('question'))
    
    #if debug: print "------STARTING LOTTERY------"
    #print "size of all predicate branches: " + str(len(eligiblePredicateBranches))
    if (len(eligiblePredicateBranches) != 0):
        chosenBranch = runLottery(eligiblePredicateBranches)
    else:
        return None

   # print "chosen branch: " + str(chosenBranch)
    # generates the restaurant with the highest priority for the specified 
    # predicate branch
    chosenRestaurant = findRestaurant(chosenBranch, ID)
   # print "chosen restaurant: " + str(chosenRestaurant)
    #  mark chosenRestaurant as being in chosenBranch
    chosenRestaurant.evaluator = chosenBranch.index

    # Find the RestaurantPredicate corresponding to this Restaurant and 
    # PredicateBranch
    chosenPredicate = RestaurantPredicate.objects.filter(restaurant = 
        chosenRestaurant, question = chosenBranch.question)[0]
    #print "Predicate to answer: " + str(chosenPredicate)

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
            #print "Decremented " + field.verbose_name + " to status of " + str(currentLeftToAsk-1)
    restaurant.save()

def incrementStatusByFive(index, restaurant):
    """
    increases the status by 5 because the answer is not certain
    """
    statusName = 'predicate' + str(index) + 'Status'

    if getattr(restaurant, statusName)==0:
        setattr(restaurant, statusName, 5)
    restaurant.save()
    return restaurant

def findTotalTickets(pbSet):
    """
    Finds the total number of "tickets" held by a set of PredicateBranches, by 
    turning selectivity into a useful integer.
    Selectivity = (no's)/(total evaluated)
    """
    totalTickets = 0

    # award tickets based on computed selectivity
    for pb in pbSet:
        selectivity = float(pb.returnedNo)/float(pb.returnedTotal)
        totalTickets += int(selectivity*1000)

    return int(totalTickets)

def runLottery(pbSet):
    """
    runs the lottery algorithm
    """

    #retrieves total num of tickets in valid predicates branches
    totalTickets = findTotalTickets(pbSet)
    if totalTickets==0:
        print "Total tickets is zero"
        return None

    # generate random number between 1 and totalTickets
    rand = randint(1, totalTickets)

    # check if rand falls in the range corresponding to each predicate
    lowBound = 0
    selectivity = float(pbSet[0].returnedNo)/pbSet[0].returnedTotal
    highBound = selectivity*1000
    
    # an empty PredicateBranch object NOT saved in the database
    chosenBranch = PredicateBranch()
    # loops through all predicate branches to see in which predicate branch rand falls in
    #print "-------Check ranges --------"

    # loops through all valid predicate branches
    for j in range(len(pbSet)):
        #print "random number: " + str(rand)
        #print "range: " + str(lowBound) + " to " + str(highBound)

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
    
def findRestaurant(predicateBranch,ID):
    """
    Finds the restaurant with the highest priority for a specified predicate such that the relevant worker
    has not answered the relevant question about the restaurant.
    """
    # find all the tasks this worker has completed
    completedTasks = Task.objects.filter(workerID=ID)
    # print "Completed Tasks: " + str(completedTasks)
    # find all the predicates for this branch that have been done by the worker
    completedPredicates = RestaurantPredicate.objects.filter(question=predicateBranch.question).filter(
        id__in=completedTasks.values('restaurantPredicate_id')).filter(value=None)

    # print "Completed predicates: " + str(completedPredicates)
    # get the Restaurants NOT associated with the completed predicates
    rSet = Restaurant.objects.exclude(id__in=completedPredicates.values('restaurant_id')).exclude(hasFailed=True)
    # print "rSet: " + str(rSet)
    # order the eligible restaurants by priority
    orderByThisStatus = 'predicate' + str(predicateBranch.index) + 'Status'
    prioritized = rSet.order_by(orderByThisStatus)

    # print "Predicate Branch Index: " + str(predicateBranch.index)
    # print " Prioritized: " + str(prioritized)
    # filter out restaurants where the relevant status is not 0 or
    predStatus = 'predicate' + str(predicateBranch.index) + 'Status'
    for restaurant in prioritized:
        status = getattr(restaurant, predStatus)
        #sets the field to currentLeftToAsk-1
        # print "Restaurant " + str(restaurant) + "has status " + str(status)
        if status > 0:
            #print "Satisfied with status " + str(status) + " on restaurant " + str(restaurant)
            return restaurant
    # We should never reach this statement
    return None
