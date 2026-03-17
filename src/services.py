import uuid

from datetime import datetime
from src.db import scans_collection
from src.celery_app import celery_app
from src.log import get_api_logger

logger = get_api_logger()

def create_new_scan_task(username: str, email: str) -> dict:
    """Handles the business logic of creating a scan and queuing the task."""
    scan_id = str(uuid.uuid4())
    
    new_scan = {
        "scan_id": scan_id,
        "status": "pending",
        "created_at": datetime.utcnow(),
        "timestamp": datetime.utcnow(),
        "username_input": username,
        "email_input": email,
        "found_count": 0,
        "results": []
    }
    
    # 1. Save to Database
    scans_collection.insert_one(new_scan)
    logger.debug("Created scan record in database for scan_id: %s", scan_id)
    
    # 2. Queue the Celery Task
    # (Note: we import perform_scan locally here if needed to avoid circular imports, 
    # or just use celery_app.send_task)
    celery_app.send_task("perform_scan", args=[scan_id, username, email])
    logger.info("Queued scan task for scan_id: %s", scan_id)
    
    new_scan.pop("_id", None)
    return new_scan

def get_scan_by_id(scan_id: str) -> dict:
    """Fetches a scan from the database."""
    return scans_collection.find_one({"scan_id": scan_id}, {"_id": 0})

