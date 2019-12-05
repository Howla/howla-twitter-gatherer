import unittest
import json
import pymongo
import networkx as nx
import random

import main
import utils

class TestDataGatheringMethods(unittest.TestCase):

  '''
  Tests to run:

  Gathering Data:
  =====

  Setup: 
    - Connect to MongoDB
    - Create DB instance
    - Create a sample collection

  1. get_top_users_by_followers:
    - Create sample reference_accounts and a category_list
    - Assert that the output is consistent with the inputs, in terms of ordering and counts
  2. get_users:
    - Create top_users_by_category with sample Twitter accounts
    - Assert that after running the algorithm, the correct UserInfo objects are stored in the database

  Teardown:
    - Foreach collection, assert current number of items
    - Delete all items within all collections
    - Assert that all collections and objects within collections have been deleted
  
  '''

  @classmethod
  def setUpClass(cls):

    with open('credentials.json') as credentials_file:
      credentials = json.load(credentials_file)

    client = pymongo.MongoClient('mongodb+srv://' + credentials['mongodbuser'] + ':' + credentials['mongodbpassword'] + '@howla-sandbox-fdsr1.mongodb.net/test?retryWrites=true&w=majority')
    db = client.data_gathering_test
    test_collection = db.test_collection
    cls._client = client
    cls._db = db
    cls._collection = test_collection

    TEST_CATEGORY_LIST = [
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

    TEST_REFERENCE_ACCOUNTS = [
      ('ohitsdoh', ['politics']),
      ('_spe', ['technology']),
      ('_pxlu', ['sports']),
      ('suzannerivecca', ['media']),
      ('TLDoublelift', ['entertainment']),
      ('pskills43', ['sports']),
      ('Pontifex', ['religion']),
      ('McDonalds', ['food']),
      ('ChickfilA', ['food']),
      ('lonelyplanet', ['travel']),
      ('cbc', ['media']),
      ('JustinTrudeau', ['politics']),
      ('Dior', ['fashion']),
      ('Apple', ['technology']),
      ('NASA', ['science']),
      ('WHO', ['science'])
    ]

    cls._CATEGORY_LIST = TEST_CATEGORY_LIST
    cls._REFERENCE_ACCOUNTS = TEST_REFERENCE_ACCOUNTS
    
  def test_db_collection_insert(self):
    test_document = {
      "author": "test_author",
      "body": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla vitae maximus nunc. Etiam iaculis erat ac orci sodales, at pellentesque purus ultrices. Fusce in cursus eros. Suspendisse dui nunc, ornare a sapien vitae, elementum pellentesque sem. In gravida mauris in interdum feugiat. Donec quis bibendum metus. Nam et gravida tellus, eget tincidunt tortor. Nunc fringilla, lorem fringilla cursus suscipit, tellus orci pretium elit, ac bibendum mauris sem sed lorem."
    }
    self._collection.insert_one(test_document)
    self.assertIn('data_gathering_test', self._client.list_database_names())
    self.assertIn('test_collection', self._db.list_collection_names())

  #region main._get_top_users_by_followers
  
  def test_test_get_top_users_by_followers_empty(self):
    RESULT_OUTPUT = main.get_top_users_by_followers([], self._REFERENCE_ACCOUNTS)
    self.assertEqual({}, RESULT_OUTPUT)

  def test_test_get_top_users_by_followers_all(self): 
    RESULT_OUTPUT = main.get_top_users_by_followers(self._CATEGORY_LIST, self._REFERENCE_ACCOUNTS)
    OUTPUT_ACCOUNTS = [item[0] for value in RESULT_OUTPUT.values() for item in value]
    ACCOUNTS_IN = [item[0] for item in self._REFERENCE_ACCOUNTS]
    self.assertTrue(
      all(
        elem in OUTPUT_ACCOUNTS for elem in ACCOUNTS_IN
      )
    )
  
  def test_get_top_users_by_followers_included_categories(self):
    RESULT_OUTPUT = main.get_top_users_by_followers(self._CATEGORY_LIST[:5], self._REFERENCE_ACCOUNTS)
    OUTPUT_ACCOUNTS = [item[0] for value in RESULT_OUTPUT.values() for item in value]
    # print(OUTPUT_ACCOUNTS)
    ACCOUNTS_IN = ['ohitsdoh', '_pxlu', 'suzannerivecca', 'TLDoublelift', 'pskills43', 'McDonalds', 'ChickfilA', 'cbc', 'JustinTrudeau']
    self.assertTrue(
      all(
        elem in OUTPUT_ACCOUNTS for elem in ACCOUNTS_IN
      )
    )

  def test_get_top_users_by_followers_excluded_categories(self):
    RESULT_OUTPUT = main.get_top_users_by_followers(self._CATEGORY_LIST[:5], self._REFERENCE_ACCOUNTS)
    # print(RESULT_OUTPUT)
    ACCOUNTS_NOT_IN = ['_spe', 'Pontifex', 'lonelyplanet', 'Apple', 'Dior', 'NASA', 'WHO']
    self.assertFalse(
      any(
        elem in RESULT_OUTPUT for elem in ACCOUNTS_NOT_IN
      )
    )

  #endregion

  #region main.users_to_graph

  def test_users_to_graph_empty(self):
    EMPTY_GRAPH = nx.DiGraph()
    self.assertEqual(len(EMPTY_GRAPH.nodes), len(main.users_to_graph([]).nodes))

  def test_users_to_graph_number_of_nodes_created(self):
    NUMBER_OF_TEST_USERS = random.randint(5, 20)
    TEST_USERINFO_LIST = utils.generate_sample_userinfo(NUMBER_OF_TEST_USERS)
    TEST_USERS_GRAPH = main.users_to_graph(TEST_USERINFO_LIST)
    self.assertTrue(NUMBER_OF_TEST_USERS, len(TEST_USERS_GRAPH.nodes))

  def test_users_to_graph_correct_users_inserted(self):
    TEST_USERINFO_LIST = utils.generate_sample_userinfo(20)
    TEST_USER_ID_LIST = [userinfo.id for userinfo in TEST_USERINFO_LIST]
    TEST_USERS_GRAPH = main.users_to_graph(TEST_USERINFO_LIST)
    self.assertTrue(
      any(
        elem in TEST_USERS_GRAPH.nodes for elem in TEST_USER_ID_LIST
      )
    )

  def test_users_to_graph_correct_edges_created(self):
    TEST_USERINFO_LIST = utils.generate_sample_userinfo(20)
    TEST_USERS_GRAPH = main.users_to_graph(TEST_USERINFO_LIST)
    for userinfo in TEST_USERINFO_LIST:
      for follower_id in userinfo.followers:
        self.assertTrue(TEST_USERS_GRAPH.has_edge(follower_id, userinfo.id))
      for friend_id in userinfo.friends:
        self.assertTrue(TEST_USERS_GRAPH.has_edge(userinfo.id, friend_id))

  #endregion

  @unittest.skip("demonstrating skipping")
  def test_check_delete_db(self):
    pass

  @classmethod
  def tearDownClass(cls):
    cls._client.close()

if __name__ == '__main__':
  unittest.main()