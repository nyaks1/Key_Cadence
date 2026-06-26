import os
from typing import Tuple


def get_risk_decision(confidence: float) -> Tuple[str, str]:
    if confidence >= 0.7:
        return "ALLOW", "High confidence match. User typing pattern is consistent with baseline."
    elif confidence >= 0.4:
        return "STEP_UP", "Moderate confidence. Timing variance detected. Recommend secondary verification."
    else:
        return "BLOCK", "Low confidence match. Typing pattern significantly deviates from baseline. Potential unauthorized access."


def get_gemini_decision(confidence: float, z_scores: list) -> Tuple[str, str]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return get_risk_decision(confidence)
    return get_risk_decision(confidence)
