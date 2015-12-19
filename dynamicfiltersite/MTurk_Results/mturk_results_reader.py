import numpy as np
import matplotlib.pyplot as plt
import datetime as DT
import pylab
import sys
import math
import csv

from scipy.stats import beta

# run by typing 
# python mturk_results_reader.py Batch_2019634_batch_results_cleaned.csv correct_answers.csv 

filename = sys.argv[1]
correctAnswersFile = sys.argv[2]

# read in data from workers
data = np.genfromtxt(fname=filename, 
					dtype={'formats': [np.dtype('S30'), np.dtype('S15'), np.dtype(int),
										np.dtype('S50'), np.dtype('S100'), np.dtype(int)],
							'names': ['AssignmentId', 'WorkerId', 'WorkTimeInSeconds',
										'Input.Restaurant', 'Input.Question', 'Answer.Q1AnswerPart1']},
					delimiter=',', usecols=range(6), skip_header=1)

# read in correct answer data
answers = np.genfromtxt(fname=correctAnswersFile, 
						dtype={'formats': [np.dtype('S30'), np.dtype(bool), 
											np.dtype(bool), np.dtype(bool), 
											np.dtype(bool), np.dtype(bool),
											np.dtype(bool), np.dtype(bool), 
											np.dtype(bool), np.dtype(bool), 
											np.dtype(bool),],
								'names': ['Restaurant', 'a0', 'a1', 'a2', 'a3',
										 	'a4', 'a5', 'a6', 'a7', 'a8', 'a9']},
						delimiter=',', usecols=range(11), skip_header=1)

# read in questions (from the first line of the correct answers file)
uniqueQuestions = np.genfromtxt(fname=correctAnswersFile, 
								dtype={'formats': [np.dtype('S100'), np.dtype('S100'),
													np.dtype('S100'), np.dtype('S100'),
													np.dtype('S100'), np.dtype('S100'),
													np.dtype('S100'), np.dtype('S100'),
													np.dtype('S100'), np.dtype('S100'),],
										'names': ['a0', 'a1', 'a2', 'a3', 'a4', 
													'a5', 'a6', 'a7', 'a8', 'a9']},
								delimiter=',', usecols=range(1,11), skip_footer=21)

# prints all the questions
uniqueQuestionsList = list(uniqueQuestions.tolist())
for question in uniqueQuestionsList:
	print question
print "\n"

# Does this restaurant have a parking lot?
# Does this restaurant have a drive-through?
# Does this restaurant have drinks for those under 21?
# Does this restaurant have more than 20 items on its menu?
# Does this restaurant serve Chinese food?
# Is this restaurant open until midnight?
# Would a typical meal at this restaurant cost more than $30?
# Does this restaurant serve breakfast?
# Does this restaurant have its own website?
# Does this restaurant have a romantic atmosphere?

#----------Find Selectivities --------------
# get a list of all 6,000 (question, answer) pairs
questionAnswerPairs = [(value4,value5) for (value0, value1, value2, value3, 
	value4, value5) in data]

# count the number of each answer for each question
answersCount = {}

# stores how many times each answer has been used in a dictionary
for question in uniqueQuestionsList:
	countDict = {100:0,80:0,60:0,0:0,-60:0,-80:0,-100:0}
	relevantPairs = filter(lambda t:t[0]==question, questionAnswerPairs)
	for pair in relevantPairs:
		countDict[pair[1]] += 1
	answersCount[question] = countDict

# compute selectivities using answer counts
for entry in answersCount:
	# print entry
	countDict = answersCount[entry]
	selectivity = (countDict[-100]+countDict[-80]+countDict[-60])/600.0
	print entry
	print "Selectivity: " + str(selectivity) + "\n"
#--------------------------------------------

# create a dictionary of (restaurant, question) keys and boolean correct answer values
correctAnswers = {}

# dictionary of (restaurant, question) keys and two-index array as values
wrongRightCounts = {}

