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

hit_csv = csv.reader(open('HIT_RESULTS_ROUND1.csv', 'r'), delimiter = ',') 
# # results csv
# cleaned_hits = csv.writer(open('CLEANED_ROUND1_trial.csv', 'w'), delimiter = ',')

header = next(hit_csv)
print header
UNPARSEABLE_NONE = ['3OONKJ5DKCJV2P7LB7O55YPEGRPBO3','3YDTZAI2WXGQLYFBQQG7LO60DNO41R','3U088ZLJVKT2NBDD4DIQ2B6HSPLW08',]
UNPARSEABLE_GBG = ['3P59JYT76LKHR4CXOVHTYFSXLSM2T5', '39U1BHVTDLR6CM8GSVVYHPXPR6MT37','3N8OEVH1FRQFLJWUFCTRBIPDNQAOOM','3K772S5NP8BJHBXIHLV5MXYY71EHE9','3ZSANO2JCF70DYBUNQRA8TQ0SDDFSD',
    '3TPWUS5F891MH38TGTBAXC8I1DDWCU','3H8DHMCCW9B5RVKQRBNIT7W5Z6KDKJ','36WLNQG78ZA9QYUWHTL90MV0COCBEQ','35GCEFQ6I5O2YYHFYNKG3DY6C3H3Z8','3180JW2OT4CFCYZFUK5NUG8070M5J4','31LM9EDVOLSJ2N5LYK19OX8MYMNNJF',
    '3Z4GS9HPNVA1F7CWH4VNPAHN7CP77O','3WAKVUDHUWG3DIOSUCOYZ2V7FMF7UH','3NPFYT4IZC4ENFTOSK3FPM7487EXG1','3I0BTBYZAXL6CG8DJE0EN8RX3XOY0C','326O153BMIY25VSGVPCFVCJ0F9OED0','3QILPRALQ5VUI6927G4IZ7Z8IASN8S',
    '3LYA37P8IQNCCYM6DFWCYH85WL8KBJ','35K3O9HUABDZ3F6CMV75JCMLRNBFEL','32SCWG5HIH47HD2RUGKCJI8CCU3P64','3IFS6Q0HJIJKNPDKOYXVBQ3S855IS7','34QN5IT0TZRRXAHV6A2KOV3VAHH802','3I7DHKZYGN0Z7WDJBUE2FIG8ET55F1',
    '3YMTUJH0DSGRUIRKS90HRUPV57P4TC','336KAV9KYQSD8QBRY14S6WKC0U42YU','3WQQ9FUS6AUSHXK54QZ98CZE1LEB8R','3ZOTGHDK5IBUJBONMTA0VNZEKFAOSG','3NVC2EB65QZ2T87A21IXP6P4684Y31','3NJM2BJS4W6WXUBS47XF5I0M8GEPCW']

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

    if assignment[4] in UNPARSEABLE_GBG:
        continue

    answer = assignment[7]
    if assignment[4] in UNPARSEABLE_NONE:
        answer = 'None'
    if 'MyHospital' in answer or 'MyMedics' in answer :
        continue
    if 'https://' in answer:
        answer = 'None' 

    ans_list = parse_pairs(answer)
    cleaned_ans_list = filter(lambda x: x != "", map(disambiguate_str, ans_list))

    if cleaned_ans_list == [] and answer != 'None':
        cant_parse.append((assignment[0],assignment[4],filter(lambda x: x != "",ans_list)))
        continue

    if len(cleaned_ans_list) in time_to_num:
        time_to_num[len(cleaned_ans_list)] += float(assignment[6])
        ans_to_num[len(cleaned_ans_list)] += 1
    else:
        time_to_num[len(cleaned_ans_list)] = float(assignment[6])
        ans_to_num[len(cleaned_ans_list)] = 1
    times_total += [float(assignment[6])]
    num_ans_each += [len(cleaned_ans_list)]

    if answer == 'None':
        num_empty += 1.0
        num_empty_this_hit += 1.0

    time += float(assignment[6])
    num_assignments += 1

    if assignment[1] != curr_hit:
        if num_empty_this_hit > 4:
            num_hits_mostly_empty += 1.0
        num_empty_this_hit = 0
        curr_hit = assignment[1]
        matches_dict[curr_hit] = {}

    for ans in cleaned_ans_list:
        curr_hit_match_dict = matches_dict[curr_hit]
        if ans in curr_hit_match_dict:
            curr_hit_match_dict[ans] += 1
        else:
            curr_hit_match_dict[ans] = 1


    num_assign_this_hit += 1
    # cleaned_hits.writerow([assignment[0],assignment[1],assignment[2],assignment[3],assignment[4],assignment[5],assignment[6],answer,assignment[8]])

sec_item_votes = {}
sec_item_csv = csv.writer(open('HOSPITAL_ROUGH.csv', 'w'), delimiter = ',')
interest_sec_items = ['1b','660','3933','3844','12303','11365','915','6420','1438','515','4930','4921','4353','10296','1027','2727','1','4455','4400','1127']

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

    
    for i in range(1,3):
        fit = numpy.polyfit(num_ans_list,avg_tim_list,i, full=True)
        print "degree", i,"residuals", fit[1][0]
        print fit
        fit_fn = numpy.poly1d(fit[0])

        plt.plot(num_ans_list,avg_tim_list,'ro', num_ans_list, fit_fn(num_ans_list), '--k')
        plt.axis([0,17,0,1500])
        plt.show()
