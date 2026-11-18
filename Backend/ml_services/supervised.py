"""Loading and inference for reproducibly trained source-scale models."""
import json
from pathlib import Path

ARTIFACTS = Path(__file__).resolve().parents[1] / "artifacts"
REPORT_PATH = ARTIFACTS / "evaluation.json"
COST_MODEL_PATH = ARTIFACTS / "trip_cost.joblib"


def model_report():
    try:
        return json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def trip_cost_prediction(payload):
    if not COST_MODEL_PATH.is_file():
        raise FileNotFoundError("Trip cost model has not been trained.")
    from joblib import load
    import pandas as pd

    bundle = load(COST_MODEL_PATH)
    frame = pd.DataFrame([{key: payload[key] for key in bundle["features"]}])
    estimate = float(bundle["pipeline"].predict(frame)[0])
    return {
        "kind": "experimental_source_cost_estimate",
        "estimate": round(estimate, 2),
        "unit": "source cost units (currency not recorded)",
        "model": bundle["model_name"],
        "evaluation": bundle["evaluation"],
        "limitation": "The source has no currency field and its provenance and cost semantics are unverified. This is not a currency-denominated quote.",
    }
