import json
import os
from pathlib import Path
from typing import Optional, Tuple

STORAGE_PATH = os.getenv("STORAGE_PATH", "data/baselines")


def get_user_path(user_id: str) -> Path:
    return Path(STORAGE_PATH) / f"{user_id}.json"


def save_baseline(user_id: str, mean: float, std: float, samples_count: int) -> None:
    path = get_user_path(user_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "user_id": user_id,
        "mean": mean,
        "std": std,
        "samples_count": samples_count
    }
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def load_baseline(user_id: str) -> Optional[Tuple[float, float, int]]:
    path = get_user_path(user_id)
    if not path.exists():
        return None
    with open(path, "r") as f:
        data = json.load(f)
    return data["mean"], data["std"], data["samples_count"]
