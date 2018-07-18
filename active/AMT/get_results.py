###NOTES: install boto3 and xmltodict through pip before using. Replace pubkey and privkey with real keys. Replace hitId with a real hitId


import boto3
MTURK_SANDBOX = 'https://mturk-requester-sandbox.us-east-1.amazonaws.com'

mturk = boto3.client('mturk',
  aws_access_key_id = pubkey,
  aws_secret_access_key = privkey,
  region_name='us-east-1',
  endpoint_url = MTURK_SANDBOX
)
print "I have $" + mturk.get_account_balance()['AvailableBalance'] + " in my Sandbox account"

csv = open('HIT_IDs.csv', "r") 


# You will need the following library
# to help parse the XML answers supplied from MTurk
# Install it in your local environment with
# pip install xmltodict
import xmltodict
# Use the hit_id previously created

for row in csv:
    hit_id = row.rstrip("\n")
    # We are only publishing this task to one Worker
    # So we will get back an array with one item if it has been completed
    worker_results = mturk.list_assignments_for_hit(HITId=hit_id, AssignmentStatuses=['Submitted'])
    print worker_results

    if worker_results['NumResults'] > 0:
        for assignment in worker_results['Assignments']:
            xml_doc = xmltodict.parse(assignment['Answer'])
            
            print "Worker's answer was:"
            if type(xml_doc['QuestionFormAnswers']['Answer']) is list:
                # Multiple fields in HIT layout
                for answer_field in xml_doc['QuestionFormAnswers']['Answer']:
                    print "For input field: " + answer_field['QuestionIdentifier']
                    if answer_field['FreeText'] is not None:
                        print "Submitted answer: " + answer_field['FreeText']
            else:
                # One field found in HIT layout
                print "For input field: " + xml_doc['QuestionFormAnswers']['Answer']['QuestionIdentifier']
                print "Submitted answer: " + xml_doc['QuestionFormAnswers']['Answer']['FreeText']
    else:
        print "No results ready yet"


