# A draft version of the eddy lottery code (to build independently and then 
# integrate)

# -*- coding: utf-8 -*-

from random import randint, choice, random

class LotteryTestClass:

    # [fixed selectivity, total, no, computed selectivity]
    # selectivity = no / total
    predicate1 = [0.20, 0, 0.0, 1.0]
    predicate2 = [0.70, 0, 0.0, 1.0]
    predicate3 = [0.85, 0, 0.0, 1.0]
    predicates = [predicate1, predicate2, predicate3]
    debug = False

    def runLottery(self):
        HITS = 100

        for i in range(0,HITS):
            totalTickets = self.findTotalTickets()

            rand = randint(1, totalTickets)
            if self.debug: print "rand int: " + str(rand)
            # check if rand falls in the range corresponding to each predicate
            lowBound = 0
            highBound = self.predicates[0][3]*100

            for j in range(len(self.predicates)):
                if self.debug: print "Finding if in range of predicate " + 
                    str(j) + "low: " + str(lowBound) + ", high: " + 
                    str(highBound)

                if lowBound <= rand <= highBound:
                    self.evaluatePredicate(self.predicates[j])
                    break
                else:
                    if self.debug: print "Moving to next range on predicate " + 
                        str(j)
                    lowBound = highBound

                    if self.debug: print "j: " + str(j)

                    nextPredicate = self.predicates[j+1]
                    highBound += nextPredicate[3]*100

                    if self.debug: print "new low: " + str(lowBound) + 
                        "new high: " + str(highBound)

        # print results
        print "\n"
        for predicate in self.predicates:
            print predicate

    def findTotalTickets(self):
        totalTickets = 0

        # award tickets based on computed selectivity
        for predicate in self.predicates:
            totalTickets += predicate[3]*100
        return int(totalTickets)

    def evaluatePredicate(self, predicate):
        # increment total
        predicate[1] += 1.0

        # probabilistically choose yes or no
        rand = random()
        if rand <= predicate[0]:
            # increment no
            predicate[2] += 1.0
            
        # recompute selectivity
        predicate[3] = (predicate[2] + 1)/ (predicate[1]+1)