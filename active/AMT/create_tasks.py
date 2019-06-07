###NOTES: install boto3 and xmltodict through pip before using. Replace pubkey and privkey with real keys.
import keys
pubkey = keys.pubkey
privkey = keys.privkey

import boto3
MTURK_SANDBOX = 'https://mturk-requester-sandbox.us-east-1.amazonaws.com'

mturk = boto3.client('mturk',
  aws_access_key_id = pubkey,
  aws_secret_access_key = privkey,
  region_name='us-east-1',
  endpoint_url = MTURK_SANDBOX
)
print "I have $" + mturk.get_account_balance()['AvailableBalance'] + " in my Sandbox account"

csv = open('HIT_IDs.csv', "a") 

#list of posted hits
hit_list = []

f = open('Hotel_items.csv')
for line in f:
  line = line.rstrip('\n')
  hotel = line
  print hotel
  question = str(open(name='itemwiseJoin.xml',mode='r').read())
  question = question.replace('XXX(ITEM_NAME_HERE)XXX', hotel)
  new_hit = mturk.create_hit(
      Title = 'Match restaurants to a hotel based on proximity',
      Description = 'Find restaurants within 0.4 miles of the given hotel',
      Keywords = 'text, enumeration, matching',
      QualificationRequirements = [{
          'QualificationTypeId':"000000000000000000L0",
          'Comparator':"GreaterThan",
          'IntegerValues':[90]}],
      Reward = '0.10',
      MaxAssignments = 10,
      LifetimeInSeconds = 600, #MAKE THIS BIGGER FOR ACTUAL
      AssignmentDurationInSeconds = 600,
      AutoApprovalDelayInSeconds = 14400,
      Question = question,
  ) ## averages ?? time
  hit_list.append((new_hit, hotel, "list_secondary", None))
  print "A new HIT has been created. You can preview it here:"
  print "https://workersandbox.mturk.com/mturk/preview?groupId=" + new_hit['HIT']['HITGroupId']
  print "HITID = " + new_hit['HIT']['HITId'] + " (Use to Get Results)"


  question2 = str(open(name='joinableFilter.xml',mode='r').read())
  question2 = question2.replace('XXX(ITEM_NAME_HERE)XXX', hotel)
  new_hit = mturk.create_hit(
      Title = 'Determine a characteristic of a hotel',
      Description = 'Determine whether the given hotel is within 0.4 miles of a restaurant with good parking',
      Keywords = 'text, enumeration, matching',
      QualificationRequirements = [{
          'QualificationTypeId':"000000000000000000L0",
          'Comparator':"GreaterThan",
          'IntegerValues':[90]}],
      Reward = '0.10',
      MaxAssignments = 10,
      LifetimeInSeconds = 600, #MAKE THIS BIGGER FOR ACTUAL
      AssignmentDurationInSeconds = 600,
      AutoApprovalDelayInSeconds = 14400,
      Question = question2,
  ) ## averages ?? time
  hit_list.append((new_hit, hotel, "eval_joinable_filter", None))
  print "A new HIT has been created. You can preview it here:"
  print "https://workersandbox.mturk.com/mturk/preview?groupId=" + new_hit['HIT']['HITGroupId']
  print "HITID = " + new_hit['HIT']['HITId'] + " (Use to Get Results)"

  break
  #  question1 = str(open(name='prejoinFilter.xml',mode='r').read())
  #  question1 = question1.replace('XXX(ITEM_NAME_HERE)XXX', hotel)
  #  new_hit = mturk.create_hit(
  #      Title = 'Find zip code of hotels',
  #      Description = 'Label the zip code of a given hotel',
  #      Keywords = 'text, quick, labeling',
  #      Reward = '0.10',
  #      MaxAssignments = 1,
  #      LifetimeInSeconds = 172800,
  #      AssignmentDurationInSeconds = 600,
  #      AutoApprovalDelayInSeconds = 14400,
  #      Question = question1,
  #  ) ## averages ?? time
#    hit_list.append((new_hit, hotel, "eval_prejoin_filter", None))
  #  print "A new HIT has been created. You can preview it here:"
  #  print "https://workersandbox.mturk.com/mturk/preview?groupId=" + new_hit['HIT']['HITGroupId']
  #  print "HITID = " + new_hit['HIT']['HITId'] + " (Use to Get Results)"

# add posted hits to an external csv
for (hit, hotel, task, restaurant) in hit_list:
  hitid = hit['HIT']['HITId']
  csv.write(str(hitid) + ", " + str(hotel) + ", " + str(task) + ", " + str(restaurant) + "\n")
# Remember to modify the URL above when you're publishing
# HITs to the live marketplace.
# Use: https://worker.mturk.com/mturk/preview?groupId=

