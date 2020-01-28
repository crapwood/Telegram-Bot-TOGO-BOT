# YOUR BOT LOGIC/STORAGE/BACKEND FUNCTIONS HERE
from pprint import pprint
import pymongo
# from pymongo import MongoClient
import secrets

client = pymongo.MongoClient()
db = client.get_database('Cheetah')

users = db.get_collection('Users')


def add_user_to_db(person, changes):
    my_query = {"_id": person['chat_id']}
    users.update(my_query, {"$addToSet": {"places": changes}}, upsert=True)


def get_places_from_db(id):
    place = db.get_collection("Users").find_one({"_id": id})['places']
    result = []
    for x in place:
        for y, z in x.items():
            print(z)
            result.append([z['name'], z['address']])
    return result


def remove_place_from_db(chat_id, to_remove):
    get_ind = to_remove.split("-")
    # print(get_ind[1])
    db.get_collection("Users").update({}, {"$unset": {f"places.{get_ind[1]}": 1}})
    db.get_collection("Users").update({}, {"$pull": {"places": None}})



