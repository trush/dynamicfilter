# run with python plotScript_alg_hist.py <filenames>

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pylab
import sys
from plotScript import multi_bar_graph_gen

#multi_hist_gen(dataList, legendList, dest, labels, title):

def main():
    num_tasks_array = []
    alg_list = []
    for i in range(1,len(sys.argv)):
        num_tasks_array.append(list(np.loadtxt(sys.argv[i], delimiter=',')))
        alg_list.append(str(sys.argv[i]))
    lbls = ('Number of Tasks', 'Frequency')
    title = 'Comparitive Task Counts'
    multi_bar_graph_gen(num_tasks_array, alg_list, 'comparitive_task_count_bar.png', labels = lbls, title = title)

if __name__ == "__main__":
    main()
