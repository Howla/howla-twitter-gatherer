#region Imports & Init API variables

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
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, compression=True))

# Init faker module and add relevent providers to generate fake data
fake = Faker()
fake.add_provider(lorem)

# Init MonogoDB connection
MONGO_CLIENT = pymongo.MongoClient('mongodb+srv://' + credentials['mongodbuser'] + ':' + credentials['mongodbpassword'] + '@howla-sandbox-fdsr1.mongodb.net/test?retryWrites=true&w=majority')
TWITTER_USER_DATA_DB = MONGO_CLIENT.twitter_user_data

#endregion

def get_ids_by_type(id_type, screen_name="ohitsdoh"): 

  '''
  Get a list of user ids from a Twitter account by the type specified.

  Keyword arguments:
  ===
  id_type -- the type of id to get (either friends or followers)
  screen_name -- the twitter account's screen name to get the ids from

  return: ids -- the list of ids represented as integers

  '''

  # Specify method by id_type to use
  if id_type == "followers":
    method_to_use = api.followers_ids
  else:
    method_to_use = api.friends_ids

  # Get the list of ids, paginated by 5000 at a time.
  ids = []
  # Arbitarily set to get 100k followers right now, until decision on how to handle more data in memory
  for page in limit_handled(tweepy.Cursor(method_to_use, screen_name=screen_name).pages(2)):
    if len(page) == 5000:
      ids.extend(page)
      time.sleep(10)
    else:
      ids.extend(page)

  return ids

def tweepy_user_to_userinfo_object(tweepy_user):

  '''
  Converts a tweepy.User object into a UserInfo object.

  Keyword Arguments:
  ===
  tweepy_user -- the tweepy.User object to convert into a UserInfo object

  return: userinfo_object -- the converted tweepy.User object as a UserInfo object

  '''

  userinfo_object = classes.UserInfo(
        id = tweepy_user._json['id'],
        description = tweepy_user._json['description'],
        handle = tweepy_user._json['screen_name'],
        followers = get_ids_by_type('followers', tweepy_user._json['screen_name']),
        friends = get_ids_by_type('friends', tweepy_user._json['screen_name']),
        tags = []
  )

  return userinfo_object
      
def add_userinfo_to_db(userinfo_collection):
  
  '''
  Add json-serialized UserInfo object(s) to the MongoDB database collection specified.

  Keyword arguments:
  ===
  userinfo_collection -- The collection of UserInfo objects to be added to the database

  return: the list of ObjectIds of the inserted UserInfo objects

  '''

  # Connect to the MongoDB database and collection
  db_userinfo = TWITTER_USER_DATA_DB.userinfo

  userinfo_to_be_inserted = [{ 
    'userid': userinfo.id,
    'description': userinfo.description,
    'handle': userinfo.handle,
    'followers': userinfo.followers,
    'friends': userinfo.friends,
    'tags': userinfo.tags
  } for userinfo in userinfo_collection]

  result = db_userinfo.insert_many(userinfo_to_be_inserted)
  return result.inserted_ids

def hydrate_userinfo_objects_from_db():

  db_userinfo = TWITTER_USER_DATA_DB.userinfo
  hydrated_userinfoes = []

  for userinfo in db_userinfo.find():
    userinfo_object = classes.UserInfo(
        id = userinfo['userid'],
        description = userinfo['description'],
        handle = userinfo['handle'],
        followers = userinfo['followers'],
        friends = userinfo['friends'],
        tags = userinfo['tags']
    )
    hydrated_userinfoes.append(userinfo_object)
  
  return hydrated_userinfoes

#region Misc Data Helpers

def generate_sample_userinfo(limit=20):

  '''
  Generates sample UserInfo objects intended for testing purposes.

  Keyword arguments:
  ===
  limit -- the number of UserInfo objects to generate

  return: the list of UserInfo objects generated

  '''

  # Generate the sample userinfo in this order:
  # 1. The pool of userids, and their associated decriptions and handles
  # 2. The relationships between the userids, randomly generate their friends and followers among others in the pool
  # 3. Create the userinfo objects and return them

  user_pool = {}
  for i in range(limit):
    # Generate a 12 digit number and add it if it doesn't exist in the user_pool of ids
    generated_userid = fake.random_int(min=100000000000, max=999999999999, step=1)
    while generated_userid in user_pool.keys():
      generated_userid = fake.random_int(min=100000000000, max=999999999999, step=1)
    # 
    user_pool[generated_userid] = {
      'description': fake.paragraph(nb_sentences=3, variable_nb_sentences=True, ext_word_list=None), 
      'handle': fake.user_name()
    }

  for userid in user_pool.keys():
    # Add friends first
    friends_to_add = []
    # Don't include the current user object
    friend_pool_size = random.randint(0, len(user_pool) - 1)
    # Take a sample of users to be added as friends
    if friend_pool_size > 0:
      friends_pool = [friendid for friendid in user_pool.keys() if friendid != userid]
      friends_to_add = random.sample(friends_pool, friend_pool_size)
    user_pool[userid]['friends'] = friends_to_add

    # Add followers, minus your friends and yourself from the pool
    followers_to_add = []
    follower_pool_size = random.randint(0, len(user_pool) - 1)
    # Take a sample of users to be added as followers
    if follower_pool_size > 0:
      followers_pool = [followerid for followerid in user_pool.keys() if followerid != userid]
      followers_to_add = random.sample(followers_pool, follower_pool_size)
    user_pool[userid]['followers'] = followers_to_add

  users = [classes.UserInfo(
    id = user_id,
    description = user_data['description'],
    handle = user_data['handle'],
    followers = user_data['followers'],
    friends = user_data['friends'],
    tags = []
  ) for user_id, user_data in user_pool.items()]

  return users

#endregion

#region Helpers

# http://docs.tweepy.org/en/latest/code_snippet.html#handling-the-rate-limit-using-cursors
def limit_handled(cursor):
  while True:
    try:
      yield cursor.next()
    except tweepy.RateLimitError:
      time.sleep(15 * 60)

#endregion

if __name__ == '__main__':
  # x = generate_sample_userinfo(limit=20)
  # for userinfo in x:
  #   print(userinfo)
  y = get_ids_by_type('followers')
  print(y)