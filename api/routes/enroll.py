from fastapi import APIRouter
from api.models.schemas import EnrollRequest, EnrollResponse
from api.core.scoring import analyze_keystroke_sample
from api.core.storage import save_baseline

router = APIRouter()


@router.post("/enroll", response_model=EnrollResponse)
async def enroll_user(request: EnrollRequest):
    mean, std = analyze_keystroke_sample(request.keystroke_timings)
    save_baseline(request.user_id, mean, std, len(request.keystroke_timings))
    return EnrollResponse(
        user_id=request.user_id,
        status="enrolled",
        samples_recorded=len(request.keystroke_timings)
    )
