###NOTES: install boto3 and xmltodict through pip before using. Replace pubkey and privkey with real keys. Replace hitId with a real hitId
import keys
pubkey = keys.pubkey
privkey = keys.privkey

import boto3
import string
import datetime
import xmltodict
MTURK_SANDBOX = 'https://mturk-requester-sandbox.us-east-1.amazonaws.com'

mturk = boto3.client('mturk',
  aws_access_key_id = pubkey,
  aws_secret_access_key = privkey,
  region_name='us-east-1',
  endpoint_url = MTURK_SANDBOX
)
print "I have $" + mturk.get_account_balance()['AvailableBalance'] + " in my Sandbox account"
#csv that holds recorded hits
csv = open('HIT_IDs.csv', "r") 

# results csv
results = open('HIT_RESULTS.csv', "w") 

# header row for results csv
first_row = "Hit Id, Hotel, Assignment Id, Assignment Status, Time Taken, workervote, feedback\n"
results.write(first_row)

#finds set of printable characters for string processing later
printable = set(string.printable)

for row in csv:
    [hit_id, hotel] = [x.strip() for x in row.split(',')]
    # We are only publishing this task to one Worker
    # So we will get back an array with one item if it has been completed
    worker_results = mturk.list_assignments_for_hit(HITId=hit_id)

    if worker_results['NumResults'] > 0:
        for assignment in worker_results['Assignments']:
            # The list of response fields from the HIT's form
            answers_list =  xmltodict.parse(assignment['Answer'])['QuestionFormAnswers']['Answer']
            if answers_list[0]['QuestionIdentifier'] != 'consent':
                raise Exception("Unexpected format: consent field is not first")
            elif answers_list[0]['FreeText'] != 'on':
                raise Exception("consent not granted for assignment", assignment['AssignmentId'])
            else:
                print "consent",answers_list[0]['FreeText']
            # Metadata from assignment, formatted for csv
            newRow = assignment["HITId"]  + ", " + " (" + hotel + ")" + ", " + assignment["AssignmentId"] +  ", " \
                + assignment["AssignmentStatus"] + ", " + str((assignment["SubmitTime"] \
                    - assignment["AcceptTime"]).total_seconds())

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

            newRow += ", " + str(answers_dict['workervote']) + ", " + str(answers_dict['feedback'])

            print newRow

            results.write(newRow + "\n")
    else:
        print "No results ready for HIT " + hit_id


print mturk.list_reviewable_hits()