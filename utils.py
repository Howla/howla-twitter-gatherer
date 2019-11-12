# System libraries
import json
import time
import csv

# Third party libraries (pip)
import tweepy

# Open credentials.json and load the information to create the tweepy API object for queries
with open('credentials.json') as credentials_file:
  credentials = json.load(credentials_file)

auth = tweepy.OAuthHandler(credentials['consumer_key'], credentials['consumer_secret'])
auth.set_access_token(credentials['access_token'], credentials['access_token_secret'])
api = tweepy.API(auth)

def get_ids_by_type(id_type, screen_name="ohitsdoh"): 

  if id_type == "followers":
    method_to_use = api.followers_ids
  else:
    method_to_use = api.friends_ids

  ids = []
  for page in tweepy.Cursor(method_to_use, screen_name=screen_name).pages():
    if len(page) == 5000:
      ids.extend(page)
      time.sleep(60)
    else:
      ids.extend(page)

  return ids

def to_csv(user_info_dict, file_name):

  with open(file_name + '.csv', 'a', newline='') as csvfile:
    fieldnames = ['follower_id', 'followee_id']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    # Add rows representing each follower of this account
    for follower_user_id in user_info_dict['followers']:
      # follower_user_id is a integer in a list
      writer.writerow({'follower_id': follower_user_id, 'followee_id': user_info_dict['id']})

    for friend_user_id in user_info_dict['friends']:
      # friend_user_id is a integer in a list
      writer.writerow({'follower_id': user_info_dict['id'], 'followee_id': friend_user_id})
