# run with python plotScript_alg_hist.py 0first_hotel_0_1.csv 1first_hotel_1_3.csv queue_eddy_hotel_0_1.csv random_hotel_0_1.csv ;open graphs/andys_dist_of_varied_selectivities_normalized.png 

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pylab
import sys

num_tasks_array = []
for i in range(1,5):
	num_tasks_array.append(list(np.loadtxt(sys.argv[i], delimiter=',')))
	print "appending " + sys.argv[i]

sns.set(style="white", palette="muted", color_codes=False)

fig = plt.figure()
ax = fig.add_subplot(111)
sns.despine(left=True)

# the histogram of the data
alg_list = ["'Gym?' first", "Under $80?' first", "dynamic filter", "random"]
linestyles=["-","-","-","-"]
markers=["^","o","v","s"]
for i in range(len(num_tasks_array)):
	sns.distplot(num_tasks_array[i], hist=False, kde_kws={"shade": False, "lw":1, "ls": linestyles[i], "marker": markers[i], "markersize":7, "markevery":4}, ax=ax, label=alg_list[i])

ax.set_xlabel('Number of Tasks')
ax.set_ylabel('Frequency')
ax.set_title('Distribution of Varied Selectivities Normalized')
#ax.set_xlim(100, 320)
ax.grid(True)

#plt.tight_layout()
#plt.show()
plt.savefig('graphs/andys_dist_of_varied_selectivities_normalized.png')
