import numpy as np
from typing import List, Tuple


def calculate_z_scores(baseline_mean: float, baseline_std: float, sample: List[float]) -> List[float]:
    if baseline_std == 0:
        return [0.0] * len(sample)
    return [(x - baseline_mean) / baseline_std for x in sample]


def calculate_confidence(z_scores: List[float]) -> float:
    abs_z = [abs(z) for z in z_scores]
    mean_abs_z = np.mean(abs_z)
    confidence = max(0.0, 1.0 - (mean_abs_z / 3.0))
    return round(confidence, 4)


def analyze_keystroke_sample(sample: List[float]) -> Tuple[float, float]:
    return float(np.mean(sample)), float(np.std(sample))
