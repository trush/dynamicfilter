import csv
import string

hit_csv = csv.reader(open('HIT_RESULTS.csv', 'r'), delimiter = ',') 

find_pairs_csv = csv.writer(open('HIT_RESULTS_FIND_PAIRS.csv', 'w'), delimiter = ',')

for assignment in hit_csv:
    if assignment[4] == "( list_secondary)":
        find_pairs_csv.writerow(assignment)
