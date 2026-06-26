from pydantic import BaseModel
from typing import List


class EnrollRequest(BaseModel):
    user_id: str
    keystroke_timings: List[float]


class EnrollResponse(BaseModel):
    user_id: str
    status: str
    samples_recorded: int


class VerifyRequest(BaseModel):
    user_id: str
    keystroke_timings: List[float]


class VerifyResponse(BaseModel):
    user_id: str
    match_confidence: float
    decision: str
    reason: str
    flagged: bool
