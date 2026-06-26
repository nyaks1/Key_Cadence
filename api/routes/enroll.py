from fastapi import APIRouter, Depends, HTTPException

from api.auth import verify_api_key
from api.models.schemas import EnrollRequest, EnrollResponse
from api.core.scoring import analyze_keystroke_sample
from api.core.storage import delete_baseline, save_baseline

router = APIRouter()


@router.post("/enroll", response_model=EnrollResponse)
async def enroll_user(request: EnrollRequest, key=Depends(verify_api_key)):
    mean, std = analyze_keystroke_sample(request.keystroke_timings)
    save_baseline(request.user_id, mean, std, len(request.keystroke_timings))
    return EnrollResponse(
        user_id=request.user_id,
        status="enrolled",
        samples_recorded=len(request.keystroke_timings),
    )


@router.delete("/user/{user_id}")
async def delete_user(user_id: str, key=Depends(verify_api_key)):
    deleted = delete_baseline(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "deleted", "user_id": user_id}
