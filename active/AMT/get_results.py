###NOTES: install boto3 and xmltodict through pip before using. Replace pubkey and privkey with real keys. Replace hitId with a real hitId
import keys
pubkey = keys.pubkey
privkey = keys.privkey

import boto3
import string
import datetime
MTURK_SANDBOX = 'https://mturk-requester-sandbox.us-east-1.amazonaws.com'

mturk = boto3.client('mturk',
  aws_access_key_id = pubkey,
  aws_secret_access_key = privkey,
  region_name='us-east-1'
)
print "I have $" + mturk.get_account_balance()['AvailableBalance'] + " in my Sandbox account"
csv = open('HIT_IDs.csv', "r") 


# You will need the following library
# to help parse the XML answers supplied from MTurk
# Install it in your local environment with
# pip install xmltodict
import xmltodict
# Use the hit_id previously created

results = open('HIT_RESULTS.csv', "w") 
flag = False

for row in csv:
    [hit_id, hotel] = [x.strip() for x in row.split(',')]
    # We are only publishing this task to one Worker
    # So we will get back an array with one item if it has been completed
    worker_results = mturk.list_assignments_for_hit(HITId=hit_id)
    print hotel
    print worker_results

    if worker_results['NumResults'] > 0:
        for assignment in worker_results['Assignments']:
            newRow = str((assignment["SubmitTime"] - assignment["AcceptTime"]).total_seconds()) + ", " + assignment["AssignmentStatus"] + ", " + assignment["WorkerId"] + "," + assignment["HITId"] + " (" + hotel + ")"
            xml_doc = xmltodict.parse(assignment['Answer'])
            
            print "Worker's answer was:"
            if type(xml_doc['QuestionFormAnswers']['Answer']) is list:
                # Multiple fields in HIT layout
                flag = False
                for answer_field in xml_doc['QuestionFormAnswers']['Answer']:
                    if answer_field['QuestionIdentifier'] == 'consent':
                        if answer_field['FreeText'] == 'on':
                            newRow += (", consent given")
                            newRow += (", [")
                            flag = True
                            break
                        else:
                            newRow += (", INADMISSABLE")
                            newRow += (", [")
                            break
                if not flag:
                    newRow += (", INADMISSABLE")
                    newRow += (", [")
                for answer_field in xml_doc['QuestionFormAnswers']['Answer']:
                    if answer_field['QuestionIdentifier'] == 'consent':
                        continue
                    if answer_field['QuestionIdentifier'] == 'comments':
                        newRow = newRow[:-2]
                        if answer_field['FreeText'] is not None:
                            newRow += "], " + answer_field['FreeText']
                        else:
                            newRow += "], no comment"
                        break
                    print "For input field: " + answer_field['QuestionIdentifier']
                    if answer_field['FreeText'] is not None:
                        newRow += (answer_field['FreeText'].lower() + "| ")
                        print "Submitted answer: " + answer_field['FreeText']
                newRow += "\n"
                for i in range(len(newRow)):
                    if newRow[i] == u'\u2019': #TODO: catch other exceptions
                        newRow = newRow[:i] + newRow[i+1:]
                        break
                results.write(newRow)
            else:
                # One field found in HIT layout
                print "For input field: " + xml_doc['QuestionFormAnswers']['Answer']['QuestionIdentifier']
                print "Submitted answer: " + xml_doc['QuestionFormAnswers']['Answer']['FreeText']
            results.write("\n")
    else:
        print "No results ready yet"


print mturk.list_reviewable_hits()