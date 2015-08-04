

def test_many_simulation(self, parameters):
        """
        A version of test_simulation that runs many simulations repeatedly in order to get aggregated data.
        """

        # record simulation identifying information to be put in each results file
        label=[]
        label.append(["Parameters:", str(parameters)])
        now = datetime.datetime.now() # get the timestamp
        label.append(["Time stamp:", str(now)])

        NUM_SIMULATIONS = parameters[0]
        NUM_RESTAURANTS = parameters[1]

        # Create restaurants with corresponding RestaurantPredicates and PredicateBranches
        for i in range(NUM_RESTAURANTS):
            enterRestaurant("Kate " + str(i), i)

        # set the selectivities and difficulties of each branch from parameters list
        branches = PredicateBranch.objects.all().order_by("index")
        branchSelectivities = {branches[0] : parameters[4],
                               branches[1] : parameters[5],
                               branches[2] : parameters[6]}
        branchDifficulties = {branches[0] : parameters[7],
                              branches[1] : parameters[8],
                              branches[2] : parameters[9]}

        recordAggregateStats = parameters[10]
        recordEddyStats = parameters[11]
        recordEddy2Stats = parameters[12]
        recordRandomStats = parameters[13]

        # establish a set of known correct answers
        predicateAnswers = self.set_correct_answers(branches, branchSelectivities, parameters[14])

        aggregateResults = [label, ["eddy num tasks", "eddy correct percentage", "eddy 2 num tasks", "eddy2 correct percentage", 
                           "random num tasks", "random correct percentage"]]

        # Use the established items, questions, selectivities, difficulties, etc to run as many simulations as specified
        for k in range(NUM_SIMULATIONS):

            print "Eddy " + str(k)
            results_eddy = self.run_simulation(eddy, branches, branchDifficulties, parameters, predicateAnswers)
            eddyTasks = len(Task.objects.all())

            # Of the answered predicates, count how many are correct
            correctCount = 0
            for predicate in RestaurantPredicate.objects.exclude(value=None):
                if predicate.value == predicateAnswers[predicate]:
                    correctCount += 1
            eddyCorrectPercentage = float(correctCount)/len(RestaurantPredicate.objects.exclude(value=None))
            
            if recordEddyStats: self.write_results(results_eddy, "eddy")
            self.reset_simulation()

            print "Eddy2 " + str(k)
            results_eddy = self.run_simulation(eddy2, branches, branchDifficulties, parameters, predicateAnswers)
            eddy2Tasks = len(Task.objects.all())

            # Of the answered predicates, count how many are correct
            correctCount = 0
            for predicate in RestaurantPredicate.objects.exclude(value=None):
                if predicate.value == predicateAnswers[predicate]:
                    correctCount += 1
            eddy2CorrectPercentage = float(correctCount)/len(RestaurantPredicate.objects.exclude(value=None))
            
            if recordEddyStats: self.write_results(results_eddy, "eddy2")
            self.reset_simulation()

            print "Random " + str(k)
            results_random = self.run_simulation(randomAlgorithm, branches, branchDifficulties, parameters, predicateAnswers)
            randomTasks = len(Task.objects.all())

            # Of the answered predicates, count how many are correct
            correctCount = 0
            for predicate in RestaurantPredicate.objects.exclude(value=None):
                if predicate.value == predicateAnswers[predicate]:
                    correctCount += 1
            randomCorrectPercentage = float(correctCount)/len(RestaurantPredicate.objects.exclude(value=None))
            
            if recordRandomStats: self.write_results(results_random, "random")
            self.reset_simulation()

            if recordAggregateStats: aggregateResults.append([eddyTasks, eddyCorrectPercentage, eddy2Tasks, eddy2CorrectPercentage, randomTasks, randomCorrectPercentage])

        self.clear_database()
  
        if recordAggregateStats: self.write_results(aggregateResults, "aggregate_results")
