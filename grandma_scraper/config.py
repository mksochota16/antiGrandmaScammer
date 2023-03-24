import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

try:
    MONGODB_URI = os.environ["MONGODB_URI"]
    MONGODB_PORT = int(os.environ["MONGODB_PORT"])
    MONGODB_DB_NAME = os.environ["MONGODB_DB_NAME"]
except KeyError as e:
    raise Exception(f"Missing required environment variable: {e}")

MONGO_CLIENT = MongoClient(MONGODB_URI, MONGODB_PORT)

SLEEP_TIME = 60 * 10 # 10 minutes