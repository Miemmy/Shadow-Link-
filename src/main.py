from fastapi import Depends, FastAPI, HTTPException
from scanners import perform_scan
from models import ScanRequest, ScanStatus, ScanResult
import uuid
from datetime import datetime
from db import scans_collection
import io
import csv
from fastapi.responses import Response

import redis.asyncio as redis
from fastapi_limiter import FastAPILimiter 
from fastapi_limiter.depends import RateLimiter

main = FastAPI()

@main.get("/")
def home():
    return {"status": "API is running"}

@main.on_event("startup")
async def startup():
    redis_connection= redis.from_url("redis://localhost:6379", encoding="utf-8", decode_responses=True)

    await FastAPILimiter.init(redis_connection)
    print ("Rate Limiter Connected to Redis")

@main.post("/scan" , 
           response_model=ScanStatus, 
           dependencies=[Depends(RateLimiter(times=3, seconds=60))])
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


@main.get("/scan/{scan_id}/report")
async def get_scan_report(scan_id:str):
    scan_doc= scans_collection.find_one({"scan_id":scan_id})
    
    if not scan_doc:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    if scan_doc.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Scan not completed yet")

    csv_file=io.StringIO()
    writer=csv.writer(csv_file)

    #header

    writer.writerow(["Shadow Link Report"])
    writer.writerow(["Target", scan_doc.get("username_input") or scan_doc.get("email_input")])
    writer.writerow(["Risk Level", scan_doc.get("risk_level", "UNKNOWN")])
    writer.writerow(["Risk Score", f"{scan_doc.get('risk_score', 0)}/100"])
    writer.writerow([])

    #table header
    writer.writerow(["Website", "Link", "Status"])

    for result in scan_doc.get("results", []):
        writer.writerow([
            result.get("source", "UNKNOWN"),
            result.get("url", "N/A"),
            "Found" 
        ])

    file_content=csv_file.getvalue().encode("utf-8")

    file_name=f"Report_{scan_doc.get('scan_id')}.csv"

    return Response(
        content=file_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={file_name}"}
    )





