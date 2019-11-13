# System libraries
import json

# Third party libraries (pip)
import tweepy # https://tweepy.readthedocs.io/en/latest/index.html
import pprint
from googlesearch import search # https://github.com/MarioVilas/googlesearch
import pandas as pd
import networkx # https://networkx.github.io/documentation/stable/install.html

# Custom scripts
import utils
import classes

# Open credentials.json and load the information to create the tweepy API object for queries
with open('credentials.json') as credentials_file:
  credentials = json.load(credentials_file)

auth = tweepy.OAuthHandler(credentials['consumer_key'], credentials['consumer_secret'])
auth.set_access_token(credentials['access_token'], credentials['access_token_secret'])
api = tweepy.API(auth)

def main():

  # Auth to Twitter's servers
  # Get a dump of each user
  # foreach user, get:
  # @Name - Twitter Handle - String
  # Bio information - string
  # Who they are following - List
  # Who is following them - List

  keyword_string = 'food'
  # https://towardsdatascience.com/use-google-and-tweepy-to-build-a-dataset-of-twitter-users-cbfd556493a9
  list_urls = []
  for url in search("site:twitter.com lists " + keyword_string, stop=20):
    if '/lists/' in url:
      list_urls.append(url)

  return list_urls

def get_users_in_lists(list_urls):

  for tw_list in list_urls[:1]:
    
    tw_list = tw_list[tw_list.find('.com') + 4:]
    user = tw_list.split('/')[1]
    list_name = tw_list.split('/')[3]

    # Using Tweepy api, getting json of all users in list
    list_members_output = api.list_members(user, list_name)[:1]
    pprint.pprint(list_members_output)

    users_dictionary = {}
    # Parsing json data and appending to appropriate lists instantiated above
    for user_id in list_members_output:
      users_dictionary[user_id._json['id']] = classes.UserInfo(
        id = user_id._json['id'],
        description = user_id._json['description'],
        handle = user_id._json['screen_name'],
        followers = utils.get_ids_by_type("followers", user_id._json['screen_name']),
        friends = utils.get_ids_by_type("friends", user_id._json['screen_name'])
      )

    # for k,v in users_dictionary.items():
    #   print(k, v)
    for id, data in users_dictionary.items():
      utils.to_csv(data, 'OUTFILE')

def users_to_graph():

  # From a CSV file with each node representing a edge on a graph, create a network graph that represents the relations dictated by the CSV file.
  pass

if __name__ == '__main__':
  x = main()
  y = get_users_in_lists(x)