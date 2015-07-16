import numpy as np
import matplotlib.pyplot as plt
import datetime as DT
import pylab
import sys

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
								    delimiter=',',
								    usecols=range(6),
								    skip_header=1)

# read in correct answer data
answers = np.genfromtxt(fname=correctAnswersFile, 
									dtype={'formats': [np.dtype('S30'), np.dtype(bool), np.dtype(bool),
									                   np.dtype(bool), np.dtype(bool), np.dtype(bool),
									                   np.dtype(bool), np.dtype(bool), np.dtype(bool),
									                   np.dtype(bool), np.dtype(bool),],
											'names': ['Restaurant', 'a0', 'a1', 'a2', 'a3',
											          'a4', 'a5', 'a6', 'a7',
											          'a8', 'a9']},
								    delimiter=',',
								    usecols=range(11),
								    skip_header=1)

# read in questions (from the first line of the correct answers file)
uniqueQuestions = np.genfromtxt(fname=correctAnswersFile, 
									dtype={'formats': [np.dtype('S100'),np.dtype('S100'),np.dtype('S100'),
									np.dtype('S100'),np.dtype('S100'),np.dtype('S100'),np.dtype('S100'),
									np.dtype('S100'),np.dtype('S100'),np.dtype('S100'),],
											'names': ['a0', 'a1', 'a2', 'a3',
											          'a4', 'a5', 'a6', 'a7',
											          'a8', 'a9']},
								    delimiter=',',
								    usecols=range(1,11),
								    skip_footer=21)

uniqueQuestionsList = list(uniqueQuestions.tolist())

#----------Find Selectivities --------------
# get a list of all 6,000 (question, answer) pairs
questionAnswerPairs = [(value4,value5) for (value0, value1, value2, value3, value4, value5) in data]

# count the number of each answer for each question
answersCount = {}

for question in uniqueQuestionsList:
	countDict = {100:0,80:0,60:0,0:0,-60:0,-80:0,-100:0}
	relevantPairs = filter(lambda t:t[0]==question, questionAnswerPairs)
	for pair in relevantPairs:
		countDict[pair[1]] += 1
	answersCount[question] = countDict

# compute selectivities using answer counts
for entry in answersCount:
	print entry
	countDict = answersCount[entry]
	
	selectivity = (countDict[-100]+countDict[-80]+countDict[-60])/600.0
	print "Selectivity: " + str(selectivity)
#--------------------------------------------

# create a dictionary of (restaurant, question) keys and boolean correct answer values
correctAnswers = {}
print len(uniqueQuestionsList)
wrongRightCounts = {}
for restRow in answers:
	r = list(restRow)
	for i in range(10):

		key = (r[0], uniqueQuestionsList[i])
		value = r[i+1]
		correctAnswers[key] = value
		wrongRightCounts[key] = [0,0]


restaurantQuestionAnswers = [(value3, value4,value5) for (value0, value1, value2, value3, value4, value5) in data]

# NOT WORKING :(
# Should count the wrong and right answers and put them in a dictionary where key is (restaurant, question) and value is [num wrong answers, num right answers]
for (rest, quest, ans) in restaurantQuestionAnswers:
	 correctAnswer = correctAnswers[(rest,quest)]
	 if ans != correctAnswers:
	 	l = wrongRightCounts[(rest,quest)]
	 	l[0] += 1
	 else:
	 	l = wrongRightCounts[(rest,quest)]
	 	l[1] += 1

print "--------------"
print wrongRightCounts

# s0 = [value0 for (value0, value1, value2, value3, value4, value5) in data]
# s1 = [value1 for (value0, value1, value2, value3, value4, value5) in data]
# s2 = [value2 for (value0, value1, value2, value3, value4, value5) in data]
# s3 = [value3 for (value0, value1, value2, value3, value4, value5) in data]
# s4 = [value4 for (value0, value1, value2, value3, value4, value5) in data]
# s5 = [value5 for (value0, value1, value2, value3, value4, value5) in data]

# print questionAnswerPairs