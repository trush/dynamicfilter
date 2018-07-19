###NOTES: install boto3 and xmltodict through pip before using. Replace pubkey and privkey with real keys.

import boto3
MTURK_SANDBOX = 'https://mturk-requester-sandbox.us-east-1.amazonaws.com'

mturk = boto3.client('mturk',
  aws_access_key_id = pubkey,
  aws_secret_access_key = privkey,
  region_name='us-east-1'
)
print "I have $" + mturk.get_account_balance()['AvailableBalance'] + " in my Sandbox account"

csv = open('HIT_IDs.csv', "w") 

f = open('Hotel_items.csv')
for line in f:
   line = line.rstrip('\n')
   hotel = line
   print hotel
   question = str(open(name='questions.xml',mode='r').read())
   question = question.replace('XXX(ITEM_NAME_HERE)XXX', hotel)
   new_hit = mturk.create_hit(
       Title = 'Match metro, subway, and train stations to hotels based on proximity',
       Description = 'Find metro, subway, and train stations within 1 mile of the given hotel',
       Keywords = 'text, enumeration, matching',
       QualificationRequirements = [{
            'QualificationTypeId':"000000000000000000L0",
            'Comparator':"GreaterThan",
            'IntegerValues':[90]}],
       Reward = '0.15',
       MaxAssignments = 10,
       LifetimeInSeconds = 172800,
       AssignmentDurationInSeconds = 600,
       AutoApprovalDelayInSeconds = 172800,
       Question = question,
   ) ## averages 4-6 minutes
   print "A new HIT has been created. You can preview it here:"
   print "https://worker.mturk.com/mturk/preview?groupId=" + new_hit['HIT']['HITGroupId']
   print "HITID = " + new_hit['HIT']['HITId'] + " (Use to Get Results)"

  #  question1 = str(open(name='questions1.xml',mode='r').read())
  #  question1 = question1.replace('XXX(ITEM_NAME_HERE)XXX', hotel)
  #  new_hit = mturk.create_hit(
  #      Title = 'Find zip code of hotels',
  #      Description = 'Label the zip code of a given hotel',
  #      Keywords = 'text, quick, labeling',
  #      Reward = '0.15',
  #      MaxAssignments = 1,
  #      LifetimeInSeconds = 172800,
  #      AssignmentDurationInSeconds = 14400,
  #      AutoApprovalDelayInSeconds = 600,
  #      Question = question1,
  #  ) ## averages 20-30 seconds
  #  print "A new HIT has been created. You can preview it here:"
  #  print "https://workersandbox.mturk.com/mturk/preview?groupId=" + new_hit['HIT']['HITGroupId']
  #  print "HITID = " + new_hit['HIT']['HITId'] + " (Use to Get Results)"

   # question2 = str(open(name='questions2.xml',mode='r').read())
   # question2 = question2.replace('XXX(ITEM_NAME_HERE)XXX', hotel)
   # new_hit = mturk.create_hit(
   #     Title = 'Match hotels and metro stations',
   #     Description = 'Choose whether or not a hotel and a metro station match based on closeness',
   #     Keywords = 'text, quick, labeling',
   #     Reward = '0.15',
   #     MaxAssignments = 1,
   #     LifetimeInSeconds = 172800,
   #     AssignmentDurationInSeconds = 14400,
   #     AutoApprovalDelayInSeconds = 600,
   #     Question = question2,
   # ) ## averages 30-50 seconds, looks to improve significantly over short time
   # print "A new HIT has been created. You can preview it here:"
   # print "https://workersandbox.mturk.com/mturk/preview?groupId=" + new_hit['HIT']['HITGroupId']
   # print "HITID = " + new_hit['HIT']['HITId'] + " (Use to Get Results)"


   row = new_hit['HIT']['HITId']
   csv.write(row + ", " + hotel + "\n")
# Remember to modify the URL above when you're publishing
# HITs to the live marketplace.
# Use: https://worker.mturk.com/mturk/preview?groupId=

