import csv
import string


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
    if addr == "" or (not addr[0].isdigit()):
        addr = ""
    return addr

hit_csv = csv.reader(open('HIT_RESULTS.csv', 'r'), delimiter = ',') 

header = next(hit_csv)
print header

time = 0.0
num_assignments = 0
num_empty = 0
curr_hit = ''
num_assign_this_hit = 0
num_empty_this_hit = 0
num_hits_mostly_empty = 0
matches_dict = {}
cant_parse = []

for assignment in hit_csv:
    #trash assignments with: MyHospital, MyMedics in name, unparseables
    #turn urls and other unparseable non-answers into Nones
    #leave the rest

    time += float(assignment[6])
    num_assignments += 1

    if assignment[0] != curr_hit:
        if num_empty_this_hit > 4:
            num_hits_mostly_empty += 1.0
        num_empty_this_hit = 0
        curr_hit = assignment[0]
        matches_dict[curr_hit] = {}

    answer = assignment[7]
    if 'MyHospital' in answer or 'MyMedics' in answer or 'https://' in answer:
        answer = 'None' 

    if answer == 'None':
        num_empty += 1.0
        num_empty_this_hit += 1.0

    ans_list = parse_pairs(answer)
    cleaned_ans_list = filter(lambda x: x != "", map(disambiguate_str, ans_list))

    if cleaned_ans_list == [] and answer != 'None':
        cant_parse.append((assignment[0],assignment[4],filter(lambda x: x != "",ans_list)))

    for ans in cleaned_ans_list:
        curr_hit_match_dict = matches_dict[curr_hit]
        if ans in curr_hit_match_dict:
            curr_hit_match_dict[ans] += 1
        else:
            curr_hit_match_dict[ans] = 1


    num_assign_this_hit += 1

if num_assignments > 0:
    print "avg time:",str(time/num_assignments)
    print "proportion empty:", str(num_empty/num_assignments)
    print "num mostly empty hits:", num_hits_mostly_empty

    for hit in matches_dict:
        print "hit", hit
        for ans in matches_dict[hit]:
            print "\t addr:",ans,"\tvotes yes:",matches_dict[hit][ans]

    print "I can't parse these",len(cant_parse),"assignments:"
    for entry in cant_parse:
        print "\tHIT",entry[0],"\tAssignment",entry[1]
