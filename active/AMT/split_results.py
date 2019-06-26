import csv
import string

all_results = csv.reader(open('HIT_RESULTS.csv', 'r'), delimiter = ',')

fp_results = csv.writer(open('FP_RESULTS.csv', 'w'), delimiter = ',')
sp_results = csv.writer(open('SP_RESULTS.csv', 'w'), delimiter = ',')


header = True
for row in all_results:
    if header:
        fp_results.writerow(row)
        sp_results.writerow(row)
        header = False
        continue
    
    if 'eval' in row[4]:
        sp_results.writerow(row)
    else:
        fp_results.writerow(row)