def set_correct_answers(self, branches, branchSelectivities, answers):
        """
        Creates a dictionary with a correct answer for each predicate in the database.
        """
        # dictionary of correct answers
        predicateAnswers = {}
        
        # define sets of all restaurant predicates according to their indices
        allRestPreds0 = RestaurantPredicate.objects.all().filter(index=0)
        allRestPreds1 = RestaurantPredicate.objects.all().filter(index=1)
        allRestPreds2 = RestaurantPredicate.objects.all().filter(index=2)
        predicateSets = [allRestPreds0, allRestPreds1, allRestPreds2]

        # define correct answers based on each predicate's selectivity
        # for predicateSet in predicateSets:
        #     while len(predicateSet) != 0:

        #         # pick one predicate to define a correct answer for
        #         restPred = choice(predicateSet)
        #         predicateSet = predicateSet.exclude(id=restPFalsered.id)

        #         # probabilistically assign the correct answer
        #         if random() < branchSelectivities[branches[restPred.index]]:
        #             predicateAnswers[restPred] = False
        #         else:
        #             predicateAnswers[restPred] = True

        # Small Test Cases
        # setting answers according to predicates
        # for i in range(len(allRestPreds0)):
        #     predicateAnswers[allRestPreds0[i]] = True

        # for i in range(len(allRestPreds1)):
        #     predicateAnswers[allRestPreds1[i]]  = True

        # for i in range(len(allRestPreds2)):
        #     predicateAnswers[allRestPreds2[i]]  = False

        #-----------------------------------------------------------------------------------------------------------------------------------#

        # setting answers according to restaurants
        # allRestaurants = Restaurant.objects.all()

        # predicates = RestaurantPredicate.objects.all().filter(restaurant=allRestaurants[0])
        # for pred in predicates:
        #     predicateAnswers[pred] = True

        # predicates = RestaurantPredicate.objects.all().filter(restaurant=allRestaurants[1])
        # for pred in predicates:
        #     predicateAnswers[pred] = False

        i = 0
        for rest in Restaurant.objects.all():
            for pb in PredicateBranch.objects.order_by('index'):
                pred = RestaurantPredicate.objects.filter(restaurant=rest, index=pb.index)[0]
                predicateAnswers[pred] = answers[i]
                i += 1

        return predicateAnswers      
