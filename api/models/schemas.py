import re
from pydantic import BaseModel, field_validator
from typing import List


class EnrollRequest(BaseModel):
    user_id: str
    keystroke_timings: List[float]

    @field_validator("user_id")
    @classmethod
    def sanitize_user_id(cls, v):
        if not re.match(r"^[a-zA-Z0-9_-]{3,64}$", v):
            raise ValueError("user_id must be 3-64 alphanumeric characters")
        return v

    @field_validator("keystroke_timings")
    @classmethod
    def must_have_samples(cls, v):
        if len(v) < 5:
            raise ValueError("Minimum 5 keystroke samples required")
        return v


class EnrollResponse(BaseModel):
    user_id: str
    status: str
    samples_recorded: int


class VerifyRequest(BaseModel):
    user_id: str
    keystroke_timings: List[float]

    @field_validator("user_id")
    @classmethod
    def sanitize_user_id(cls, v):
        if not re.match(r"^[a-zA-Z0-9_-]{3,64}$", v):
            raise ValueError("user_id must be 3-64 alphanumeric characters")
        return v

    @field_validator("keystroke_timings")
    @classmethod
    def must_have_samples(cls, v):
        if len(v) < 5:
            raise ValueError("Minimum 5 keystroke samples required")
        return v


class VerifyResponse(BaseModel):
    user_id: str
    match_confidence: float
    decision: str
    reason: str
    flagged: bool
