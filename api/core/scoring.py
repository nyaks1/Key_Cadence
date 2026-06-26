import numpy as np
from typing import List, Tuple


def calculate_z_scores(baseline_mean: float, baseline_std: float, sample: List[float]) -> List[float]:
    """Compute z-scores for each timing in the sample against the baseline.

    A z-score measures how many standard deviations a value is from the mean.
    Returns all zeros if baseline_std is 0 (no variance in the baseline).

    Args:
        baseline_mean: The mean keystroke timing from enrollment.
        baseline_std: The standard deviation from enrollment.
        sample: List of keystroke timing intervals to score.

    Returns:
        List of z-scores, one per input timing.
    """
    if baseline_std == 0:
        return [0.0] * len(sample)
    return [(x - baseline_mean) / baseline_std for x in sample]


def calculate_confidence(z_scores: List[float]) -> float:
    """Convert z-scores into a 0.0-1.0 confidence score.

    Takes the mean of absolute z-scores and maps it to a confidence value
    using the formula: confidence = max(0, 1 - mean_abs_z / 3).
    A mean absolute z-score of 0 maps to 1.0 (perfect match), 3+ maps to 0.0.

    Args:
        z_scores: List of z-scores from calculate_z_scores.

    Returns:
        Confidence score rounded to 4 decimal places.
    """
    abs_z = [abs(z) for z in z_scores]
    mean_abs_z = np.mean(abs_z)
    confidence = max(0.0, 1.0 - (mean_abs_z / 3.0))
    return round(confidence, 4)


def analyze_keystroke_sample(sample: List[float]) -> Tuple[float, float]:
    """Compute the mean and standard deviation of a keystroke timing sample.

    Used during enrollment to build a user's typing baseline.

    Args:
        sample: List of keystroke timing intervals in milliseconds.

    Returns:
        Tuple of (mean, standard deviation) as floats.
    """
    return float(np.mean(sample)), float(np.std(sample))
