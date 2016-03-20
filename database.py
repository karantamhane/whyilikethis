# from models import *
from pymongo import *
# import json

# DB methods take in any object that has a class variable "collection" which references
# the collection name where it is stored in the database

class Database:
    def __init__(self):
        self.client = MongoClient()
        # if drop_db:
        #     self.client.drop_database('whyilikethis')
        # TODO: Look into configuring databases if creating anew
        self.db = self.client.whyilikethis

    def get_collection(self, collection):
        return self.db[collection]

    def add_entry(self, entry):
        # Add an entry
        table = self.db[entry.__class__.collection]
        return table.insert_one(entry.info)

    def update_entry(self, query, entry):
        # Update entry
        table = self.db[entry.__class__.collection]
        # print query, entry, entry.info
        return table.update_one(query,{'$set': entry.info})

    def replace_entry(self, query, entry):
        # Update entry
        table = self.db[entry.__class__.collection]
        # print query, entry, entry.info
        return table.replace_one(query, entry.info)

    def find_entry(self, collection, query):
        # Find entry
        table = self.db[collection]
        return table.find_one(query)

    def delete_entry(self, collection, query):
        # Delete entry
        table = self.db[collection]
        return table.delete_one(query)

    def close(self):
        self.client.close()

