# Code adapted from tutorial at http://www.bogotobogo.com/python/python_matplotlib.php

import numpy as np
import matplotlib.pyplot as plt
import datetime as DT
import pylab
import sys

filename = sys.argv[1]
now = DT.datetime.now()
data = np.loadtxt(filename, skiprows=2, delimiter=',', dtype={'names': ('eddy num tasks', 'eddy correct percent', 
	'eddy 2 num tasks', 'eddy 2 correct percentage', 'random num tasks', 'random correct percent'),
          'formats': (np.int, np.float, np.int, np.float, np.int, np.float)})

s0 = [value0 for (value0, value1, value2, value3, value4, value5) in data]
s1 = [value1 for (value0, value1, value2, value3, value4, value5) in data]
s2 = [value2 for (value0, value1, value2, value3, value4, value5) in data]
s3 = [value3 for (value0, value1, value2, value3, value4, value5) in data]
s4 = [value4 for (value0, value1, value2, value3, value4, value5) in data]
s5 = [value5 for (value0, value1, value2, value3, value4, value5) in data]


print "Eddy average: " + str(np.average(s0))
print "Eddy2 average: " + str(np.average(s2))
print "Random average: " + str(np.average(s4))

fig = plt.figure()

# add grid lines
ax = fig.add_subplot(111)
ax.grid()

plt.hist(s0)

plt.xlabel('Tasks Completed')
plt.ylabel('Number of Runs')
plt.title('Tasks to Complete all Questions (Eddy)')
plt.savefig('test_results/eddy_histogram' + str(now.date())+ "_" + str(now.time())[:-7] + '.png')

plt.clf()
plt.cla()
#-----------------------
fig = plt.figure()

# add grid lines
ax = fig.add_subplot(111)
ax.grid()

plt.hist(s2)

plt.xlabel('Tasks Completed')
plt.ylabel('Number of Runs')
plt.title('Tasks to Complete all Questions (Eddy 2)')
plt.savefig('test_results/eddy2_histogram' + str(now.date())+ "_" + str(now.time())[:-7] + '.png')

plt.clf()
plt.cla()
#-----------------------
fig = plt.figure()

# add grid lines
ax = fig.add_subplot(111)
ax.grid()

plt.hist(s4)

plt.xlabel('Tasks Completed')
plt.ylabel('Number of Runs')
plt.title('Tasks to Complete all Questions (Random)')
plt.savefig('test_results/random_histogram' + str(now.date())+ "_" + str(now.time())[:-7] + '.png')

# #-----------------------
# plt.clf()
# plt.cla()

# fig = plt.figure()

# # add grid lines
# ax = fig.add_subplot(111)
# ax.grid()

# plt.hist(s1, bins=10)

# plt.xlabel('Correct percentage')
# plt.ylabel('Number of Runs')
# plt.title('Correct percentage (Eddy)')
# plt.savefig('test_results/eddy_correct_histogram' + str(now.date())+ "_" + str(now.time())[:-7] + '.png')

# #-----------------------
# plt.clf()
# plt.cla()

# fig = plt.figure()

# # add grid lines
# ax = fig.add_subplot(111)
# ax.grid()

# plt.hist(s3, bins=10)

# plt.xlabel('Correct percentage')
# plt.ylabel('Number of Runs')
# plt.title('Correct percentage (Random)')
# plt.savefig('test_results/random_correct_histogram' + str(now.date())+ "_" + str(now.time())[:-7] + '.png')