# 
for restRow in answers:
	r = list(restRow)

	for i in range(10):
		key = (r[0], uniqueQuestionsList[i]) # key is restaurant and question
		value = r[i+1] # answer to that restaurant predicate pair
		correctAnswers[key] = value # put both in dictionary
		wrongRightCounts[key] = [0,0] # initialize wrong/right counts at 0,0

restaurantQuestionAnswers = [(value3, value4,value5) for (value0, value1, value2, 
	value3, value4, value5) in data]

# initializes number of yes and no to 1
yesNoCount = {}
for (restaurant, question, answer) in restaurantQuestionAnswers:
	yesNoCount[(restaurant,question)] = [1,1]

# increments yes/no by 1 for each answer
for (restaurant, question, answer) in restaurantQuestionAnswers:
	if answer < 0:
		yesNoCount[(restaurant,question)][1] += 1
	elif answer > 0:
		yesNoCount[(restaurant,question)][0] += 1


#calculate entropy of each restaurant predicate pairs
predicate = []
restaurantArray = []
numYes = []
numNo = []
entropy = []
for (restaurant,question) in yesNoCount:
	predicate.append(question)
	restaurantArray.append(restaurant)
	numYes.append(yesNoCount[(restaurant,question)][0]-1)
	numNo.append(yesNoCount[(restaurant,question)][1]-1)

	probYes = float(yesNoCount[(restaurant,question)][0]) / (yesNoCount[(restaurant,
		question)][0] + yesNoCount[(restaurant,question)][1])
	entr = -1*(probYes * math.log(probYes, 10) + (1-probYes) * math.log(1-probYes, 10))

	entropy.append(entr)

results = [["Predicate", "Restaurant", "Number of Yes", "Number of No", "Entropy"]]
for row in map(None, predicate, restaurantArray, numYes, numNo, entropy):
	results.append(row)

with open('table.csv', 'w') as csvfile:
	writer = csv.writer(csvfile)
	[writer.writerow(r) for r in results]

# initializes dictionary of confidence levels and how many times each one is used
confidenceLevelDist = {}
confidenceLevelDist[-100] = 0
confidenceLevelDist[-80] = 0
confidenceLevelDist[-60] = 0
confidenceLevelDist[0] = 0
confidenceLevelDist[60] = 0
confidenceLevelDist[80] = 0
confidenceLevelDist[100] = 0

# normalized version of above dictionary
confidenceLevelNorm = {}
confidenceLevelNorm[-100] = 0
confidenceLevelNorm[-80] = 0
confidenceLevelNorm[-60] = 0
confidenceLevelNorm[0] = 0
confidenceLevelNorm[60] = 0
confidenceLevelNorm[80] = 0
confidenceLevelNorm[100] = 0

totalAns = len(restaurantQuestionAnswers)

# Should count the wrong and right answers and put them in a dictionary where 
# key is (restaurant, question) and value is [num wrong answers, num right answers]
for (rest, quest, ans) in restaurantQuestionAnswers:
	 correctAnswer = correctAnswers[(rest,quest)]

	 confidenceLevelDist[ans]+= 1

	 answer = False
	 # ans is the confidence level of the answer because answer is represented at
	 #  0,+-60,80,100
	 if ans > 0:
		answer = True

	 # Putting IDK is also a wrong answer
	 if answer != correctAnswer:
		l = wrongRightCounts[(rest,quest)]
		l[0] += 1
	 else:
		l = wrongRightCounts[(rest,quest)]
		l[1] += 1

# print "--------------"
# print wrongRightCounts

# shows the percent of the time each confidence level is used
confidenceLevelNorm[-100] = float(confidenceLevelDist[-100])/totalAns
confidenceLevelNorm[-80] = float(confidenceLevelDist[-80])/totalAns
confidenceLevelNorm[-60] = float(confidenceLevelDist[-60])/totalAns
confidenceLevelNorm[0] = float(confidenceLevelDist[0])/totalAns
confidenceLevelNorm[60] = float(confidenceLevelDist[60])/totalAns
confidenceLevelNorm[80] = float(confidenceLevelDist[80])/totalAns
confidenceLevelNorm[100] = float(confidenceLevelDist[100])/totalAns

