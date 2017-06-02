# run with python plotScript_alg_hist.py <filenames>

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pylab
import sys

num_tasks_array = []
for i in range(1,6):
	num_tasks_array.append(list(np.loadtxt(sys.argv[i], delimiter=',')))

sns.set(style="white", palette="muted", color_codes=True)

fig = plt.figure()
ax = fig.add_subplot(111)
sns.despine(left=True)

# the histogram of the data
alg_list = ["optimal switch", "worst switch", "sliding window", "ticketing queue", "random"]
for i in range(len(num_tasks_array)):
	sns.distplot(num_tasks_array[i], hist=False, kde_kws={"shade": False}, ax=ax, label=alg_list[i])

ax.set_xlabel('Number of Tasks')
ax.set_ylabel('Frequency')
ax.set_title('Distribution of Synthesized Cost Switch Normalized')
#ax.set_xlim(100, 320)
ax.grid(True)

#plt.tight_layout()
#plt.show()
plt.savefig('graphs/synthesized_cost_switch_normed.png')