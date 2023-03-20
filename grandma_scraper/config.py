import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_PORT = int(os.getenv("MONGODB_PORT"))
MONGODB_DB_NAME= os.getenv("MONGODB_OLD_DB_NAME")
MONGO_CLIENT = MongoClient(MONGODB_URI, MONGODB_PORT)