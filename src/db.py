import os
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import ConnectionFailure, ConfigurationError, OperationFailure
from src.log import get_db_logger

load_dotenv()

logger = get_db_logger()

# Get the URI from the environment
mongo_uri = os.getenv("MONGO_URI")

if not mongo_uri:
    logger.error("MONGO_URI not found in environment variables")
    raise ValueError("No MONGO_URI found in .env file")

try:
    # Create a new client and connect to the server
    client = MongoClient(mongo_uri, server_api=ServerApi('1'))
    
    # Test the connection
    client.admin.command('ping')
    logger.info("Successfully connected to MongoDB")
    
except ConnectionFailure as e:
    logger.error("Failed to connect to MongoDB: %s", str(e))
    raise ConnectionError(f"MongoDB connection failed: {str(e)}")
except ConfigurationError as e:
    logger.error("MongoDB configuration error: %s", str(e))
    raise ValueError(f"MongoDB configuration error: {str(e)}")
except Exception as e:
    logger.error("Unexpected error connecting to MongoDB: %s", str(e))
    raise RuntimeError(f"Unexpected database error: {str(e)}")

try:
    db = client["shadowlink"]
    scans_collection = db["scans_collection"]
    
    # Create index for better performance
    scans_collection.create_index("scan_id", unique=True)
    scans_collection.create_index("created_at")
    scans_collection.create_index("status")
    logger.info("Database collections and indexes initialized")
    
except OperationFailure as e:
    logger.error("Failed to initialize database collections: %s", str(e))
    raise RuntimeError(f"Database initialization failed: {str(e)}")
except Exception as e:
    logger.error("Unexpected error initializing database: %s", str(e))
    raise RuntimeError(f"Unexpected database initialization error: {str(e)}")

