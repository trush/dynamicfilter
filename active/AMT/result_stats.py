import csv
import string

results = csv.reader(open('SP_RESULTS.csv', 'r'), delimiter = ',')


num_results = {'p1':0.0, 'p2':0.0}
selectivity = {'p1':[], 'p2':[]}
time = {'p1':0.0, 'p2':0.0}

curr_hosp = ''
yes_votes_p1 = 0.0
no_votes_p1 = 0.0
failed_p1 = 0.0
# yes_votes_p2 = 0.0
# failed_p2 = 0.0
votes_dict = {}
worker_dict = {}


cleaned = csv.writer(open('SP_CLEAN.csv', 'w'), delimiter = ',')


header = True
for row in results:
    if header:
        header = False
        cleaned.writerow(row[:1] + row[2:])
        continue
    
    # if float(row[6]) < 300.0:
    #     continue

    if row[3] != curr_hosp:
        if curr_hosp is not '':
            votes_dict[curr_hosp] = (yes_votes_p1, no_votes_p1)
            if yes_votes_p1 < no_votes_p1:
                failed_p1 += 1
                print curr_hosp, "failed p1"
            # if yes_votes_p2 < 5:
            #     failed_p2 += 1    
            #     print curr_hosp, "failed p2"    
        curr_hosp = row[3]
        yes_votes_p1 = 0.0
        no_votes_p1 = 0.0
        # yes_votes_p2 = 0.0



    # if '1' in row[3]:
    worker = row[1]
    if worker not in worker_dict:
        worker_dict[worker] = []
    answer = row[8].strip()
    if not answer[0].isdigit():
        worker_dict[worker] += ['inadmissible '+str(answer)]
    else:
        if "3-4" in answer:
            answer = "4"
        cleaned_answer = str(filter(lambda x: x.isdigit(), answer).strip())
        if cleaned_answer is "":
            worker_dict[worker] += ['inadmissible ' + str(answer)]
        else:
            worker_dict[worker] += [cleaned_answer]
            cleaned.writerow(row[:1] + row[2:8] + [cleaned_answer] + row[9:])
            num_results['p1'] += 1
        int_ans = int(cleaned_answer)
        if int_ans > 4:
            yes_votes_p1 += 1
            selectivity['p1'] += [1]
            time['p1'] += float(row[7])
        else:
            no_votes_p1 += 1
            selectivity['p1'] += [0]
            time['p1'] += float(row[7])
    

for worker in worker_dict:
    print "worker", worker, worker_dict[worker]
print "number of results (p1): ", num_results['p1']
# print "number of results (p2): ", num_results['p2']
print "average time (p1): ", time['p1']/num_results['p1']
# print "average time (p2): ", time['p2']/num_results['p2']
print "selectivity of assignments (p1): ", sum(selectivity['p1'])/num_results['p1']
# print "selectivity of assignments (p2): ", sum(selectivity['p2'])/num_results['p2']
print "selectivity of items (p1): ", 1- failed_p1/20
# print "selectivity of items (p2): ", 1- failed_p2/20

for item in votes_dict:
    print "votes:",votes_dict[item],"\titem:",item
