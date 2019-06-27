## Draft space for us to figure out how we will simulate fake data to run later

	def get_sample_answer_dict(self, filename):
		# read in worker data from cleaned file
		data = np.genfromtxt(fname=filename,
							dtype={'formats': [np.dtype(int), np.dtype('S100'),
										np.dtype('S200'), np.dtype(int)],
									'names': ['WorkTimeInSeconds', 'Input.Hotel',
										'Input.Question', 'Answer.Q1AnswerPart1']},
							delimiter=',',
							usecols=range(4),
							skip_header=1)

		# Get a list of all the tasks in the file, represented as tuples of
		# (item, question, answer)
		tasks = [(item, question, answer) for (workTimeInSeconds, item, question, answer) in data]

		# create the dictionary and populate it with empty lists
		sampleData = {}
		for p in IP_Pair.objects.all():
			sampleData[p] = []

		# Add every task's answer into the appropriate list in the dictionary
		for (item, question, answer) in tasks:

			# answer==0 means worker answered "I don't know"
			if answer != 0:

				# get the RestaurantPredicates matching this task (will be a
				# QuerySet of length 1 or 0)
				predKey = IP_Pair.objects.filter(predicate__question__question_text=question).filter(item__name=item)

				# Some tasks won't have matching RestaurantPredicates, since we
				# may not be using all the possible predicates
				if predKey.count() > 0:
					if answer > 0:
						sampleData[predKey[0]].append(True)
					elif answer < 0:
						sampleData[predKey[0]].append(False)

		return sampleData



	def get_correct_answers(self, filename):
		#read in answer data
		raw = generic_csv_read(filename)
		data = []
		for row in raw:
			l=[row[0]]
			for val in row[1:]:
				if val == "FALSE" or val == "False":
					l.append(False)
				elif val == "TRUE" or val == "True":
					l.append(True)
				else:
					raise ValueError("Error in correctAnswers csv file")
			data.append(l)
		answers = data
		# create an empty dictionary that we'll populate with (item, predicate) keys
		# and boolean correct answer values
		correctAnswers = {}

		for line in answers:
			for i in range(len(line)-1):
				key = (Item.objects.get(name = line[0]),
					Predicate.objects.get(pk = i+1))
				value = line[i+1]
				correctAnswers[key] = value

		return correctAnswers