# print "--------------"
# print confidenceLevelNorm

# Calculate the difficulty of each predicate and puts it in a dictionary
diffDic = {}

# initializes the dictionary
for question in uniqueQuestionsList:
	diffDic[question] = [0,0]

# adds in the number of wrong votes and the total number of votes for that question
for (rest, quest, ans) in restaurantQuestionAnswers:
	l = diffDic[quest]
	l[0] += wrongRightCounts[(rest,quest)][0]
	l[1] += 30

# calculates the difficulty
for question in uniqueQuestionsList:
	diffDic[question] = float(diffDic[question][0])/diffDic[question][1]

# print "--------------"
# print diffDic

# array of time each HIT took in case we need data points on time
# or want to more carefully examine the spammer based on time
timeDataPoints = [value2 for (value0, value1, value2, value3, value4, value5) in data]
# print timeDataPoints
# print float(sum(timeDataPoints))/len(timeDataPoints)

fig = plt.figure()

# gets list of unique worker IDs
workerIDs = [value1 for (value0, value1, value2, value3, value4, value5) in data]
uniqueWorkerIDs = set(list(workerIDs))

# initializes dictionary of worker ID keys and values of (number of wrong answers, 
#	total answers submitted)
workerError = {}
workerErrorWhenYes = {}
workerErrorWhenNo = {}

# initializes all three dictionaries
for workerID in uniqueWorkerIDs:
	workerError[workerID] = [0,0]
	workerErrorWhenNo[workerID] = [0,0]
	workerErrorWhenYes[workerID] = [0,0]

workerIDtuples = [(value1, value3, value4, value5) for (value0, value1, value2, 
	value3, value4, value5) in data]

# tabulated the number of times each worker answered a question wrong
for (workerID, rest, quest, ans) in workerIDtuples:
	correctAnswer = correctAnswers[(rest,quest)]

	answer = False
	# ans is the confidence level of the answer because answer is represented at 
	# 0,+-60,80,100
	if ans > 0:
		answer = True

	# Putting IDK is also a wrong answer
	if answer != correctAnswer:
		l = workerError[workerID]
		l[0] += 1

	workerError[workerID][1] += 1

	# calculates worker error when true value is True
	if correctAnswer == True:
		if answer != correctAnswer:
			l = workerErrorWhenYes[workerID]
			l[0] += 1

		workerErrorWhenYes[workerID][1] += 1

	# calculates worker error when true value is False
	else :
		if answer != correctAnswer:
			l = workerErrorWhenNo[workerID]
			l[0] += 1

		workerErrorWhenNo[workerID][1] += 1

# calculate the percent each worker gives the wrong answer
for workerID in uniqueWorkerIDs:

	workerError[workerID] = float(workerError[workerID][0])/workerError[workerID][1]

	if workerErrorWhenNo[workerID][1] == 0:
		workerErrorWhenNo[workerID] = 0
	else:
		workerErrorWhenNo[workerID] = float(workerErrorWhenNo[workerID][0])/workerErrorWhenNo[workerID][1]

	if workerErrorWhenYes[workerID][1] == 0:
		workerErrorWhenYes[workerID] = 0
	else:
		workerErrorWhenYes[workerID] = float(workerErrorWhenYes[workerID][0])/workerErrorWhenYes[workerID][1]

# array of error percentages, not a dictionary
workerErrorArray = []
workerErrorYesArray = []
workerErrorNoArray = []

# puts in worker error to an array
for workerID in uniqueWorkerIDs:
	workerErrorArray.append(workerError[workerID])
	workerErrorYesArray.append(workerErrorWhenYes[workerID])
	workerErrorNoArray.append(workerErrorWhenNo[workerID])

