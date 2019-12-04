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
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, compression=True)

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
TOP_100_ACCOUNTS_BY_FOLLOWERS = [
  ('barackobama', ['politics']),
  # ('katyperry', ['entertainment']),
  # ('justinbieber', ['entertainment']),
  # ('rihanna', ['entertainment']),
  # ('taylorswift13', ['entertainment']),
  # ('cristiano', ['sports']),
  # ('ladygaga', ['entertainment']),
  # ('theellenshow', ['entertainment']),
  # ('youtube', ['media']),
  # ('arianagrande', ['entertainment']),
  # ('realdonaldtrump', ['politics']),
  # ('jtimberlake', ['entertainment']),
  # ('kimkardashian', ['entertainment']),
  # ('selenagomez', ['entertainment']),
  # ('twitter', ['media']),
  # ('britneyspears', ['entertainment']),
  # ('cnnbrk', ['media']),
  # ('shakira', ['entertainment']),
  # ('narendramodi', ['politics']),
  # ('jimmyfallon', ['entertainment'])
]

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
  
  # Part 1: Gathering the data
  # Foreach category, get the top 10 users by followers within that category, and their followers
  # Foreach follower, if they have >5 others that they are following, create a userinfo object and add it to the database

  # Part 2: Creating the graph
  # Foreach category, get the top 10 users by followers within that category, and categorize them, then insert into the directed graph as the top-level nodes with the tags
  # Foreach user in the database, add it to the graph as a node

  # Part 3: Category propagation
  # Foreach node in the 

  pass

#region Part 1: Gathering Data

def get_top_users_by_followers(category_list, reference_accounts):

  '''
  Gets the top 10 users per category by followers specified by category_list.

  Keyword Arguments:
  ===
  category_list -- the list of categories to get users for
  reference_accounts -- the list of accounts to gather data from

  return: top_users_by_category -- a dictionary of categories, with the values being the list of users of that category, sorted by followers descending

  '''

  top_users_by_category = {}
  
  for account_info in reference_accounts:
    tweepy_user_object = api.get_user(account_info[0])
    num_followers = tweepy_user_object._json['followers_count']
    if account_info[1][0] in category_list:
      if account_info[1][0] not in top_users_by_category.keys():
        top_users_by_category[account_info[1][0]] = [(account_info[0], num_followers)]
      else:
        top_users_by_category[account_info[1][0]].append((account_info[0], num_followers))

  for category, category_data in top_users_by_category.items():
    top_users_by_category[category] = sorted(category_data, key=lambda tup: tup[1], reverse=True)[:9]

  return top_users_by_category

def get_users(top_users_by_category):

  '''
  Gets all followers of each user in top_users_by_category that follows 5 or more other accounts, and stores them into the database as a UserInfo object.

  Keyword Arguments:
  ===
  top_users_by_category -- a dictionary of categories, with the values being the list of users of that category, sorted by followers descending

  return: result_ids -- the ObjectIds of the UserInfo objects that have been inserted into the database

  '''
  followers_to_add = []
  follower_ids_to_add = []

  for category, category_data in top_users_by_category.items():
    for user_data in category_data:
      tweepy_user_object = api.get_user(user_data[0])
      userinfo_object = utils.tweepy_user_to_userinfo_object(tweepy_user_object)
      for page in tweepy.Cursor(api.followers_ids, screen_name=user_data[0]).pages(1):
        for follower_id in random.sample(page, 10):
          try:
            follower_user_object = api.get_user(follower_id)
            print(follower_user_object)
            if follower_user_object._json['friends_count'] >= 10 and follower_user_object._json['id'] not in follower_ids_to_add:
              follower_userinfo_object = utils.tweepy_user_to_userinfo_object(follower_user_object)
              followers_to_add.append(follower_userinfo_object)
              follower_ids_to_add.append(follower_user_object._json['id'])
          except tweepy.TweepError:
            print("Failed to run the command on that user, Skipping...")
            continue

  print(followers_to_add)
  result_ids = utils.add_userinfo_to_db(followers_to_add)
  
  return result_ids

#endregion

#region Part 2: Constructing the graph

