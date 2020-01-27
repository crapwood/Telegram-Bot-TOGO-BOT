# YOUR BOT LOGIC/STORAGE/BACKEND FUNCTIONS HERE
from pprint import pprint
import pymongo
# from pymongo import MongoClient
import secrets

client = pymongo.MongoClient()
db = client.get_database('Cheetah')

users = db.get_collection('Users')


def add_user_to_db(person, changes):
    myquery = {"_id": person['chat_id']}
    users.update(myquery, {"$addToSet": {"places": changes}}, upsert=True)
