import unittest
import json
import pymongo

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

  def test_db_collection_insert(self):
    test_document = {
      "author": "test_author",
      "body": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla vitae maximus nunc. Etiam iaculis erat ac orci sodales, at pellentesque purus ultrices. Fusce in cursus eros. Suspendisse dui nunc, ornare a sapien vitae, elementum pellentesque sem. In gravida mauris in interdum feugiat. Donec quis bibendum metus. Nam et gravida tellus, eget tincidunt tortor. Nunc fringilla, lorem fringilla cursus suscipit, tellus orci pretium elit, ac bibendum mauris sem sed lorem."
    }
    self._collection.insert_one(test_document)
    self.assertIn('data_gathering_test', self._client.list_database_names())
    self.assertIn('test_collection', self._db.list_collection_names())

  @unittest.skip("demonstrating skipping")
  def test_check_delete_db(self):
    pass

  @classmethod
  def tearDownClass(cls):
    cls._client.close()

if __name__ == '__main__':
  unittest.main()