# run with python plotScript_alg_hist.py <filename>
# or autorun with tests in test_simulations
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pylab
import sys
from plotScript import hist_gen

def main():
	filename = sys.argv[1]
	data = list(np.loadtxt(filename, delimiter=','))
	dest=filename[:-4]
	hist_gen(data, dest + '_task_count.png', labels=('Number of Tasks', 'Frequency'), title='Distribution of Cost Normalized')

if __name__ == "__main__":
    main()