def users_to_graph(users):

  '''
  Converts a given list of UserInfo objects into a directed graph.

  Keyword Arguments:
  ===
  users -- the list of UserInfo objects as nodes in the graph

  return: a directed graph representing the given UserInfo objects

  '''
  
  # foreach user in users, create an node in the graph, and link it to it's followers and friends as edges
  users_graph = nx.DiGraph()
  for user in users:
    if user.id not in users_graph.nodes:
    # Add a new node with the id as the node identifer
      users_graph.add_node(user.id, userinfo=user)
    # Add directed edges with friends and followers
    for friendid in user.friends:
      if friendid not in users_graph.nodes:
        users_graph.add_node(friendid, next(n_user for n_user in users if n_user.id == friendid))
      users_graph.add_edge(user.id, friendid)
    for followerid in user.followers:
      if followerid not in users_graph.nodes:
        users_graph.add_node(followerid, next(n_user for n_user in users if n_user.id == followerid))
      users_graph.add_edge(followerid, user.id)

  return users_graph

def assign_top_level_categories(users_graph, top_level_reference_accounts):

  ''' 
  Assigns tags for categories for top level nodes based on reference accounts to the given graph.

  Keyword Arguments:
  ===
  users_graph -- the graph's top-level nodes to assign tags for
  top_level_reference_accounts -- the reference accounts to be assign to the graph

  return: users_graph -- the graph after having the top-level nodes assigned based on tags

  '''

  # To access a graph node by name, simply refer to it through dictionary access
  # e.g. user_graph['node_A']
  # To access the node's attributes, it's simply user_graph['node_A'].attribute_A

  users_graph_handles = nx.get_node_attributes(users_graph, 'handle').values()
  top_level_userinfoes = [utils.tweepy_user_to_userinfo_object(api.get_user(account_info[0])) for account_info in top_level_reference_accounts]
  for top_level_userinfo in top_level_userinfoes:
    userinfo_tags = next((x[1] for x in top_level_reference_accounts if x[0] == top_level_userinfo.handle.lower()), None)
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
        if friendid in users_graph.nodes:
          users_graph.add_edge(top_level_userinfo.id, friendid)
      for followerid in top_level_userinfo.followers:
        if followerid in users_graph.nodes:
          users_graph.add_edge(followerid, top_level_userinfo.id)

  return users_graph

def categorize_node(user_graph_node):

  '''
  Given a graph node repsenting a UserInfo object, classify by keywords based on it's followers and friends.

  Keyword Argument:
  ===
  graph_node -- the node in the directed graph to be classified

  return: users_graph -- the graph of users once 

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

#endregion

#region Part 3: Categorization & Propagation

#endregion

#region Helpers

def get_breakdown_by_category(reference_accounts):

  TOP_ACCOUNTS_BY_CATEGORIES = {}
  for handle in reference_accounts.keys():
    # The first tag should be the primary tag
    account_primary_tag = reference_accounts[handle]['tags'][0]
    account_num_followers = api.get_users(handle)._json['followers_count']
    if account_primary_tag not in TOP_ACCOUNTS_BY_CATEGORIES:
      TOP_ACCOUNTS_BY_CATEGORIES[account_primary_tag] = [(handle, account_num_followers)]
    else:
      TOP_ACCOUNTS_BY_CATEGORIES[account_primary_tag].append((handle, account_num_followers))

  for category, category_data in TOP_ACCOUNTS_BY_CATEGORIES.items():
    TOP_ACCOUNTS_BY_CATEGORIES[category] = sorted(category_data, key=lambda tup: tup[1], reverse=True)

  return TOP_ACCOUNTS_BY_CATEGORIES

#endregion

#region To-be-restructured

def get_lists_of_users(keywords):

  '''
  Get lists of Twitter users based on keywords from the keywords list.

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
  For each list in list_urls, get all the users in each list, as an UserInfo object.

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

#endregion

if __name__ == '__main__':
  # x = main()
  y = get_top_users_by_followers(TOP_LEVEL_CATEGORIES, TOP_100_ACCOUNTS_BY_FOLLOWERS)
  print(y)
  v = get_users(y)
  print(v)
  # m = users_to_graph(utils.generate_sample_userinfo(20))
  # print(m.nodes)
  # m = assign_top_level_categories(m, TOP_100_ACCOUNTS_BY_FOLLOWERS)
  # y = nx.get_node_attributes(m, 'userinfo')
  # for k,v in y.items():
  #   print(k, v)
  # print(m.number_of_edges())
  # print(TOP_LEVEL_CATEGORIES)
  # n = classify_node('asd', TEST_ACCOUNTS_FOR_CLASIFICATION)
  # print(n)
  # user = api.get_user('barackobama')
  # followers = utils.get_ids_by_type('followers', 'barackobama')
  # print(followers)