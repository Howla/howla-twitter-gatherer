#region Imports & Init API variables

# System libraries
import json
import random

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

TOP_LEVEL_CATEGORIES = [
  'sports',
  'entertainment',
  'media',
  'food',
  'politics',
  'fashion',
  'technology',
  'religion',
  'travel',
  'science'
]

# https://friendorfollow.com/twitter/most-followers/
TOP_100_ACCOUNTS_BY_FOLLOWERS = {
  'barackobama': {
    'num_followers': 110418682,
    'tags': [
      'politics'
    ]
  },
  'katyperry': {
    'num_followers': 108285060, 
    'tags': [
      'entertainment'
    ]
  },
  'justinbeiber': {
    'num_followers': 107282921, 
    'tags': [
      'entertainment'
    ]
  },
  'rihanna': {
    'num_followers': 94579639, 
    'tags': [
      'entertainment'
    ]
  },  
  'talyorswift13': {
    'num_followers': 85171168, 
    'tags': [
      'entertainment'
    ]
  },  
  'cristiano': {
    'num_followers': 81139838, 
    'tags': [
      'sports'
    ]
  },  
  'ladygaga': {
    'num_followers': 80334549, 
    'tags': [
      'entertainment'
    ]
  },  
  'theellenshow': {
    'num_followers': 79055072, 
    'tags': [
      'entertainment'
    ]
  },  
  'youtube': {
    'num_followers': 72093748, 
    'tags': [
      'media'
    ]
  }, 
  'arianagrande': {
    'num_followers': 67544943, 
    'tags': [
      'entertainment'
    ]
  },   
  'realdonaldtrump': {
    'num_followers': 67544943, 
    'tags': [
      'politics'
    ]
  },  
  'jtimberlake': {
    'num_followers': 65026564, 
    'tags': [
      'entertainment'
    ]
  },  
  'kimkardashian': {
    'num_followers': 62377742, 
    'tags': [
      'entertainment'
    ]
  },  
  'selenagomez': {
    'num_followers': 58947690, 
    'tags': [
      'entertainment'
    ]
  }, 
  'twitter': {
    'num_followers': 56757969, 
    'tags': [
      'media'
    ]
  },  
  'britneyspears': {
    'num_followers': 56254837, 
    'tags': [
      'entertainment'
    ]
  }, 
  'cnnbrk': {
    'num_followers': 56110580, 
    'tags': [
      'media'
    ]
  }, 
  'shakira': {
    'num_followers': 51676098, 
    'tags': [
      'entertainment'
    ]
  }, 
  'jimmyfallon': {
    'num_followers': 51512361, 
    'tags': [
      'entertainment'
    ]
  }, 
  'narendramodi': {
    'num_followers': 51474434, 
    'tags': [
      'politics'
    ]
  }, 
}

# For testing purposes

TEST_MODE_ACTIVE = True

TEST_ACCOUNTS_FOR_CLASIFICATION = [
  ('ohitsdoh', ['politics']),
  ('_spe', ['technology']),
  ('_pxlu', ['sports']),
  ('suzannerivecca', ['media'])
]

#endregion

def main():
  pass

def get_lists_of_users(keywords):

  '''
  Get lists of Twitter users based on keywords from the keywords list

  Keyword Arguments:
  ====
  keywords -- the list of keywords to search Twitter lists for

  return: a list of urls that corresponds to the keywords provided

  '''

  # Auth to Twitter's servers
  # Get a dump of each user
  # foreach user, get:
  # @Name - Twitter Handle - String
  # Bio information - string
  # Who they are following - List
  # Who is following them - List

  # https://towardsdatascience.com/use-google-and-tweepy-to-build-a-dataset-of-twitter-users-cbfd556493a9
  list_urls = []
  for keyword_string in keywords:
    for url in search("site:twitter.com lists " + keyword_string, stop=20):
      if '/lists/' in url:
        list_urls.append(url)

  return list_urls

def get_users_in_lists(list_urls):

  '''
  For each list in list_urls, get all the users in each list, as an UserInfo object

  Keyword Arguments:
  ===
  list_urls -- the urls of the lists of Twitter users to be converted to UserInfo objects

  return: a list of UserInfo objects

  '''

  for tw_list in list_urls[:1]:
    
    tw_list = tw_list[tw_list.find('.com') + 4:]
    user = tw_list.split('/')[1]
    list_name = tw_list.split('/')[3]

    # Using Tweepy api, getting json of all users in list
    list_members_output = api.list_members(user, list_name)[:1]
    # pprint.pprint(list_members_output)

    # Create a list of UserObject info for each user object in list_members_output
    users = [utils.tweepy_user_to_userinfo_object(user_id) for user_id in list_members_output]
    result = utils.add_userinfo_to_db(users)

    return users

