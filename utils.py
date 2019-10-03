# System libraries
import json
import time
# Third party libraries (pip)
import tweepy

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


  