import os
import json
import httpx
from typing import Tuple


GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"


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

    prompt = (
        "You are a behavioral biometric security analyst. Analyze this keystroke "
        "authentication attempt and decide the access level.\n\n"
        f"Match confidence: {confidence}\n"
        f"Z-scores per keystroke interval: {json.dumps([round(z, 4) for z in z_scores])}\n"
        f"Mean absolute z-score: {round(sum(abs(z) for z in z_scores) / len(z_scores), 4) if z_scores else 0}\n\n"
        "Respond with ONLY a JSON object, no other text:\n"
        '{"decision": "ALLOW"|"STEP_UP"|"BLOCK", "reason": "<one sentence>"}\n\n'
        "Rules:\n"
        "- ALLOW: confidence >= 0.7, pattern is consistent\n"
        "- STEP_UP: confidence 0.4-0.7, some variance detected\n"
        "- BLOCK: confidence < 0.4 or suspicious outlier z-scores (|z| > 3)\n"
    )

    try:
        resp = httpx.post(
            GEMINI_URL,
            headers={"x-goog-api-key": api_key},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=10,
        )
        resp.raise_for_status()
        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        result = json.loads(text)
        decision = result.get("decision", "STEP_UP")
        reason = result.get("reason", "Gemini analysis.")
        if decision not in ("ALLOW", "STEP_UP", "BLOCK"):
            return get_risk_decision(confidence)
        return decision, reason
    except Exception:
        return get_risk_decision(confidence)