# print "--------------"
# print workerError
# print "--------------"
# print workerErrorWhenYes
# print "--------------"
# print workerErrorWhenNo

# finds probability of answering True when answer is False
predicateError = {}
restQuestionAnswer = [(value3, value4,value5) for (value0, value1, value2, value3, 
	value4, value5) in data]

for (rest, question, answer) in restQuestionAnswer:
	predicateError[(rest, question)] = [0,1]

for (rest, question, ans) in restQuestionAnswer:
	correctAnswer = correctAnswers[(rest,quest)]
	
	answer = False
	# ans is the confidence level of the answer because answer is represented at 
	# 0,+-60,80,100
	if ans > 0:
		answer = True

	if answer != correctAnswer:
		predicateError[(rest,question)][0] += 1

	predicateError[(rest,question)][1] += 1

for key in predicateError:
	predicateError[key] = float(predicateError[key][0])/predicateError[key][1]

# print "--------------"
# print predicateError

# calculates the difference in error percentage from when the true value is True 
# and False
workerErrorDiff = {}
for workerID in uniqueWorkerIDs:
	if workerErrorWhenYes[workerID] == 0 or workerErrorWhenNo[workerID] == 0:
		workerErrorDiff[workerID] = 0
	else:
		workerErrorDiff[workerID] = workerErrorWhenYes[workerID] - workerErrorWhenNo[workerID]

# print "--------------"
# print workerErrorDiff

# print "--------------"
# print len(uniqueWorkerIDs)
# print float(30*200)/len(uniqueWorkerIDs)

# calculates the number of times each worker answered a question
numQuestionsAnswered = {}
for workerID in uniqueWorkerIDs:
	numQuestionsAnswered[workerID] = 0

for (workerID, rest, quest, ans) in workerIDtuples:
	numQuestionsAnswered[workerID] += 1

# print "--------------"
# print numQuestionsAnswered

# dictionary of how many workers have answered X number of questions
numQuestionsDist = {}
numQuestionsDist[10] = 0
numQuestionsDist[30] = 0
numQuestionsDist[50] = 0
numQuestionsDist[100] = 0

# calculates the distribution of questions answered
for workerID in uniqueWorkerIDs:
	if numQuestionsAnswered[workerID] < 10:
		numQuestionsDist[10] += 1
	elif numQuestionsAnswered[workerID] < 30:
		numQuestionsDist[30] += 1
	elif numQuestionsAnswered[workerID] < 50:
		numQuestionsDist[50] += 1
	else: numQuestionsDist[100] += 1

# print "--------------"
# print numQuestionsDist

# plot histogram of confidence levels and yes/no answers submitted by workers 
# for each predicate branch
s0 = []
s1 = []
s2 = []
s3 = []
s4 = []
s5 = []
s6 = []
s7 = []
s8 = []
s9 = []

for (question, answer) in questionAnswerPairs:
	if question == uniqueQuestionsList[0]:
		s0.append(answer)
	elif question == uniqueQuestionsList[1]:
		s1.append(answer)
	elif question == uniqueQuestionsList[2]:
		s2.append(answer)
	elif question == uniqueQuestionsList[3]:
		s3.append(answer)
	elif question == uniqueQuestionsList[4]:
		s4.append(answer)
	elif question == uniqueQuestionsList[5]:
		s5.append(answer)
	elif question == uniqueQuestionsList[6]:
		s6.append(answer)
	elif question == uniqueQuestionsList[7]:
		s7.append(answer)
	elif question == uniqueQuestionsList[8]:
		s8.append(answer)
	elif question == uniqueQuestionsList[9]:
		s9.append(answer)

# now = DT.datetime.now()
# plt.xlabel('Confidence Levels')
# plt.ylabel('Number of Times Submitted')

