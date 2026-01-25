from pydantic import BaseModel, EmailStr, model_validator
from typing import List, Optional
from datetime import datetime

class ScanRequest(BaseModel):
    username: Optional[str]
    email: Optional[EmailStr]

#incase they give us nothing
    @model_validator(mode="after")
    def check_for_one(self):
        if not self.username and not self.email:
            raise ValueError("Either username or email must be provided.")
        return self

# a single site result (e.g. GitHub)
class ScanResult(BaseModel):
    source: str       # Matches "source" in scanners.py
    exists: bool
    url: Optional[str] = None  # Matches "url" in scanners.py

# The full status response
class ScanStatus(BaseModel):
    scan_id: str
    status: str
    found_count: int = 0  # Useful for the frontend to show a badge
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    results: List[ScanResult] = []

