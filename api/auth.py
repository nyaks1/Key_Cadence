import os

from fastapi import HTTPException, Security
from fastapi.security.api_key import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(key: str = Security(api_key_header)):
    """FastAPI dependency that validates the X-API-Key header.

    Checks the provided key against the comma-separated VALID_API_KEYS
    environment variable. Rejects missing or invalid keys with 403.

    Args:
        key: The API key extracted from the X-API-Key header.

    Returns:
        The validated key string.

    Raises:
        HTTPException: 403 if the key is missing or not in the valid set.
    """
    if key is None:
        raise HTTPException(status_code=403, detail="Missing X-API-Key header")
    valid_keys = os.getenv("VALID_API_KEYS", "").split(",")
    if key not in valid_keys:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return key
