import csv
import string
import matplotlib.pyplot as plt
import numpy
from scipy import stats

all_seconds = {}

## takes a string of entries (separated by the string {{NEWENTRY}}) for find_pairs and parses them
def parse_pairs(pairs):
    if pairs is None or pairs is "" or pairs == 'None':
        return []
    else:
        processed = []
        for match in pairs.strip("{{NEWENTRY}}").split("{{NEWENTRY}}"):
            temp = match.strip()
            temp = temp.lower()
            processed.append(temp)
        return processed

## turns string responses into unique identifying strings
#NOTE: this function is specific to our example (hotels and restaurants)
# new functions must be written for different queries
def disambiguate_str(sec_item_str):
    #we want the (numeric) non-whitespace characters after the semicolon
    semicol_pos = sec_item_str.rfind(';')
    if ';' not in sec_item_str:
        if sec_item_str != '' and sec_item_str[0].isdigit():
            semicol_pos = -1
        elif ',' in sec_item_str:
            semicol_pos = sec_item_str.find(',')
    addr = sec_item_str[semicol_pos+1:].strip()
    for i in range(len(addr)):
        if addr[i].isspace():
            addr = addr[:i]
            break
    if addr == "1":
        if "barnes" in sec_item_str:
            addr = "1b"
    if addr == "" or (not addr[0].isdigit()):
        addr = ""
    else:
        if addr not in all_seconds:
            all_seconds[addr] = sec_item_str
    return addr

hit_csv = csv.reader(open('FP_RESULTS.csv', 'r'), delimiter = ',') 
# # results csv
cleaned_hits = csv.writer(open('CLEANED_ROUND2.csv', 'w'), delimiter = ',')

header = next(hit_csv)
print header
UNPARSEABLE_NONE = []
UNPARSEABLE_GBG = []

time = 0.0
num_assignments = 0
num_empty = 0
curr_hit = ''
num_assign_this_hit = 0
num_empty_this_hit = 0
num_hits_mostly_empty = 0
matches_dict = {}
cant_parse = []
time_to_num = {}
ans_to_num = {}
times_total = []
num_ans_each = []

for assignment in hit_csv:
    #trash assignments with: MyHospital, MyMedics in name, unparseables
    #turn urls and other unparseable non-answers into Nones
    #leave the rest

    if assignment[1+4] in UNPARSEABLE_GBG:
        continue

    answer = assignment[1+7]
    if assignment[1+4] in UNPARSEABLE_NONE:
        answer = 'None'
    if 'MyHospital' in answer or 'MyMedics' in answer :
        continue
    if 'https://' in answer:
        answer = 'None' 

    ans_list = parse_pairs(answer)
    cleaned_ans_list = filter(lambda x: x != "", map(disambiguate_str, ans_list))

    if cleaned_ans_list == [] and answer != 'None':
        cant_parse.append((assignment[0],assignment[1+4],filter(lambda x: x != "",ans_list)))
        continue

    if len(cleaned_ans_list) in time_to_num:
        time_to_num[len(cleaned_ans_list)] += float(assignment[1+6])
        ans_to_num[len(cleaned_ans_list)] += 1
    else:
        time_to_num[len(cleaned_ans_list)] = float(assignment[1+6])
        ans_to_num[len(cleaned_ans_list)] = 1
    times_total += [float(assignment[1+6])]
    num_ans_each += [len(cleaned_ans_list)]

    if answer == 'None':
        num_empty += 1.0
        num_empty_this_hit += 1.0

    time += float(assignment[1+6])
    num_assignments += 1

    if assignment[1+1] != curr_hit:
        if num_empty_this_hit > 4:
            num_hits_mostly_empty += 1.0
        num_empty_this_hit = 0
        curr_hit = assignment[1+1]
        matches_dict[curr_hit] = {}

    for ans in cleaned_ans_list:
        curr_hit_match_dict = matches_dict[curr_hit]
        if ans in curr_hit_match_dict:
            curr_hit_match_dict[ans] += 1
        else:
            curr_hit_match_dict[ans] = 1


    num_assign_this_hit += 1
    cleaned_hits.writerow([assignment[0],assignment[1],assignment[2],assignment[3],assignment[4],assignment[5],assignment[6],assignment[7],answer,assignment[9]])

sec_item_votes = {}
sec_item_csv = csv.writer(open('HOSPITAL_ROUGH.csv', 'w'), delimiter = ',')
interest_sec_items = []

if num_assignments > 0:
    print "I can't parse these",len(cant_parse),"assignments:"
    for entry in cant_parse:
        print "\tHIT",entry[0],"\tAssignment",entry[1]

    for hit in matches_dict:
        print "hotel", hit
        for ans in matches_dict[hit]:
            print "\t addr:",ans,"\tvotes yes:",matches_dict[hit][ans]
            if ans not in sec_item_votes:
                sec_item_votes[ans] = 0
            sec_item_votes[ans] +=matches_dict[hit][ans]
    
    print "there are",len(all_seconds),"addresses"
    for addr in all_seconds:
        if sec_item_votes[addr] > 15:
            print "******************************"
        print "address:",addr,"votes:",sec_item_votes[addr],"\tfull name:", all_seconds[addr]
        if sec_item_votes[addr] > 1:
            sec_item_csv.writerow([addr,sec_item_votes[addr],all_seconds[addr]])
        if sec_item_votes[addr] > 15:
            print "******************************"
    
    # for item in interest_sec_items:
    #     sec_item_csv.writerow([item,sec_item_votes[item],all_seconds[item]])

    print "avg time:",str(time/num_assignments)
    print "proportion empty:", str(num_empty/num_assignments)
    print "num mostly empty hits:", num_hits_mostly_empty
    avg_tim_list = []
    num_ans_list = []
    for num_responses in ans_to_num:
        print "avg time:", time_to_num[num_responses]/ans_to_num[num_responses], "\tfor", num_responses,"responses"
        print num_responses,"ocurred", ans_to_num[num_responses],"times"
        avg_tim_list += [time_to_num[num_responses]/ans_to_num[num_responses]]
        num_ans_list += [num_responses]
    
    for i in range(1,3):
        fit = numpy.polyfit(num_ans_each,times_total,i, full=True)
        print "degree", i,"residuals", fit[1][0]
        print fit
        fit_fn = numpy.poly1d(fit[0])

        plt.plot(num_ans_each,times_total,'ro', num_ans_list, fit_fn(num_ans_list), '--k')
        plt.axis([0,17,0,1500])
        plt.show()

    
    # for i in range(1,3):
    #     fit = numpy.polyfit(num_ans_list,avg_tim_list,i, full=True)
    #     print "degree", i,"residuals", fit[1][0]
    #     print fit
    #     fit_fn = numpy.poly1d(fit[0])

    #     plt.plot(num_ans_list,avg_tim_list,'ro', num_ans_list, fit_fn(num_ans_list), '--k')
    #     plt.axis([0,17,0,1500])
    #     plt.show()