# plt.hist(s0)
# plt.title('Histogram of Confidence Levels for Difficulty ' + str(diffDic[uniqueQuestionsList[0]]))
# plt.savefig('confidenceLevel_histogram_Question0_' + str(now.date())+ "_" + str(now.time())[:-7] + '.png')

# plt.clf()
# plt.cla()

# plt.hist(s1)
# plt.title('Histogram of Confidence Levels for Difficulty ' + str(diffDic[uniqueQuestionsList[1]]))
# plt.savefig('confidenceLevel_histogram_Question1_' + str(now.date())+ "_" + str(now.time())[:-7] + '.png')

# plt.clf()
# plt.cla()

# plt.hist(s2)
# plt.title('Histogram of Confidence Levels for Difficulty ' + str(diffDic[uniqueQuestionsList[2]]))
# plt.savefig('confidenceLevel_histogram_Question2_' + str(now.date())+ "_" + str(now.time())[:-7] + '.png')

# plt.clf()
# plt.cla()

# plt.hist(s3)
# plt.title('Histogram of Confidence Levels for Difficulty ' + str(diffDic[uniqueQuestionsList[3]]))
# plt.savefig('confidenceLevel_histogram_Question3_' + str(now.date())+ "_" + str(now.time())[:-7] + '.png')

# plt.clf()
# plt.cla()

# plt.hist(s4)
# plt.title('Histogram of Confidence Levels for Difficulty ' + str(diffDic[uniqueQuestionsList[4]]))
# plt.savefig('confidenceLevel_histogram_Question4_' + str(now.date())+ "_" + str(now.time())[:-7] + '.png')

# plt.clf()
# plt.cla()

# plt.hist(s5)
# plt.title('Histogram of Confidence Levels for Difficulty ' + str(diffDic[uniqueQuestionsList[5]]))
# plt.savefig('confidenceLevel_histogram_Question5_' + str(now.date())+ "_" + str(now.time())[:-7] + '.png')

# plt.clf()
# plt.cla()

# plt.hist(s6)
# plt.title('Histogram of Confidence Levels for Difficulty ' + str(diffDic[uniqueQuestionsList[6]]))
# plt.savefig('confidenceLevel_histogram_Question6_' + str(now.date())+ "_" + str(now.time())[:-7] + '.png')

# plt.clf()
# plt.cla()

# plt.hist(s7)
# plt.title('Histogram of Confidence Levels for Difficulty ' + str(diffDic[uniqueQuestionsList[7]]))
# plt.savefig('confidenceLevel_histogram_Question7_' + str(now.date())+ "_" + str(now.time())[:-7] + '.png')

# plt.clf()
# plt.cla()

# plt.hist(s8)
# plt.title('Histogram of Confidence Levels for Difficulty ' + str(diffDic[uniqueQuestionsList[8]]))
# plt.savefig('confidenceLevel_histogram_Question8_' + str(now.date())+ "_" + str(now.time())[:-7] + '.png')

# plt.clf()
# plt.cla()

# plt.hist(s9)
# plt.title('Histogram of Confidence Levels for Difficulty ' + str(diffDic[uniqueQuestionsList[9]]))
# plt.savefig('confidenceLevel_histogram_Question9_' + str(now.date())+ "_" + str(now.time())[:-7] + '.png')

# plt.clf()
# plt.cla()

# initializes dictionary of how many yes answers and number of no answers
dicYesNo = {}
for question in uniqueQuestionsList:
	dicYesNo[question] = [0,0]

# puts in values to the dictionary
for (rest, quest, ans) in restaurantQuestionAnswers:
	if ans > 0:
		dicYesNo[quest][0] += 1
	elif ans < 0:
		dicYesNo[quest][1] += 1

for question in uniqueQuestionsList:
	dicYesNo[question] = 'Ratio of Yes to No Answers: ' + str(float(dicYesNo[question][0])/dicYesNo[question][1]) + ", Difficulty: " + str(diffDic[question])
	# print question + " || " + dicYesNo[question]
