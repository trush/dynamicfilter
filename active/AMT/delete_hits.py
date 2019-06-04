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
# contains IDs of published HITs
hitid_csv = open('HIT_IDs.csv', "r") 

#tracks undeletable hits
unfinished_hits = []

for row in hitid_csv:
    # gets hit id from csv
    (hit_id, hotel) = [x.strip() for x in row.split(',')]

    hit = mturk.get_hit(HITId = hit_id)

    if hit['HIT']['HITStatus'] == 'REVIEWABLE':
        mturk.delete_hit(HITId=hit_id)
        print hit_id
    else:
        # use update_expiration_for_hit to force expire then delete
        unfinished_hits.append((hit_id, hotel))

resultcsv = open('HIT_RESULTS.csv', "w")
for (hitid, hotel) in unfinished_hits:
    resultcsv.write(hitid + ", " + hotel + "\n")