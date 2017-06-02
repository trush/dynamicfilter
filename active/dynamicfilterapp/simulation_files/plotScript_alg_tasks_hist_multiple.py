# run with python plotScript_alg_hist.py <filenames>

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pylab
import sys
from plotScript import multi_hist_gen

#multi_hist_gen(dataList, legendList, dest, labels, title):

def main():
	num_tasks_array = []
	for i in range(1,len(sys.argv)):
		num_tasks_array.append(list(np.loadtxt(sys.argv[i], delimiter=',')))
	alg_list = ["first", "second", "third","4","5","6"]
	lbls = ('Number of Tasks', 'Frequency')
	title = 'Distribution of Synthesized Cost Switch Normalized'
	multi_hist_gen(num_tasks_array, alg_list, "TESTINGNAME.png", labels=lbls, title=title)

if __name__ == "__main__":
    main()
