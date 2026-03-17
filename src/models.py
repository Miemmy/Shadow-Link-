from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import List, Optional, Any, Dict
from datetime import datetime

# --- REQUEST MODEL ---
class ScanRequest(BaseModel):
    username: Optional[str] = Field(default=None, min_length=1, max_length=50)
    email: Optional[EmailStr] = Field(default=None)

    @model_validator(mode='after')
    def validate_input(self):
        if not self.username and not self.email:
            raise ValueError("Either username or email must be provided")
        return self

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