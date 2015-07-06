from scipy.special import btdtr

class CostEstimate():

	def estimate_cost(self, d, t, c, i):
		difficulty = d
		threshold = t

		loggedCorrect = c
		loggedIncorrect = i

		tasksLeft = 0
		done = False
		while (not done):
			expectedCorrect = tasksLeft*(1.0-difficulty)
			expectedIncorrect = tasksLeft - expectedCorrect
			if btdtr(loggedCorrect+expectedCorrect+1, loggedIncorrect+expectedIncorrect+1, 0.5) < threshold:
				print expectedCorrect
				print expectedIncorrect
				done = True
			else:
				tasksLeft += 1
		return tasksLeft