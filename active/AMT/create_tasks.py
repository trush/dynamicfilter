###NOTES: install boto3 and xmltodict through pip before using. Replace pubkey and privkey with real keys.
import keys
pubkey = keys.pubkey
privkey = keys.privkey

import sys
import csv
import boto3
MTURK_SANDBOX = 'https://mturk-requester-sandbox.us-east-1.amazonaws.com'

mturk = boto3.client('mturk',
  aws_access_key_id = pubkey,
  aws_secret_access_key = privkey,
  region_name='us-east-1'
  # endpoint_url = MTURK_SANDBOX
)
print "I have $" + mturk.get_account_balance()['AvailableBalance'] + " in my account"
print "Are you sure you want to post HITs to this account?"
response = raw_input()

if response == 'yes':
  print "posting HITs"
else:
  print response
  sys.exit()
mycsv = open('HIT_IDs.csv', "a") #post to SANDBOX_HIT_IDs for sandbox data

#list of posted hits
hit_list = []

f = csv.reader(open('HOSPITAL_CLEAN.csv','r'), delimiter=',')
header = True 
for line in f:
  if header:
    header = False
    continue
  hotel = line[2]
  print hotel
  question = str(open(name='secondPredicate.xml',mode='r').read())
  question = question.replace('XXX(ITEM_NAME_HERE)XXX', hotel)
  new_hit = mturk.create_hit(
      Title = 'Evaluate a property of a hospital or clinic',
      Description = 'Answer the given yes/no question about the given hospital or clinic',
      Keywords = 'text, enumeration, matching',
      QualificationRequirements = [{
          'QualificationTypeId':"000000000000000000L0",
          'Comparator':"GreaterThan",
          'IntegerValues':[90]}],
      Reward = '0.10',
      MaxAssignments = 9,
      LifetimeInSeconds = 172800,
      AssignmentDurationInSeconds = 1200,
      AutoApprovalDelayInSeconds = 14400,
      Question = question,
  ) ## averages ?? time
  hit_list.append((new_hit, hotel, "eval_secondary_pred", None))
  print "A new HIT has been created. You can preview it here:"
  print "https://worker.mturk.com/mturk/preview?groupId=" + new_hit['HIT']['HITGroupId']
  print "HITID = " + new_hit['HIT']['HITId'] + " (Use to Get Results)"



# f = open('Hotel_items.csv')
# for line in f:
#   line = line.rstrip('\n')
#   hotel = line
#   print hotel
#   question = str(open(name='itemwiseJoin.xml',mode='r').read())
#   question = question.replace('XXX(ITEM_NAME_HERE)XXX', hotel)
#   new_hit = mturk.create_hit(
#       Title = 'Match hospitals to a hotel based on proximity',
#       Description = 'Find hospitals within 2.5 miles of the given hotel',
#       Keywords = 'text, enumeration, matching',
#       QualificationRequirements = [{
#           'QualificationTypeId':"000000000000000000L0",
#           'Comparator':"GreaterThan",
#           'IntegerValues':[90]}],
#       Reward = '0.25',
#       MaxAssignments = 9,
#       LifetimeInSeconds = 172800,
#       AssignmentDurationInSeconds = 1200,
#       AutoApprovalDelayInSeconds = 14400,
#       Question = question,
#   ) ## averages ?? time
#   hit_list.append((new_hit, hotel, "list_secondary", None))
#   print "A new HIT has been created. You can preview it here:"
#   print "https://worker.mturk.com/mturk/preview?groupId=" + new_hit['HIT']['HITGroupId']
#   print "HITID = " + new_hit['HIT']['HITId'] + " (Use to Get Results)"


  # question2 = str(open(name='joinableFilter.xml',mode='r').read())
  # question2 = question2.replace('XXX(ITEM_NAME_HERE)XXX', hotel)
  # new_hit = mturk.create_hit(
  #     Title = 'Determine a characteristic of a hotel',
  #     Description = 'Determine whether a given hotel is within 2 miles of a hospital with ',
  #     Keywords = 'text, enumeration, matching',
  #     QualificationRequirements = [{
  #         'QualificationTypeId':"000000000000000000L0",
  #         'Comparator':"GreaterThan",
  #         'IntegerValues':[90]}],
  #     Reward = '0.30',
  #     MaxAssignments = 9,
  #     LifetimeInSeconds = 172800,
  #     AssignmentDurationInSeconds = 1200,
  #     AutoApprovalDelayInSeconds = 14400,
  #     Question = question2,
  # ) ## averages ?? time
  # hit_list.append((new_hit, hotel, "eval_joinable_filter", None))
  # print "A new HIT has been created. You can preview it here:"
  # print "https://workersandbox.mturk.com/mturk/preview?groupId=" + new_hit['HIT']['HITGroupId']
  # print "HITID = " + new_hit['HIT']['HITId'] + " (Use to Get Results)"

# add posted hits to an external csv
for (hit, hotel, task, hospital) in hit_list:
  hitid = hit['HIT']['HITId']
  mycsv.write(str(hitid) + ", " + str(hotel) + ", " + str(task) + ", " + str(hospital) + "\n")
# Remember to modify the URL above when you're publishing
# HITs to the live marketplace.
# Use: https://worker.mturk.com/mturk/preview?groupId=

