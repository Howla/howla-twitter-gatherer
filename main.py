#region Imports & Init API variables

# System libraries
import json
import random
import copy
import pprint

# Third party libraries (pip)
import tweepy # https://tweepy.readthedocs.io/en/latest/index.html
from googlesearch import search # https://github.com/MarioVilas/googlesearch
import pandas as pd
import networkx as nx # https://networkx.github.io/documentation/stable/install.html
from faker import Faker # https://faker.readthedocs.io/en/stable/

# Custom libraries
import utils
import classes

# Open credentials.json and load the information to create the tweepy API object for queries
with open('credentials.json') as credentials_file:
  credentials = json.load(credentials_file)

auth = tweepy.OAuthHandler(credentials['consumer_key'], credentials['consumer_secret'])
auth.set_access_token(credentials['access_token'], credentials['access_token_secret'])
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, compression=True)

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

def get_top_users_by_followers(category_list, reference_accounts_by_category):

  '''
  Gets the top 10 users per category by followers specified by category_list.

  Keyword Arguments:
  ===
  category_list -- the list of categories to get users for
  reference_accounts -- the list of accounts to gather data from

  return: top_users_by_category -- a dictionary of categories, with the values being the list of users of that category, sorted by followers descending

  '''

  top_users_by_category = {}
  
  for category in reference_accounts_by_category.keys():
    users_in_category = reference_accounts_by_category[category]
    for account_handle in users_in_category:
      print(account_handle)
      tweepy_user_object = api.get_user(account_handle)
      num_followers = tweepy_user_object._json['followers_count']
      if category in category_list:
        if category not in top_users_by_category.keys():
          top_users_by_category[category] = [(account_handle, num_followers)]
        else:
          top_users_by_category[category].append((account_handle, num_followers))

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
  userinfo_objects_to_add = []
  already_processed_follower_ids = []

  for category, category_data in top_users_by_category.items():
    for user_data in category_data:
      tweepy_user_object = api.get_user(user_data[0])
      userinfo_object = utils.tweepy_user_to_userinfo_object(tweepy_user_object)
      current_user_followers = []
      # # =================
      for page in tweepy.Cursor(api.followers_ids, screen_name=user_data[0]).pages(1):
        for follower_id in random.sample(page, 10):
          if follower_id not in already_processed_follower_ids:
            try:
              follower_user_object = api.get_user(follower_id)
              print(follower_user_object)
              if follower_user_object._json['friends_count'] >= 10 and follower_user_object._json['followers_count'] >= 5 and follower_id not in already_processed_follower_ids:
                follower_userinfo_object = utils.tweepy_user_to_userinfo_object(follower_user_object)
                userinfo_objects_to_add.append(follower_userinfo_object)
                current_user_followers.append(follower_id)
            except tweepy.TweepError:
              print("Failed to run the command on that user, Skipping...")
              continue
          already_processed_follower_ids.append(follower_id)
      userinfo_object.followers = current_user_followers
      userinfo_objects_to_add.append(userinfo_object)
      # =================
      # for page in tweepy.Cursor(api.followers_ids, screen_name=user_data[0]).pages():
      #   for follower_id in page:
      #     if follower_id not in already_processed_follower_ids:
      #       try:
      #         follower_user_object = api.get_user(follower_id)
      #         if follower_user_object._json['friends_count'] >= 10 and follower_id not in already_processed_follower_ids:
      #           follower_userinfo_object = utils.tweepy_user_to_userinfo_object(follower_user_object)
      #           followers_to_add.append(follower_userinfo_object)
      #       except tweepy.TweepError:
      #         print("Failed to run the command on that user, Skipping...")
      #         continue
      #     already_processed_follower_ids.append(follower_id)

  print(userinfo_objects_to_add)
  result_ids = utils.add_userinfo_to_db(userinfo_objects_to_add)
  
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
        friend_user = next((n_user for n_user in users if n_user.id == friendid), None)
        if friend_user is None:
          friend_user = utils.tweepy_user_to_userinfo_object(api.get_user(friendid))
        users_graph.add_node(friendid, userinfo=friend_user)
      users_graph.add_edge(user.id, friendid)
    for followerid in user.followers:
      if followerid not in users_graph.nodes:
        follower_user = next((n_user for n_user in users if n_user.id == followerid), None)
        if follower_user is None:
          follower_user = utils.tweepy_user_to_userinfo_object(api.get_user(followerid))
        users_graph.add_node(followerid, userinfo=follower_user)
      users_graph.add_edge(followerid, user.id)

  return users_graph

def assign_top_level_categories(users_graph, top_level_userinfo_objects):

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
  for top_level_userinfo in top_level_userinfo_objects:
    userinfo_tags = next((x[1] for x in top_level_reference_accounts if x[0] == top_level_userinfo_objects.handle.lower()), None)
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

  return users_graph

#endregion

#region Part 3: Categorization & Propagation

def propagate_tags(users_graph):

  users_graph_copy = copy.copy(users_graph)
  # https://stackoverflow.com/questions/21627457/looping-through-nodes-and-extract-attributes-in-networkx
  # First pass, the order matters, need to figure out when it shouldn't
  for user_id, user_attributes in users_graph.nodes(data=True):
    # e.x (873588304690, {'userinfo': <classes.UserInfo object at 0x000002BB4E0B2390>})
    # user_attributes is all the attributes assigned to the node
    userinfo_object = user_attributes['userinfo']
    current_user_friends_tags = []
    for friend_id in userinfo_object.friends:
      friend_tags = tags_from_friend(users_graph_copy, friend_id)
      current_user_friends_tags.extend(friend_tags)
    userinfo_object.tags = list(set(userinfo_object.tags + current_user_friends_tags))
  
  return users_graph

def categorize_node(user_graph_node):

  '''
  Given a graph node repsenting a UserInfo object, classify by keywords based on its friends.

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

#region Helpers

def tags_from_friend(users_graph, friend_id):

  return users_graph.nodes[friend_id]['userinfo'].tags

def get_breakdown_by_category(reference_accounts):

  TOP_ACCOUNTS_PER_CATEGORY = {}
  for handle in reference_accounts.keys():
    # The first tag should be the primary tag
    account_primary_tag = reference_accounts[handle]['tags'][0]
    account_num_followers = api.get_users(handle)._json['followers_count']
    if account_primary_tag not in TOP_ACCOUNTS_PER_CATEGORY:
      TOP_ACCOUNTS_PER_CATEGORY[account_primary_tag] = [(handle, account_num_followers)]
    else:
      TOP_ACCOUNTS_PER_CATEGORY[account_primary_tag].append((handle, account_num_followers))

  for category, category_data in TOP_ACCOUNTS_PER_CATEGORY.items():
    TOP_ACCOUNTS_PER_CATEGORY[category] = sorted(category_data, key=lambda tup: tup[1], reverse=True)

  return TOP_ACCOUNTS_PER_CATEGORY

#endregion

if __name__ == '__main__':
  # x = main()
  # y = get_top_users_by_followers(TOP_LEVEL_CATEGORIES, TOP_ACCOUNTS_BY_CATEGORIES)
  # print(y)
  # v = get_users(y)
  # print(v)
  # m = utils.hydrate_userinfo_objects_from_db()
  # print(m)
  m = users_to_graph(utils.generate_sample_userinfo(5))
  for info, node_a in m.nodes(data=True):
    node_a['userinfo'].tags = fake.words(nb=1, ext_word_list=None)
    print(node_a['userinfo'])
  m = propagate_tags(m)
  for info, node_a in m.nodes(data=True):
    print(info, node_a['userinfo'].tags)
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