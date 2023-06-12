import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

try:
    MONGODB_URI: str = os.environ["MONGODB_URI"]
    MONGODB_PORT: int = int(os.environ["MONGODB_PORT"])
    MONGODB_DB_NAME: str = os.environ["MONGODB_DB_NAME"]
    SKIP_CERT_DOMAINS_CHECK: bool = os.environ["SKIP_CERT_DOMAINS_CHECK"] == "True"
    CHROMEDRIVER_PATH: str = os.environ["CHROMEDRIVER_PATH"]
except KeyError as e:
    pass
    #raise Exception(f"Missing required environment variable: {e}")

MONGO_CLIENT: MongoClient = MongoClient(MONGODB_URI, MONGODB_PORT)

SLEEP_TIME = 60 * 10 # 10 minutes