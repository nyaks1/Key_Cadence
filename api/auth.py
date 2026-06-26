import os

from fastapi import HTTPException, Security
from fastapi.security.api_key import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(key: str = Security(api_key_header)):
    if key is None:
        raise HTTPException(status_code=403, detail="Missing X-API-Key header")
    valid_keys = os.getenv("VALID_API_KEYS", "").split(",")
    if key not in valid_keys:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return key