def users_to_graph(users):

  '''
  Converts a given list of UserInfo objects into a directed graph

  Keyword Arguments:
  ===
  users -- the list of UserInfo objects as nodes in the graph

  return: a directed graph representing the given UserInfo objects

  '''
  
  # foreach user in users, create an node in the graph, and link it to it's followers and friends as edges
  users_graph = nx.DiGraph()
  for user in users:
    # Add a new node with the id as the node identifer
    users_graph.add_node(user.id, userinfo=user)
    # Add directed edges with friends and followers
    for friendid in user.friends:
      users_graph.add_edge(user.id, friendid)
    for followerid in user.followers:
      users_graph.add_edge(followerid, user.id)

  return users_graph

def assign_top_level_categories(users_graph, top_level_reference_accounts):

  # To access a graph node by name, simply refer to it through dictionary access
  # e.g. user_graph['node_A']
  # To access the node's attributes, it's simply user_graph['node_A'].attribute_A

  users_graph_handles = nx.get_node_attributes(users_graph, 'handle').values()
  top_level_userinfoes = [utils.tweepy_user_to_userinfo_object(api.get_user(account_info[0])) for account_info in top_level_reference_accounts]
  for top_level_userinfo in top_level_userinfoes:
    userinfo_tags = next((x for x in top_level_reference_accounts if x[0] == top_level_userinfo.handle), None)
    top_level_userinfo.tags = userinfo_tags
    if TEST_MODE_ACTIVE:
      # Assign followers
      follower_pool_size = random.randint(0, len(users_graph.nodes))
      follower_pool = random.sample(users_graph.nodes, follower_pool_size)
      top_level_userinfo.followers = follower_pool
      # Assign friends
      friends_pool_size = random.randint(0, len(users_graph.nodes))
      friends_pool = random.sample(users_graph.nodes, friends_pool_size)
      top_level_userinfo.friends = friends_pool
    if top_level_userinfo.handle not in users_graph_handles:
      users_graph.add_node(top_level_userinfo.id, userinfo=top_level_userinfo)
      for friendid in top_level_userinfo.friends:
        users_graph.add_edge(top_level_userinfo.id, friendid)
      for followerid in top_level_userinfo.followers:
        users_graph.add_edge(followerid, top_level_userinfo.id)

  return users_graph

def categorize_node(user_graph, user_graph_node):

  '''
  Given a graph node repsenting a UserInfo object, classify by keywords based on it's followers and friends

  Keyword Argument:
  ===
  graph_node -- the node in the directed graph to be classified

  return: None

  '''

  # First, manually classify top level nodes, such as NBA, McDonalds, etc
  # Then, foreach node that directly follows or is friends with a top-level node, propagate the labels of the top-level node to the connected node
  # Then, for each those nodes, repeat the process, and enqueue nodes that until all nodes have been propagated to
  # Then, aggregate the count of the labels (some nodes may have the same labele propagated more than once due to their connections), and rank them in order

  '''
  1. Define the 10 categories to be used (food, entertainment, sports, etc)
  2. On Twitter, get the top 10 accounts for each category (defined by us)
  3. From these accounts, do the above propagation suggested, for X levels (to be determined later)
  '''

  pass

#region Helpers

def get_breakdown_by_category(reference_accounts):

  TOP_ACCOUNTS_BY_CATEGORIES = {}
  for handle in reference_accounts.keys():
    # The first tag should be the primary tag
    account_primary_tag = reference_accounts[handle]['tags'][0]
    account_num_followers = len(utils.get_ids_by_type('followers', handle))
    if account_primary_tag not in TOP_ACCOUNTS_BY_CATEGORIES:
      TOP_ACCOUNTS_BY_CATEGORIES[account_primary_tag] = [(handle, account_num_followers)]
    else:
      TOP_ACCOUNTS_BY_CATEGORIES[account_primary_tag].append((handle, account_num_followers))

  for category, category_data in TOP_ACCOUNTS_BY_CATEGORIES.items():
    TOP_ACCOUNTS_BY_CATEGORIES[category] = sorted(category_data, key=lambda tup: tup[1], reverse=True)

#endregion

if __name__ == '__main__':
  # x = main()
  # y = get_users_in_lists(x)
  m = users_to_graph(utils.generate_sample_userinfo(20))
  print(m.nodes)
  m = assign_top_level_categories(m, TEST_ACCOUNTS_FOR_CLASIFICATION)
  y = nx.get_node_attributes(m, 'userinfo')
  for k,v in y.items():
    print(k, v)
  # print(m.number_of_edges())
  # print(TOP_LEVEL_CATEGORIES)
  # n = classify_node('asd', TEST_ACCOUNTS_FOR_CLASIFICATION)
  # print(n)