import os
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

load_dotenv()

# 2. Get the URI from the environment
mongo_uri = os.getenv("MONGO_URI")

if not mongo_uri:
    raise ValueError("No MONGO_URI found in .env file")

# Create a new client and connect to the server
client = MongoClient(mongo_uri, server_api=ServerApi('1'))

db = client["shadowlink"]
scans_collection = db["scans_collection"]

