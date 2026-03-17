import os 
from fastapi import HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader
from dotenv import load_dotenv

api_key_header=APIKeyHeader(name="X-API-Key", auto_error=False)

SECRET_API_KEY=os.getenv("SECRET_API_KEY","Ffall_back_on_me_key")

def verify_api_key(api_key:str=Security(api_key_header)):
   if api_key != SECRET_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
        return api_key



