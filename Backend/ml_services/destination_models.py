"""Load notebook-trained, proxy-label destination models once per process."""
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd

ARTIFACTS = Path(__file__).resolve().parents[1] / "artifacts"


@lru_cache(maxsize=2)
def _load(filename):
    path = ARTIFACTS / filename
    if not path.is_file():
        return None
    try:
        return joblib.load(path)
    except Exception:
        return None


def destination_model_status():
    return {
        "temperature_model_available": _load("destination_temperature_rf.joblib") is not None,
        "crowd_model_available": _load("destination_crowd_logistic.joblib") is not None,
        "labels": "proxy targets derived from destination metadata and seasonal rules",
    }


def temperature_center(profile, month, reference_range):
    model = _load("destination_temperature_rf.joblib")
    if model is None:
        return None
    low, high = reference_range
    region = str(profile.get("region") or "other").strip().casefold()
    row = pd.DataFrame([{"reference_low_c": low, "reference_high_c": high,
                         "region_group": region if region in {"north", "south"} else "other",
                         "month": month}])
    try:
        return float(model.predict(row)[0])
    except Exception:
        return None


def crowd_category(profile, month, relative_month_index):
    model = _load("destination_crowd_logistic.joblib")
    if model is None:
        return None
    try:
        row = pd.DataFrame([{
            "crowd_reference": str(profile.get("crowd_level") or "Unknown").strip().casefold(),
            "category": str(profile.get("category") or "Unknown"),
            "region": str(profile.get("region") or "Unknown"),
            "budget": float(profile["budget_inr"]),
            "duration_days": float(profile["duration_days"]),
            "month": month,
            "relative_month_index": relative_month_index,
        }])
        prediction = str(model.predict(row)[0])
    except Exception:
        return None
    return prediction if prediction in {"Low", "Medium", "High"} else None
