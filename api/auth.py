import hmac
import os

from fastapi import HTTPException, Security
from fastapi.security.api_key import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def _get_valid_keys() -> list[str]:
    """Parse VALID_API_KEYS env var, filtering empty strings from trailing commas."""
    raw = os.getenv("VALID_API_KEYS", "")
    return [k for k in raw.split(",") if k]


async def verify_api_key(key: str = Security(api_key_header)):
    """FastAPI dependency that validates the X-API-Key header.

    Uses constant-time comparison to prevent timing attacks. Rejects
    missing or invalid keys with 403.

    Args:
        key: The API key extracted from the X-API-Key header.

    Returns:
        The validated key string.

    Raises:
        HTTPException: 403 if the key is missing or not in the valid set.
    """
    if not key:
        raise HTTPException(status_code=403, detail="Missing X-API-Key header")
    valid_keys = _get_valid_keys()
    if not any(hmac.compare_digest(key, vk) for vk in valid_keys):
        raise HTTPException(status_code=403, detail="Invalid API key")
    return key
