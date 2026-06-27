import logging
import re

from fastapi import APIRouter, Depends, HTTPException

from api.auth import verify_api_key
from api.models.schemas import EnrollRequest, EnrollResponse
from api.core.scoring import analyze_keystroke_sample
from api.core.storage import delete_baseline, save_baseline

logger = logging.getLogger("keycadence.enroll")
router = APIRouter()

USER_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{3,64}$")


@router.post("/enroll", response_model=EnrollResponse)
async def enroll_user(request: EnrollRequest, key=Depends(verify_api_key)):
    """Enroll a user by recording their keystroke timing baseline.

    Analyzes the provided keystroke timings to compute a mean and standard
    deviation, then stores them as the user's baseline. Re-enrolling the
    same user_id overwrites the previous baseline.

    Args:
        request: EnrollRequest with user_id and keystroke_timings (min 5).
        key: Validated API key (injected by dependency).

    Returns:
        EnrollResponse with the user_id, enrollment status, and sample count.
    """
    mean, std = analyze_keystroke_sample(request.keystroke_timings)
    save_baseline(request.user_id, mean, std, len(request.keystroke_timings))
    logger.info("Enrolled user %s with %d samples", request.user_id, len(request.keystroke_timings))
    return EnrollResponse(
        user_id=request.user_id,
        status="enrolled",
        samples_recorded=len(request.keystroke_timings),
    )


@router.delete("/user/{user_id}")
async def delete_user(user_id: str, key=Depends(verify_api_key)):
    """Delete a user and their keystroke baseline (POPIA data erasure).

    Args:
        user_id: The user to delete.
        key: Validated API key (injected by dependency).

    Returns:
        JSON confirmation with the deleted user_id.

    Raises:
        HTTPException: 404 if the user does not exist.
        HTTPException: 422 if user_id format is invalid.
    """
    if not USER_ID_RE.match(user_id):
        raise HTTPException(status_code=422, detail="Invalid user_id format")
    deleted = delete_baseline(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    logger.info("Deleted user %s", user_id)
    return {"status": "deleted", "user_id": user_id}
