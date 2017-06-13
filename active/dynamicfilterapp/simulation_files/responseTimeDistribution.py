from plotScript import *
import numpy as np
import csv
import scipy


def importResponseTimes (filename):
    answers = np.genfromtxt(fname = filename, dtype = int, delimiter = ",")

    trueResponseTimes = []
    falseResponseTimes = []

    for line in answers:
        if (line[3] > 0):
            trueResponseTimes.append(line[0])
        if (line[3] < 0):
            falseResponseTimes.append(line[0])
    return trueResponseTimes, falseResponseTimes

hotels = importResponseTimes("dynamicfilterapp/simulation_files/hotels/hotel_cleaned_data.csv")
restaurants = importResponseTimes("dynamicfilterapp/simulation_files/restaurants/real_data1.csv")

multi_hist_gen([hotels[0], restaurants[0]], ["Hotels", "Restaurants"], "dynamicfilterapp/simulation_files/TrueDistributions.png",
                labels = ("", "Response Times"), title = "True Response Times Distributed")

multi_hist_gen([hotels[1], restaurants[1]], ["Hotels", "Restaurants"], "dynamicfilterapp/simulation_files/FalseDistributions.png",
                labels = ("", "Response Times"), title = "False Response Times Distributed")

trueU, trueP = scipy.stats.mannwhitneyu(hotels[0], restaurants[0])
falseU, falseP = scipy.stats.mannwhitneyu(hotels[1], restaurants[1])
