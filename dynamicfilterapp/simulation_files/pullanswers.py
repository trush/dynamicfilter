import numpy as np
OUTPUT_PATH = "hotels/"

def pullOutAnswers (filename):
    """
    A very specific func that pulled "correct" answers about hotels from a csv
    file in a particular format. Could be generalized to pull similar info from
    a different csv file.
    """
    answers = np.genfromtxt(fname = filename, dtype = None, delimiter = ",")

    itemSets = {}

    for line in answers:
        key = line[0]
        if key in itemSets:
            itemSets[key].append(line[4])
        else:
            itemSets[key] = [line[4]]

    f = open(OUTPUT_PATH + "Hotel_correct_answers.csv", "w")

    for key in d:
        f.write(str(key) + ",")
        for i in range(len(itemSets[key])):
            if (i == len(itemSets[key]) - 1):
                f.write(str(itemSets[key][i]))
            else:
                f.write(str(itemSets[key][i]) + ",")
        f.write('\n')

    print "Wrote" + OUTPUT_PATH + "Hotel_correct_answers.csv"
    return itemSets
