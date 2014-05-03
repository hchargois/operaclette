#!/usr/bin/env python2

from pymongo import MongoClient
import code

MONGO_DBNAME = "operaclette"
MONGO_URL = "mongodb://localhost/"

db = MongoClient(MONGO_URL)[MONGO_DBNAME]
code.interact(banner="You can interact with the database through the 'db' object", local=locals())
