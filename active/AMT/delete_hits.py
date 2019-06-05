# This file deletes all completed hits and removes all incomplete hits
# from MTurk. Use with care.
import keys
from datetime import datetime
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
# contains IDs of all published HITs and their corresponding hotels
hitid_csv = open('HIT_IDs.csv', "r") 
# all_hits = mturk.list_hits()['HITs']

#tracks undeletable hits
finished_hits = []

for row in hitid_csv:
    # gets hit id from csv
    (hit_id, hotel) = [x.strip() for x in row.split(',')]

    hit = mturk.get_hit(HITId = hit_id)

    # removes hits from MTurk if they are reviewable (have already been accepted or rejected)
    if hit['HIT']['HITStatus'] == 'Assignable' or hit['HIT']['HITStatus'] == u'Assignable':
      mturk.update_expiration_for_hit(HITId=hit_id, ExpireAt=datetime(2019, 1, 1))
      print "hit " + hit_id + " expired from MTurk."
    elif hit['HIT']['HITStatus'] == 'Reviewable' or hit['HIT']['HITStatus'] == u'Reviewable':
      mturk.delete_hit(HITId=hit_id)
      print "Reviewable hit " + hit_id + " deleted from MTurk."
    else:
      print "hit " + hit_id + " not removed, status=" + str(hit['HIT']['HITStatus'])
      finished_hits.append((hit_id, hotel))


# clear removed HITs from csv
hitid_csv = open('HIT_IDs.csv', "w") 

#refill completed hits
for (hit_id, hotel) in finished_hits:
  hitid_csv.write(hit_id + ", " + hotel + "\n")


print "All recorded assignable HITs expired. No tasks should be posted to MTurk."