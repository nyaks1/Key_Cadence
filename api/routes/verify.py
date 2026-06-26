from fastapi import APIRouter, Depends, HTTPException

from api.auth import verify_api_key
from api.models.schemas import VerifyRequest, VerifyResponse
from api.core.scoring import calculate_confidence, calculate_z_scores
from api.core.storage import load_baseline
from api.agent.risk_agent import get_gemini_decision

router = APIRouter()


@router.post("/verify", response_model=VerifyResponse)
async def verify_user(request: VerifyRequest, key=Depends(verify_api_key)):
    """Verify a user's identity by comparing keystroke timings to their baseline.

    Loads the stored baseline, computes z-scores for the new sample, derives
    a confidence score, and passes both to the Gemini risk agent for a final
    access decision.

    Args:
        request: VerifyRequest with user_id and keystroke_timings (min 5).
        key: Validated API key (injected by dependency).

    Returns:
        VerifyResponse with match_confidence, decision, reason, and flagged.

    Raises:
        HTTPException: 404 if the user has not been enrolled.
    """
    baseline = load_baseline(request.user_id)
    if baseline is None:
        raise HTTPException(status_code=404, detail="User not enrolled")

    baseline_mean, baseline_std, _ = baseline
    z_scores = calculate_z_scores(baseline_mean, baseline_std, request.keystroke_timings)
    confidence = calculate_confidence(z_scores)
    decision, reason = get_gemini_decision(confidence, z_scores)

    return VerifyResponse(
        user_id=request.user_id,
        match_confidence=confidence,
        decision=decision,
        reason=reason,
        flagged=decision != "ALLOW",
    )
