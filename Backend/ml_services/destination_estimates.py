"""Transparent monthly destination estimates from static profile facts and seasonal rules."""
import re

from ml_services.destinations import destination_profiles
from ml_services.tourism import MONTHS, _tourism_rows
from ml_services.city_directory import normalize_city
from ml_services.destination_models import temperature_center, crowd_category

MONTH_NUMBER = {name: index + 1 for index, name in enumerate(MONTHS)}
NORTH_OFFSETS = [-5, -3, 0, 4, 7, 8, 6, 5, 3, 0, -3, -5]
SOUTH_OFFSETS = [-1, 0, 2, 4, 4, 2, 1, 1, 1, 0, -1, -1]
OTHER_OFFSETS = [-3, -2, 1, 4, 6, 6, 4, 4, 2, 0, -2, -3]
CROWD_BASE = {"low": 25, "moderate": 48, "medium": 48, "high": 70, "very high": 88}


def _temperature_range(value):
    """Parse a two-value climate range while preserving negative temperatures."""
    text = str(value or "").strip().replace("−", "-").replace("–", "-").replace("—", "-")
    # A separator is a hyphen surrounded by optional whitespace; a leading hyphen
    # belongs to a signed number (for example, -15--5).
    match = re.fullmatch(r"\s*(-?\d+(?:\.\d+)?)\s*-\s*(-?\d+(?:\.\d+)?)\s*(?:°?\s*C)?\s*", text, re.I)
    if not match:
        return None
    low, high = map(float, match.groups())
    if high < low:
        low, high = high, low
    return low, high


def _crowd_bucket(score):
    if score < 36:
        return "Low"
    if score < 61:
        return "Moderate"
    if score < 81:
        return "High"
    return "Very High"


def _monthly_demand_pattern(state, month):
    rows = _tourism_rows()
    if not rows:
        return None
    state_key = normalize_city(state)
    state_rows = [row for row in rows if normalize_city(row["state"]) == state_key]
    chosen = state_rows or rows
    month_name = MONTHS[month - 1]
    current = [row["total_tourists"] for row in chosen if row["month"] == month_name]
    monthly = {}
    for name in MONTHS:
        values = [row["total_tourists"] for row in chosen if row["month"] == name]
        if values:
            monthly[name] = sum(values) / len(values)
    if not current or not monthly:
        return None
    mean = sum(monthly.values()) / len(monthly)
    if mean <= 0:
        return None
    return {"relative_index": round((sum(current) / len(current)) / mean * 100, 1),
            "scope": "state" if state_rows else "all supplied states",
            "state": state_rows[0]["state"] if state_rows else None,
            "month_observations": len(current), "baseline_months": len(monthly)}


def _lookup_destination(destination_id):
    profiles = destination_profiles()["profiles"]
    return next((row for row in profiles if str(row.get("id")) == str(destination_id)), None)


def estimate_destination_month(destination_id, month):
    if isinstance(month, bool) or not isinstance(month, int) or not 1 <= month <= 12:
        raise ValueError("month must be an integer from 1 to 12.")
    profile = _lookup_destination(destination_id)
    if profile is None:
        raise LookupError("Destination profile was not found.")

    region = normalize_city(profile.get("region"))
    offsets = NORTH_OFFSETS if region == "north" else SOUTH_OFFSETS if region == "south" else OTHER_OFFSETS
    baseline_temp = _temperature_range(profile.get("temperature_range_c"))
    temperature = None
    if baseline_temp:
        offset = offsets[month - 1]
        model_center = temperature_center(profile, month, baseline_temp)
        center = round(model_center if model_center is not None else
                       (baseline_temp[0] + baseline_temp[1]) / 2 + offset, 1)
        estimated_range = [round(center - 1.4, 1), round(center + 1.4, 1)]
        temperature = {"kind": "random_forest_proxy_estimate" if model_center is not None else "rules_based_approximate_estimate", "unit": "°C",
                       "range": estimated_range, "central_estimate": center,
                       "range_label": "proxy-model temperature estimate; not daily weather extremes" if model_center is not None else "approximate monthly climate estimate; not daily weather extremes",
                       "reference_range": [baseline_temp[0], baseline_temp[1]], "monthly_adjustment": offset,
                       "method": "Random Forest trained on proxy labels from reference-range midpoint and regional month adjustments. The band is at most 3?C; this is not observed weather or a validated forecast." if model_center is not None else "Fallback: reference-range midpoint plus regional month adjustment; the band is at most 3?C and is not observed weather or a validated forecast."}
    else:
        temperature = {"kind": "unavailable", "range": None, "unit": "°C",
                       "reason": "No parseable destination reference temperature range is available."}

    pattern = _monthly_demand_pattern(profile.get("state"), month)
    base = CROWD_BASE.get(str(profile.get("crowd_level") or "").strip().casefold())
    crowd = None
    if pattern and base is not None:
        # The no-year workbook supports seasonal ratios only, not dated forecasts.
        score = max(0, min(100, base + (pattern["relative_index"] - 100) * 0.22))
        predicted_level = crowd_category(profile, month, pattern["relative_index"])
        fallback_level = {"Moderate": "Medium", "Very High": "High"}.get(_crowd_bucket(score), _crowd_bucket(score))
        crowd = {"kind": "logistic_regression_proxy_classification" if predicted_level else "rules_based_approximate_estimate", "level": predicted_level or fallback_level,
                 "relative_demand_index": round(score, 1), "unit": "index points (0–100)",
                 "source_month_index": pattern["relative_index"], "source_scope": pattern["scope"],
                 "method": "Logistic Regression predicts a three-class proxy category from destination crowd reference, metadata, selected month, and year-free monthly tourism index. The index is input context, not a probability; labels are not verified counts or a future forecast." if predicted_level else "Fallback: destination crowd reference and year-free monthly profile produce a seasonal estimate mapped to Low, Medium, or High."}
    else:
        reason = "Destination crowd reference label is missing." if base is None else "Historical monthly tourism pattern is unavailable."
        crowd = {"kind": "unavailable", "level": None, "unit": "index points (0–100)", "reason": reason}
    month_tokens = [part.strip().casefold()[:3] for part in (profile.get("months_best_for") or "").split("-")]
    month_abbr = [name[:3].casefold() for name in MONTHS]
    within_best_months = None
    if len(month_tokens) == 2 and all(token in month_abbr for token in month_tokens):
        start, end = (month_abbr.index(token) + 1 for token in month_tokens)
        within_best_months = start <= month <= end if start <= end else month >= start or month <= end
    return {"destination": {"id": profile["id"], "name": profile["name"], "state": profile.get("state")},
            "selected_month": {"number": month, "name": MONTHS[month - 1], "within_best_months": within_best_months},
            "temperature": temperature, "crowd": crowd,
            "limitations": ["The historical workbook has no year and cannot support a genuine future forecast.",
                            "Temperature and crowd training labels are proxies derived from metadata and seasonal rules; evaluation measures agreement with those proxies, not real-world forecast accuracy."]}
