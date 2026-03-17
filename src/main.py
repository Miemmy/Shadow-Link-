from fastapi import FastAPI, Request, HTTPException, status
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from src.models import ScanRequest, ScanStatus
from src.log import init_logging, get_api_logger
from src.services import create_new_scan_task, get_scan_by_id

# 1. Initialize FastAPI and Logger
main = FastAPI(title="ShadowLink API")
logger = get_api_logger()

# 2. Initialize the IP-based Rate Limiter
limiter = Limiter(key_func=get_remote_address)
main.state.limiter = limiter
main.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@main.on_event("startup")
async def startup():
    try:
        init_logging()
        logger.info("Starting ShadowLink API server (Public Mode with IP Rate Limiting)")
    except Exception as e:
        print(f"Failed to initialize logging: {e}")
        raise

@main.get("/")
def home():
    return {"status": "ShadowLink API is running"}

# 3. The Public POST Route (Protected by SlowAPI)
@main.post("/scan", response_model=ScanStatus)
@limiter.limit("5/minute")
def start_scan(request: Request, payload: ScanRequest):
    # The 'request' parameter is strictly here so SlowAPI can track the user's IP
    
    if not payload.username and not payload.email:
        logger.warning("Scan rejected: Neither username nor email provided")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Either username or email must be provided"
        )
    
    try:
        # Hand off to the Kitchen (services.py)
        new_scan = create_new_scan_task(payload.username, payload.email)
        return new_scan
    except Exception as e:
        logger.error("Unexpected error in start_scan: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Failed to start scan"
        )

# 4. The GET Route
@main.get("/scan/{scan_id}", response_model=ScanStatus)
@limiter.limit("20/minute") 
def get_scan_status(request: Request, scan_id: str):
    scan = get_scan_by_id(scan_id)
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Scan '{scan_id}' not found"
        )
    return scan

