###NOTES: install boto3 and xmltodict through pip before using. Replace pubkey and privkey with real keys. Replace hitId with a real hitId
import keys
pubkey = keys.pubkey
privkey = keys.privkey

import boto3
import string
import datetime
import xmltodict
import csv
MTURK_SANDBOX = 'https://mturk-requester-sandbox.us-east-1.amazonaws.com'

mturk = boto3.client('mturk',
  aws_access_key_id = pubkey,
  aws_secret_access_key = privkey,
  region_name='us-east-1'
  #endpoint_url = MTURK_SANDBOX
)
print "I have $" + mturk.get_account_balance()['AvailableBalance'] + " in my account"
#csv that holds recorded hits
my_csv = csv.reader(open('HIT_IDs.csv', 'r'), delimiter = ',') #read from SANDBOX_HIT_IDs for sandbox data

# results csv
results = csv.writer(open('HIT_RESULTS.csv', 'w'), delimiter = ',')

# header row for results csv
first_row = ["Hit Id", "Worker Id", "Hotel", "Hospital", "Task", "Assignment Id", "Assignment Status", "Time Taken", "workervote","supplementary", "feedback"]
results.writerow(first_row)

#finds set of printable characters for string processing later
printable = set(string.printable)

for row in my_csv:
    print row
    [hit_id, hotel, task, hospital] = row
    # We are only publishing this task to one Worker
    # So we will get back an array with one item if it has been completed
    worker_results = mturk.list_assignments_for_hit(HITId=hit_id)

    if worker_results['NumResults'] > 0:
        for assignment in worker_results['Assignments']:
            # The list of response fields from the HIT's form
            answers_list =  xmltodict.parse(assignment['Answer'])['QuestionFormAnswers']['Answer']
            if answers_list[0]['QuestionIdentifier'] != 'consent':
                print "***"
                print "warning: consent not first for HIT ", hit_id
                print "hotel: ", hotel, " task: ", task, "assignment"
                print "***"
            elif answers_list[0]['FreeText'] != 'on':
                raise Exception("consent not granted for assignment", assignment['AssignmentId'])
            else:
                print "consent",answers_list[0]['FreeText']
            # Metadata from assignment, formatted for csv
            newRow = [assignment["HITId"], assignment["WorkerId"], "(" + hotel + ")"," (" + hospital + ")", "(" + task + ")",assignment["AssignmentId"], \
                assignment["AssignmentStatus"],str((assignment["SubmitTime"] - assignment["AcceptTime"]).total_seconds())]

            #Nicer answers data structure  
            answers_dict = {}
            for answer_field in answers_list:
                question = answer_field['QuestionIdentifier']
                worker_response = answer_field['FreeText']
                #clean unprintable characters
                if worker_response is not None:
                    answers_dict[question] = filter(lambda x: x in printable, worker_response)
                    #if workervote contains u"/r", replace with special substring
                    answers_dict[question] = answers_dict[question].replace("\r","{{NEWENTRY}}")
                else:
                    answers_dict[question] = None

            #replaces marked blank responses w/ "None"
            if u'markedblank' in answers_dict and answers_dict['markedblank'] == 'on':
                newRow += ['None']
            else:
                newRow += [str(answers_dict['workervote'])]

            #Adds supplementary field if present
            if 'supplementary' in answers_dict:
                if answers_dict['supplementary'] == "":
                    raise Exception ("A worker left a required field blank")
                else:
                    newRow += [str(answers_dict['supplementary'])]
            else:
                newRow += ["None"]

            #Adds feedback
            newRow += [str(answers_dict['feedback'])]

            print newRow

            results.writerow(newRow)
    else:
        print "No results ready for HIT " + hit_id


print mturk.list_reviewable_hits()