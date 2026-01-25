from fastapi import FastAPI, HTTPException
from scanners import perform_scan
from models import ScanRequest
import uuid
from datetime import datetime
from db import scans_collection

main = FastAPI()

@main.get("/")
def home():
    return {"status": "API is running"}

@main.post("/scan")
def start_scan(request:ScanRequest):
     scan_id=str(uuid.uuid4())

     new_scan = {
        "scan_id": scan_id,
        "status": "pending",
        "created_at": datetime.utcnow(),
        "timestamp": datetime.utcnow(),
        "username_input": request.username,
        "email_input": request.email,
        "found_count": 0,
        "results": []
    }
     try:
        scans_collection.insert_one(new_scan)
     except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create scan record")   
     perform_scan.delay(scan_id, request.username, request.email)
     new_scan.pop("_id", None)  # remove mongoDB internal ID from displayed response
     return new_scan   # basically new_scan

     
@main.get("/scan/{scan_id},response_model=ScanStatus")
def get_scan_status(scan_id:str):
     
    scan= scans_collection.find_one({"scan_id":scan_id},{"_id":0}) #{"_id": 0} is set as zero in order to hide this field from the output response
     
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan
