# run with python plotScript_alg_hist.py <filename>
# or autorun with tests in test_simulations
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pylab
import sys

def alg_count_gen(filename, dest):
	data = list(np.loadtxt(filename, delimiter=','))

	sns.set(style="white", palette="muted", color_codes=True)

	fig = plt.figure()
	ax = fig.add_subplot(111)
	sns.despine(left=True)

	# the histogram of the data
	sns.distplot(data, hist=False, kde_kws={"shade": False}, ax=ax)

	ax.set_xlabel('Number of Tasks')
	ax.set_ylabel('Frequency')
	ax.set_title('Distribution of Cost Normalized')
	#ax.set_xlim(100, 320)
	ax.grid(True)

	#plt.tight_layout()
	#plt.show()
	plt.savefig(dest + '_task_count.png')


def main():
	filename = sys.argv[1]
	alg_count_gen(filename, filename[:-4])

if __name__ == "__main__":
    main()