def test_many_simulation_controller(self):
        """
        Calls the test_many_simulation function with as many sets of parameters as are specified.
        """
        recordAggregateStats = True # record the number of tasks and correct percentage for each run of each algorithm in one file

        # choose whether to record individual run stats in separate files
        eddy = False
        eddy2 = False
        random = False
        
        parameterSets = []
        #selectivity 0, selectivity 1, selectivity 2, branchDifficulties dictionary

        answers1 = [True, True, False,
                   True, True, False,
                   True, True, False,
                   True, True, False,
                   True, True, False,
                   True, True, False,
                   True, True, False,
                   True, True, False,
                   True, True, False,
                   True, True, False]

        set1 =[ 100, # number of simulations
                10, # number of restaurants
                [100,100,100,100,100], # confidence options
                [0.0], # personality options
                0.0, # selectivity 0
                0.0, # selectivity 1
                0.0, # selectivity 2
                0.0, # difficulty 0
                0.0, # difficulty 1
                0.0, # difficulty 2
                recordAggregateStats,
                eddy,
                eddy2,
                random,
                answers1
                ]
        parameterSets.append(set1)

        # answers2 = [False, False, True,
        #            True, False, False,
        #            False, True, True,
        #            True, False, False,
        #            False, True, False,
        #            False, True, True,
        #            True, False, True,
        #            True, True, False,
        #            False, True, True,
        #            True, False, False]

        # set2 =[ 100, # number of simulations
        #         10, # number of restaurants
        #         [100,100,100,100,100], # confidence options
        #         [0.0], # personality options
        #         0.0, # selectivity 0
        #         0.0, # selectivity 1
        #         0.0, # selectivity 2
        #         0.0, # difficulty 0
        #         0.0, # difficulty 1
        #         0.0, # difficulty 2
        #         recordAggregateStats,
        #         eddy,
        #         eddy2,
        #         random,
        #         answers2
        #         ]
        # parameterSets.append(set2)

        # answers3 = [False, False, False,
        #            True, False, False,
        #            False, True, False,
        #            True, False, False,
        #            False, True, False,
        #            False, True, True,
        #            True, False, True,
        #            True, True, False,
        #            False, True, False,
        #            True, False, False]

        # set3 =[ 100, # number of simulations
        #         10, # number of restaurants
        #         [100,100,100,100,100], # confidence options
        #         [0.0], # personality options
        #         0.0, # selectivity 0
        #         0.0, # selectivity 1
        #         0.0, # selectivity 2
        #         0.0, # difficulty 0
        #         0.0, # difficulty 1
        #         0.0, # difficulty 2
        #         recordAggregateStats,
        #         eddy,
        #         eddy2,
        #         random,
        #         answers3
        #         ]
        # parameterSets.append(set3)

        # answers4 = [False, False, True,
        #            False, False, False,
        #            False, False, False,
        #            False, False, False,
        #            False, False, False,
        #            False, True, False,
        #            False, False, False,
        #            False, False, False,
        #            False, False, False,
        #            True, False, False]

        # set4 =[ 100, # number of simulations
        #         10, # number of restaurants
        #         [100,100,100,100,100], # confidence options
        #         [0.0], # personality options
        #         0.0, # selectivity 0
        #         0.0, # selectivity 1
        #         0.0, # selectivity 2
        #         0.0, # difficulty 0
        #         0.0, # difficulty 1
        #         0.0, # difficulty 2
        #         recordAggregateStats,
        #         eddy,
        #         eddy2,
        #         random,
        #         answers4
        #         ]
        # parameterSets.append(set4)

        # answers5 = [True, True, True,
        #            True, True, True,
        #            True, False, True,
        #            False, True, True,
        #            True, True, False,
        #            True, True, True,
        #            True, True, True,
        #            True, True, True,
        #            True, True, True,
        #            True, True, True]

        # set5 =[ 100, # number of simulations
        #         10, # number of restaurants
        #         [100,100,100,100,100], # confidence options
        #         [0.0], # personality options
        #         0.0, # selectivity 0
        #         0.0, # selectivity 1
        #         0.0, # selectivity 2
        #         0.0, # difficulty 0
        #         0.0, # difficulty 1
        #         0.0, # difficulty 2
        #         recordAggregateStats,
        #         eddy,
        #         eddy2,
        #         random,
        #         answers5
        #         ]
        # parameterSets.append(set5)
    
        # answers6 = [True, True, True,
        #            True, True, True,
        #            True, False, True,
        #            False, True, True,
        #            True, True, False,
        #            True, True, True,
        #            True, False, True,
        #            True, True, False,
        #            True, True, True,
        #            True, True, False]

        # set6 =[ 100, # number of simulations
        #         10, # number of restaurants
        #         [100,100,100,100,100], # confidence options
        #         [0.0], # personality options
        #         0.0, # selectivity 0
        #         0.0, # selectivity 1
        #         0.0, # selectivity 2
        #         0.0, # difficulty 0
        #         0.0, # difficulty 1
        #         0.0, # difficulty 2
        #         recordAggregateStats,
        #         eddy,
        #         eddy2,
        #         random,
        #         answers6
        #         ]
        # parameterSets.append(set6)

        # answers7 = [True, True, False,
        #            True, False, False,
        #            True, False, False,
        #            False, True, False,
        #            True, True, False,
        #            True, True, False,
        #            True, False, True,
        #            True, True, False,
        #            True, False, False,
        #            True, False, False]

        # set7 =[ 100, # number of simulations
        #         10, # number of restaurants
        #         [100,100,100,100,100], # confidence options
        #         [0.0], # personality options
        #         0.0, # selectivity 0
        #         0.0, # selectivity 1
        #         0.0, # selectivity 2
        #         0.0, # difficulty 0
        #         0.0, # difficulty 1
        #         0.0, # difficulty 2
        #         recordAggregateStats,
        #         eddy,
        #         eddy2,
        #         random,
        #         answers7
        #         ]
        # parameterSets.append(set7)

        # answers8 = [False, True, False,
        #            True, False, False,
        #            False, False, False,
        #            False, False, False,
        #            True, True, False,
        #            False, False, False,
        #            False, False, True,
        #            True, False, False,
        #            False, False, False,
        #            False, False, False]

        # set8 =[ 100, # number of simulations
        #         10, # number of restaurants
        #         [100,100,100,100,100], # confidence options
        #         [0.0], # personality options
        #         0.0, # selectivity 0
        #         0.0, # selectivity 1
        #         0.0, # selectivity 2
        #         0.0, # difficulty 0
        #         0.0, # difficulty 1
        #         0.0, # difficulty 2
        #         recordAggregateStats,
        #         eddy,
        #         eddy2,
        #         random,
        #         answers8
        #         ]
        # parameterSets.append(set8)

        # answers9 = [False, True, False,
        #            True, False, False,
        #            False, False, True,
        #            True, True, False,
        #            True, True, True,
        #            False, True, False,
        #            True, False, True,
        #            True, True, False,
        #            False, False, True,
        #            True, False, False]
                   
        # set9 =[ 100, # number of simulations
        #         10, # number of restaurants
        #         [100,100,100,100,100], # confidence options
        #         [0.0], # personality options
        #         0.0, # selectivity 0
        #         0.0, # selectivity 1
        #         0.0, # selectivity 2
        #         0.0, # difficulty 0
        #         0.0, # difficulty 1
        #         0.0, # difficulty 2
        #         recordAggregateStats,
        #         eddy,
        #         eddy2,
        #         random,
        #         answers9
        #         ]
        # parameterSets.append(set9)

        for parameters in parameterSets:
            print "Parameter set: " + str(parameters)
            self.test_many_simulation(parameters)

       # an audio alert that the tests are done
        os.system('say "simulations complete"')
