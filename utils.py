#region Imports & Init
# System libraries
import json
import time
import csv
import random

# Third party libraries (pip)
import tweepy
import pymongo
import dns
from faker import Faker # https://faker.readthedocs.io/en/stable/
from faker.providers import lorem

# Custom libraries
import classes

# Open credentials.json and load the information to create the tweepy API object for queries
with open('credentials.json') as credentials_file:
  credentials = json.load(credentials_file)

auth = tweepy.OAuthHandler(credentials['consumer_key'], credentials['consumer_secret'])
auth.set_access_token(credentials['access_token'], credentials['access_token_secret'])
api = tweepy.API(auth)
fake = Faker()
fake.add_provider(lorem)

#endregion

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
      
def add_userinfo_to_db(userinfo_collection):

  client = pymongo.MongoClient("mongodb+srv://pxlu:V8cjnDXOlIj3Vt96@howla-sandbox-fdsr1.mongodb.net/test?retryWrites=true&w=majority")
  db = client['twitter_user_data']
  db_userinfo = db.userinfo
  # print(db.list_collection_names())

  userinfo_to_be_inserted = [{ 
    'userId': userinfo.id,
    'description': userinfo.description,
    'handle': userinfo.handle,
    'followers': userinfo.followers,
    'friends': userinfo.friends
  } for userinfo in userinfo_collection]

  result = db_userinfo.insert_many(userinfo_to_be_inserted)
  return result.inserted_ids

#region Misc Data Helpers

def generate_sample_userinfo(limit=20):

  result = []
  # Generate the sample userinfo in this order:
  # 1. The pool of userids, and their associated decriptions and handles
  # 2. The relationships between the userids, randomly generate their friends and followers among others in the pool
  # 3. Create the userinfo objects and return them

  user_pool = {}
  for i in range(limit):
    generated_userid = fake.random_int(min=100000000000, max=999999999999, step=1)
    while generated_userid in user_pool.keys():
      generated_userid = fake.random_int(min=100000000000, max=999999999999, step=1)
    user_pool[generated_userid] = {
      'description': fake.paragraph(nb_sentences=3, variable_nb_sentences=True, ext_word_list=None), 
      'handle': fake.user_name()
    }

  for userid in user_pool.keys():
    # Add friends first
    friends_to_add = []
    friend_pool_size = random.randint(0, len(user_pool) - 1)
    if friend_pool_size > 0:
      friends_pool = [friendid for friendid in user_pool.keys() if friendid != userid]
      friends_to_add = random.sample(friends_pool, friend_pool_size)
    user_pool[userid]['friends'] = friends_to_add

    # Add followers, minus your friends and yourself from the pool
    followers_to_add = []
    follower_pool_size = random.randint(0, len(user_pool) - friend_pool_size - 1)
    if follower_pool_size > 0:
      followers_pool = [followerid for followerid in user_pool.keys() if followerid not in friends_to_add and followerid != userid]
      followers_to_add = random.sample(followers_pool, follower_pool_size)
    user_pool[userid]['followers'] = followers_to_add

  users = [classes.UserInfo(
    id = user_id,
    description = user_data['description'],
    handle = user_data['handle'],
    followers = user_data['followers'],
    friends = user_data['friends']
  ) for user_id, user_data in user_pool.items()]

  return users

#endregion

#region Depreciated Helpers

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

#endregion

if __name__ == '__main__':
  generate_sample_userinfo(limit=20)