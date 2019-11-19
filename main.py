# System libraries
import json

# Third party libraries (pip)
import tweepy # https://tweepy.readthedocs.io/en/latest/index.html
import pprint
from googlesearch import search # https://github.com/MarioVilas/googlesearch
import pandas as pd
import networkx as nx # https://networkx.github.io/documentation/stable/install.html

# Custom libraries
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

  # For each list in list_urls, get all the users in each list, as an UserInfo object

  for tw_list in list_urls[:1]:
    
    tw_list = tw_list[tw_list.find('.com') + 4:]
    user = tw_list.split('/')[1]
    list_name = tw_list.split('/')[3]

    # Using Tweepy api, getting json of all users in list
    list_members_output = api.list_members(user, list_name)[:1]
    # pprint.pprint(list_members_output)

    # Create a list of UserObject info for each user object in list_members_output
    users = [classes.UserInfo(
        id = user_id._json['id'],
        description = user_id._json['description'],
        handle = user_id._json['screen_name'],
        followers = utils.get_ids_by_type('followers', user_id._json['screen_name']),
        friends = utils.get_ids_by_type('friends', user_id._json['screen_name'])
      ) for user_id in list_members_output]

    result = utils.add_userinfo_to_db(users)
    print(result)

    return users

def users_to_graph(users):

  # From a CSV file with each node representing a edge on a graph, create a network graph that represents the relations dictated by the CSV file.
  
  # foreach user in users, create an node in the graph, and link it to it's followers and friends as edges
  users_graph = nx.DiGraph()
  for user in users:
    # Add a new node with the 
    users_graph.add_node(user.id, handle=user.handle)
    for friendid in user.friends:
      users_graph.add_edge(friendid, user.id)
      users_graph.add_edge(user.id, friendid)
    for followerid in user.followers:
      users_graph.add_edge(followerid, user.id)

  print(users_graph.nodes.data())
  print(users_graph.number_of_edges())

if __name__ == '__main__':
  # x = main()
  # y = get_users_in_lists(x)
  m = users_to_graph(utils.generate_sample_userinfo())