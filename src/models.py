from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import List, Optional, Any, Dict
from datetime import datetime

# --- REQUEST MODEL ---
class ScanRequest(BaseModel):
    username: Optional[str] = Field(default=None)
    email: Optional[EmailStr] = Field(default=None)

    # This validator ensures the USER sends at least one.
    # It should ONLY run on the Request, not the Status.
    

class ScanResult(BaseModel):
    source: str       
    exists: bool
    url: Optional[str] = None 

class ScanStatus(BaseModel):
    scan_id: str
    status: str
    
    username_input: Optional[str] = None
    email_input: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    found_count: int = 0
    results: List[ScanResult] = []
    risk_score: int = 0       
    risk_level: str = "PENDING"
    scan_summary: Optional[str] = None