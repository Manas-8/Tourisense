"""Train and evaluate the experimental source-cost regressor.

Run from Backend with: ``python -m ml_services.train_models``.
Hotel cancellation and booking-volume experiments are not part of this workflow.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import dump
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from ml_services.supervised import ARTIFACTS, COST_MODEL_PATH

DATA = Path(__file__).resolve().parents[1] / "Data"
RANDOM_STATE = 42


def _chronological_split(frame, date_column, ratio=0.8):
    dates = sorted(frame[date_column].dropna().unique())
    if len(dates) < 5:
        raise ValueError(f"Not enough distinct dates in {date_column} for holdout evaluation")
    test_start = dates[int(len(dates) * ratio)]
    train = frame[frame[date_column] < test_start]
    test = frame[frame[date_column] >= test_start]
    return train, test, pd.Timestamp(test_start)


def _regression_metrics(actual, predicted):
    mse = float(mean_squared_error(actual, predicted))
    return {
        "mae": round(float(mean_absolute_error(actual, predicted)), 3),
        "mse": round(mse, 3),
        "rmse": round(mse ** 0.5, 3),
        "r2": round(float(r2_score(actual, predicted)), 4) if len(actual) > 1 else None,
    }


def _trip_cost_report(save_artifact=True):
    path = DATA / "Travel And Tourism.csv"
    frame = pd.read_csv(path, encoding="utf-8-sig")
    frame["Booking_Date"] = pd.to_datetime(frame["Booking_Date"], errors="coerce")
    frame["Travel_Date"] = pd.to_datetime(frame["Travel_Date"], errors="coerce")
    frame["lead_days"] = (frame["Travel_Date"] - frame["Booking_Date"]).dt.days
    frame["travel_month"] = frame["Travel_Date"].dt.month
    frame["travel_dayofweek"] = frame["Travel_Date"].dt.dayofweek
    categorical = ["Destination_City", "Destination_Country", "Meal_Plan", "Transportation_Type"]
    numeric = ["Number_of_Travellers", "Number_of_Adults", "Number_of_Children", "Number_of_Rooms",
               "Number_of_Nights", "Hotel_Rating", "lead_days", "travel_month", "travel_dayofweek"]
    features = categorical + numeric
    target = "Total_Trip_Cost"
    if frame[features + [target, "Booking_Date"]].isna().any().any():
        raise ValueError("Travel cost data is missing required training inputs or target values")
    if (frame["lead_days"] < 0).any() or (frame[target] <= 0).any():
        raise ValueError("Travel cost data failed lead-time/positive-target validation")

    train, test, test_start = _chronological_split(frame.sort_values("Booking_Date"), "Booking_Date")
    baseline_prediction = np.repeat(float(train[target].median()), len(test))
    preprocessor = ColumnTransformer([
        ("categorical", Pipeline([("impute", SimpleImputer(strategy="most_frequent")),
                                  ("onehot", OneHotEncoder(handle_unknown="ignore"))]), categorical),
        ("numeric", SimpleImputer(strategy="median"), numeric),
    ])
    pipeline = Pipeline([("features", preprocessor),
                         ("model", RandomForestRegressor(n_estimators=200, max_depth=10,
                                                          min_samples_leaf=5, n_jobs=-1,
                                                          random_state=RANDOM_STATE))])
    pipeline.fit(train[features], train[target])
    prediction = pipeline.predict(test[features])
    baseline_metrics = _regression_metrics(test[target], baseline_prediction)
    model_metrics = _regression_metrics(test[target], prediction)
    result = {
        "kind": "experimental_trip_cost_regression", "source": path.name,
        "source_rows": len(frame),
        "target": "Total_Trip_Cost (source-reported total; currency and cost semantics undocumented)",
        "features": features,
        "excluded": ["Booking_ID", "Customer_ID", "Customer_Name", "Booking_Status", "Cancellation_Status",
                     "Cancellation_Reason", "Discount_Amount", "Customer_Rating", "Customer_Review_Comment",
                     "Return_Date"],
        "split": "Chronological holdout: earliest 80% of distinct Booking_Date values train, latest 20% test.",
        "test_start": test_start.date().isoformat(), "train_rows": len(train), "test_rows": len(test),
        "baseline": {"name": "training_median", **baseline_metrics},
        "model": {"name": "random_forest_regressor", **model_metrics},
        "target_median": float(frame[target].median()), "target_p99": float(frame[target].quantile(.99)),
        "currency": None,
        "provenance_note": "Dataset provenance is unverified; do not treat this as an INR quote.",
        "limitation": "Output is in source cost units. Currency and quoted/paid cost semantics are unknown.",
    }
    can_save = save_artifact and model_metrics["mae"] < baseline_metrics["mae"]
    if can_save:
        ARTIFACTS.mkdir(parents=True, exist_ok=True)
        dump({"pipeline": pipeline, "features": features, "model_name": result["model"]["name"],
              "evaluation": {"test_start": result["test_start"], "test_rows": result["test_rows"],
                             "mae": model_metrics["mae"], "rmse": model_metrics["rmse"],
                             "baseline_mae": baseline_metrics["mae"], "baseline_rmse": baseline_metrics["rmse"]}},
             COST_MODEL_PATH)
        result["artifact_saved"] = True
    else:
        result["artifact_saved"] = False
        result["artifact_write_skipped"] = not save_artifact
    print("\n[trip cost | diagnostic, chronological Booking_Date split]")
    print(json.dumps(result, indent=2))
    return result


def main():
    reports = {"trip_cost": _trip_cost_report()}
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS / "evaluation.json").write_text(json.dumps(reports, indent=2), encoding="utf-8")
    print(f"\nWrote evaluation report: {ARTIFACTS / 'evaluation.json'}")
    print(f"Trip-cost artifact available: {COST_MODEL_PATH.is_file()}")


if __name__ == "__main__":
    main()
