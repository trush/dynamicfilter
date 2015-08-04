def test_simulation(self):

    label = raw_input("Label this simulation test: ")

    NUM_RESTAURANTS = 10
    AVERAGE_TIME = 60000 # 60 seconds
    STANDARD_DEV = 20000 # 20 seconds
    CONFIDENCE_OPTIONS = [60,60,80,100,100]
    PERSONALITIES = [0,0,0,0,0]
    SELECTIVITY_0 = 0.0
    SELECTIVITY_1 = 0.0
    SELECTIVITY_2 = 0.0

    graphData = []

    # Save the time and date of simulation
    now = datetime.datetime.now()

    # Create restaurants with PBs and RPs
    for i in range(NUM_RESTAURANTS):
        enterRestaurant("Kate " + str(i), i)

    branches = PredicateBranch.objects.all()
    branchDifficulties = {branches[0] : 0.0,
                          branches[1] : 0.0,
                          branches[2] : 0.0}

    # dictionary of predicates as keys and their true answers as values
    predicateAnswers = {}
    
    # all restaurant predicates according to their respective indices
    allRestPreds0 = RestaurantPredicate.objects.all().filter(index=0)
    allRestPreds1 = RestaurantPredicate.objects.all().filter(index=1)
    allRestPreds2 = RestaurantPredicate.objects.all().filter(index=2)

    # set answers based on predicate's selectivity
    while len(allRestPreds0) != 0:

        restPred = choice(allRestPreds0)
        allRestPreds0 = allRestPreds0.exclude(id=restPred.id)

        if random() < SELECTIVITY_0:
            predicateAnswers[restPred] = False
        else:
            predicateAnswers[restPred] = True

    while len(allRestPreds1) != 0:
        restPred = choice(allRestPreds1)
        allRestPreds1 = allRestPreds1.exclude(id=restPred.id)

        if random() < SELECTIVITY_1:
            predicateAnswers[restPred] = False
        else:
            predicateAnswers[restPred] = True

    while len(allRestPreds2) != 0:
        restPred = choice(allRestPreds2)
        allRestPreds2 = allRestPreds2.exclude(id=restPred.id)

        if random() < SELECTIVITY_2:
            predicateAnswers[restPred] = False
        else:
            predicateAnswers[restPred] = True

    # start keeping track of worker IDs at 100
    IDcounter = 100

    # keeps track of how many tasks related to each branch are actually No's
    predIdealNo     = {branches[0]:0,
                       branches[1]:0,
                       branches[2]:0}
    predActualNo    = {branches[0]:0,
                       branches[1]:0,
                       branches[2]:0}
    predActualTotal = {branches[0]:0,
                       branches[1]:0,
                       branches[2]:0}

    # choose one predicate to start
    predicate = eddy(IDcounter)
  
    while (predicate != None):
        # default answer is the correct choice
        answer = predicateAnswers[predicate]

        # choose a time by sampling from a distribution
        completionTime = normal(AVERAGE_TIME, STANDARD_DEV)
        
        # randomly select a confidence level
        confidenceLevel = choice(CONFIDENCE_OPTIONS)

        # if the correct answer is False, then add it to the ideal dictionary to keep track
        if answer == False:
            predIdealNo[branches[predicate.index]] += 1

        # add to the total number of predicates flowing to a branch
        predActualTotal[branches[predicate.index]] += 1

        # generate random decimal from 0 to 1
        randNum = random()
    
        branch = PredicateBranch.objects.filter(index=predicate.index)[0]
        if randNum < branchDifficulties[branch] + choice(PERSONALITIES):
            # the worker gets the question wrong
            answer = not answer

        # if the worker's answer is False, then add it to the actual dictionary
        if answer == False:
            predActualNo[branches[predicate.index]] += 1

        # make Task answering the predicate, using answer and time
        task = enterTask(IDcounter, answer, completionTime, confidenceLevel, predicate)

        # appends data of predicate 0 to graph later
        if branch.index==0:
            graphData.append([predActualTotal[branch], float(branch.returnedNo)/branch.returnedTotal])

        # get the associated PredicateBranch
        pB = PredicateBranch.objects.filter(question=predicate.question)[0]
        updateCounts(pB, task)
        decrementStatus(predicate.index, predicate.restaurant)
        
        statusName = "predicate" + str(predicate.index) + "Status"
        if getattr(predicate.restaurant, statusName)==0:
            predicate.restaurant = aggregate_responses(predicate)

        predicate.restaurant.evaluator = None
        predicate.save()

        # increase IDcounter
        IDcounter += 1
        # get a predicate from the eddy
        predicate = eddy(IDcounter)
    
    # write results to file
    l = []
    l.append(["Simulation Test:", label])
    l.append(["Timestamp:", str(now)])
    l.append(["Number of tasks completed by workers:", str(len(Task.objects.all()))])
    l.append(["Total Restaurants: ",NUM_RESTAURANTS])

    # Of the answered predicates, count how many are correct
    correctCount = 0
    for predicate in RestaurantPredicate.objects.exclude(value=None):
        if predicate.value == predicateAnswers[predicate]:
            correctCount += 1

    l.append(["Correct percentage:", float(correctCount)/len(RestaurantPredicate.objects.exclude(value=None))])

    totalCompletionTime = 0
    for task in Task.objects.all():
        totalCompletionTime += task.completionTime
    l.append(["Total completion time of all tasks (minutes):", totalCompletionTime/60000.0])

    l.append([])
    l.append(["PredicateBranch", "Difficulty", "Ideal Selectivity", "Unweighted Task Selectivity", "Weighted Task Selectivity", "Total Returned", "Returned No"])
    for branch in PredicateBranch.objects.all():
        predicateBranchRow = []
        predicateBranchRow.append(branch.question)
        predicateBranchRow.append(branchDifficulties[branch])

        # record ideal selectivity
        if predActualTotal[branch] != 0:
            predicateBranchRow.append(float(predIdealNo[branch])/float(predActualTotal[branch]))
        else:
            predicateBranchRow.append("None evaluated")

        # record unweighted task selectivity
        if predActualTotal[branch] != 0:
            predicateBranchRow.append(float(predActualNo[branch])/float(predActualTotal[branch]))
        else:
            predicateBranchRow.append("None evaluated")

        predicateBranchRow.append(float(branch.returnedNo)/branch.returnedTotal)
        predicateBranchRow.append(branch.returnedTotal)
        predicateBranchRow.append(branch.returnedNo)
        l.append(predicateBranchRow)

    l.append([])
    l.append(["Restaurant", "Predicate 0", "Predicate 1", "Predicate 2", "Passed Filter"])
    for rest in Restaurant.objects.all():
        restaurantRow = []
        restaurantRow.append(rest.name)
        for predicate in RestaurantPredicate.objects.filter(restaurant=rest):
            restaurantRow.append(predicate.value)
        restaurantRow.append(not rest.hasFailed)
        l.append(restaurantRow)

    with open('test_results/test' + str(now.date())+ "_" + str(now.time())[:-7] + '.csv', 'w') as csvfile:
        writer = csv.writer(csvfile)
        [writer.writerow(r) for r in l]

    # with open('test_results/graph' + str(now.date())+ "_" + str(now.time())[:-7] + '.csv', 'w') as csvfile:
    #     writer = csv.writer(csvfile)
    #     [writer.writerow(r) for r in graphData]