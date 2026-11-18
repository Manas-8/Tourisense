import csv
from pathlib import Path

from flask import Blueprint, jsonify, request
from auth_utils import require_roles

from ml_services.destinations import destination_profiles, recommend
from ml_services.experience import experience_summary
from ml_services.tourism import government_overview, tourism_summary
from ml_services.supervised import COST_MODEL_PATH, trip_cost_prediction
from ml_services.city_directory import food_directory, hotel_directory, travel_cost_match, directory_coverage, normalize_city
from ml_services.destination_estimates import estimate_destination_month
from ml_services.destination_models import destination_model_status
from ml_services.trip_estimator import estimate_trip_cost

ml_bp = Blueprint("ml_bp", __name__, url_prefix="/api/ml")


def _source_row_count(path):
    try:
        with path.open(encoding="utf-8-sig", newline="") as stream:
            return max(sum(1 for _ in csv.reader(stream)) - 1, 0)
    except OSError:
        return None


@ml_bp.get("/status")
def status():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1] / "Data"
    sources = {"destination_catalog": root / "Destinations.csv", "destination_metadata": root / "tourism_statistics.csv",
               "ratings": root / "destination_details.csv", "tourism_monthly": root / "user_visits.xlsx"}
    coverage = None
    rating_status = None
    tourism_status = None
    if sources["destination_catalog"].is_file() and sources["destination_metadata"].is_file():
        try:
            coverage = destination_profiles()["coverage"]
        except (OSError, KeyError, ValueError):
            coverage = None
    if sources["ratings"].is_file():
        try:
            rating_status = experience_summary()
        except (OSError, KeyError, ValueError):
            rating_status = None
    if sources["tourism_monthly"].is_file():
        try:
            tourism_status = government_overview()
        except (OSError, KeyError, ValueError):
            tourism_status = None
    new_data = Path(__file__).resolve().parents[1] / "Data"
    destination_models = destination_model_status()
    try:
        directory_status = directory_coverage()
    except (OSError, KeyError, ValueError):
        directory_status = None
    return jsonify(status="ok", data={"services": {
        "recommendations": {"available": coverage is not None, "method": "content_based_ranking", "coverage": coverage},
        "tourism": {"available": tourism_status is not None, "kind": "historical_monthly_summary", "future_forecast_available": False, "reason": "The workbook has no year field."},
        "experience": {"available": rating_status is not None, "kind": "observed_rating_summary", "trained_model_available": False},
        "trip_cost": {"available": True, "kind": "rules_based_approximate_estimate", "configuration_available": (Path(__file__).resolve().parents[1] / "config" / "trip_cost_rates.json").is_file()},
        "experimental_trip_cost_model": {"available": COST_MODEL_PATH.is_file(), "kind": "source_cost_regression; currency unknown"},
        "crowd": {"forecast_available": False, "seasonal_estimate_available": True, "trained_model_available": destination_models["crowd_model_available"], "kind": "logistic_regression_proxy_classification" if destination_models["crowd_model_available"] else "rules_based_approximate_estimate", "reason": "Three-class model uses proxy labels derived from source crowd metadata and year-free monthly tourism profiles; not verified crowd counts or a future forecast."},
        "temperature": {"forecast_available": False, "seasonal_estimate_available": True, "trained_model_available": destination_models["temperature_model_available"], "kind": "random_forest_proxy_estimate" if destination_models["temperature_model_available"] else "rules_based_approximate_estimate", "reason": "Model is trained on proxy labels derived from source temperature ranges and regional month adjustments; not observed weather or a validated forecast."},
        "directories": {"available": directory_status is not None, "kind": "source_directory"},
    }, "datasets": {
        "destination_catalog": {"path": "Backend/Data/Destinations.csv", "available": coverage is not None, "rows": coverage["catalog_rows"] if coverage else None, "meaning": "five named catalog concepts repeated under unique IDs"},
        "destination_metadata": {"path": "Backend/Data/tourism_statistics.csv", "available": coverage is not None, "rows": coverage["metadata_rows"] if coverage else None, "meaning": "destination attribute profiles"},
        "ratings": {"path": "Backend/Data/destination_details.csv", "available": rating_status is not None, "rows": rating_status["observations"] if rating_status else None, "meaning": "visit-level ratings; identifiers retained only for verified joins"},
        "tourism_monthly": {"path": "Backend/Data/user_visits.xlsx", "available": tourism_status is not None, "rows": tourism_status["coverage"]["records"] if tourism_status else None, "meaning": "state/month statistics with no year"},
        "hotel_bookings_2024": {"path": "Backend/Data/hotel_bookings_updated_2024.csv", "available": (new_data / "hotel_bookings_updated_2024.csv").is_file(), "rows": _source_row_count(new_data / "hotel_bookings_updated_2024.csv"), "meaning": "retained source for validation/reference only; no deployed booking prediction"},
        "travel_cost": {"path": "Backend/Data/Travel And Tourism.csv", "available": (new_data / "Travel And Tourism.csv").is_file(), "rows": _source_row_count(new_data / "Travel And Tourism.csv"), "meaning": "booking-level source-reported cost; currency unknown"},
        "hotel_directory": {"path": "Backend/Data/hotels.csv", "available": (new_data / "hotels.csv").is_file(), "rows": _source_row_count(new_data / "hotels.csv"), "meaning": "directory; operations/availability unverified"},
        "food_guide": {"path": "Backend/Data/india-tourism-food-dataset.csv", "available": (new_data / "india-tourism-food-dataset.csv").is_file(), "rows": _source_row_count(new_data / "india-tourism-food-dataset.csv"), "meaning": "city food and tourist spot guide"},
        "directory_coverage": directory_status,
    }})

@ml_bp.post("/recommendations")
def recommendations():
    payload = request.get_json(silent=True) or {}
    try:
        interests = payload.get("interests", [])
        if not isinstance(interests, list) or any(not isinstance(x, str) for x in interests):
            return jsonify(status="error", error="interests must be a list of strings."), 400
        if len(interests) > 20 or any(len(x) > 80 for x in interests):
            return jsonify(status="error", error="Provide at most 20 interests, each no longer than 80 characters."), 400
        for key in ("region", "season", "crowd"):
            value = payload.get(key)
            if value is not None and (not isinstance(value, str) or len(value) > 80):
                return jsonify(status="error", error=f"{key} must be a string no longer than 80 characters."), 400
        for key in ("budget", "duration_days"):
            value = payload.get(key)
            upper = 100000000 if key == "budget" else 60
            if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0 or value > upper):
                return jsonify(status="error", error=f"{key} must be between 0 and {upper}."), 400
        result = recommend(payload)
        return jsonify(status="ok", data=result)
    except ValueError as exc:
        return jsonify(status="error", error=str(exc)), 400
    except (OSError, KeyError) as exc:
        return jsonify(status="error", error="Destination source data could not be read."), 503


@ml_bp.get("/profiles")
def profiles():
    try:
        return jsonify(status="ok", data=destination_profiles())
    except (OSError, KeyError) as exc:
        return jsonify(status="error", error="Destination profile data could not be read."), 503


@ml_bp.get("/dashboard-overview")
@require_roles("admin")
def dashboard_overview():
    try:
        return jsonify(status="ok", data=government_overview())
    except (OSError, KeyError) as exc:
        return jsonify(status="error", error="Tourism source data could not be read."), 503


@ml_bp.get("/tourism")
def tourism():
    try:
        result = tourism_summary(request.args.get("state"), request.args.get("metric", "total_tourists"))
        return jsonify(status="ok", data=result)
    except ValueError as exc:
        return jsonify(status="error", error=str(exc)), 400
    except (OSError, KeyError) as exc:
        return jsonify(status="error", error="Tourism source data could not be read."), 503


@ml_bp.get("/experience")
@require_roles("admin")
def experience():
    try:
        return jsonify(status="ok", data=experience_summary())
    except OSError:
        return jsonify(status="error", error="Rating source data could not be read."), 503


@ml_bp.get("/model-status")
@require_roles("admin")
def model_status():
    return jsonify(status="ok", data={
        "trip_cost_model_available": COST_MODEL_PATH.is_file(),
        "crowd_prediction_available": destination_model_status()["crowd_model_available"],
        "monthly_crowd_estimate_available": True,
        "temperature_prediction_available": destination_model_status()["temperature_model_available"],
        "monthly_temperature_estimate_available": True,
        "occupancy_prediction_available": False,
        "limitations": [
            "No observed monthly temperatures are present; the deployed Random Forest is trained on proxy labels derived from metadata and seasonal adjustments.",
            "The hotel directory and booking records contain no reconciled room-capacity denominator for occupancy.",
            "Destination crowd categories are trained on proxy labels derived from metadata and year-free monthly tourism patterns; they are not verified crowd counts.",
            "The 2024 hotel-booking file is not used by a deployed cancellation, demand, occupancy, or crowd model.",
            "The travel-cost source has no currency field and appears synthetic or heavily anonymized.",
        ],
    })


@ml_bp.get("/destination-insights")
def destination_insights():
    destination_id = (request.args.get("destination_id") or "").strip()
    if not destination_id or len(destination_id) > 250:
        return jsonify(status="error", error="destination_id is required."), 400
    try:
        profiles = destination_profiles()["profiles"]
        profile = next((row for row in profiles if row["id"] == destination_id), None)
        if profile is None:
            return jsonify(status="error", error="Destination profile was not found."), 404
        direct_hotel = hotel_directory(profile["name"])
        direct_food = food_directory(profile["name"])
        if direct_hotel["count"] or direct_food["available"]:
            directory_city = profile["name"]
            city_basis = "destination name exact/normalized city match"
            hotels, food = direct_hotel, direct_food
        else:
            directory_city = profile["nearest_major_city"] or profile["name"]
            city_basis = "nearest_major_city metadata; directory listings may be in a different city"
            hotels, food = hotel_directory(directory_city), food_directory(directory_city)
        return jsonify(status="ok", data={
            "destination": profile,
            "reference_facts": {
                "best_season": profile.get("best_season"),
                "best_months": profile.get("months_best_for"),
                "temperature_range_c": profile.get("temperature_range_c"),
                "trip_duration_days": profile.get("duration_days"),
                "budget_inr_per_person": profile.get("budget_inr"),
                "typical_crowd_level": profile.get("crowd_level"),
                "source": "tourism_statistics.csv; reference metadata, not month-specific model output",
            },
            "directory": {"city": directory_city, "city_basis": city_basis,
                          "hotels": hotels, "food": food},
            "trip_cost_source_match": travel_cost_match(profile["name"], "India"),
        })
    except (OSError, KeyError, ValueError) as exc:
        return jsonify(status="error", error="Destination detail sources could not be read."), 503


@ml_bp.get("/destination-estimates")
def destination_estimates():
    destination_id = (request.args.get("destination_id") or "").strip()
    month_value = request.args.get("month")
    if not destination_id or len(destination_id) > 250:
        return jsonify(status="error", error="destination_id is required."), 400
    if month_value is None:
        return jsonify(status="error", error="month must be an integer from 1 to 12."), 400
    try:
        month = int(month_value)
    except (TypeError, ValueError) as exc:
        return jsonify(status="error", error="month must be an integer from 1 to 12."), 400
    try:
        result = estimate_destination_month(destination_id, month)
        return jsonify(status="ok", data=result)
    except ValueError as exc:
        return jsonify(status="error", error=str(exc)), 400
    except LookupError as exc:
        return jsonify(status="error", error=str(exc)), 404
    except (OSError, KeyError) as exc:
        return jsonify(status="error", error="Seasonal source data could not be read."), 503


@ml_bp.post("/trip-estimate")
def trip_estimate():
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return jsonify(status="error", error="A JSON object of trip estimate inputs is required."), 400
    try:
        result = estimate_trip_cost(payload.get("destination"), payload.get("transport_mode"),
                                    payload.get("travellers"), payload.get("duration_days"),
                                    payload.get("food_preference"), payload.get("rooms"))
        return jsonify(status="ok", data=result)
    except ValueError as exc:
        return jsonify(status="error", error=str(exc)), 400
    except (OSError, KeyError, TypeError) as exc:
        return jsonify(status="error", error="Trip estimate configuration or destination data is unavailable."), 503


@ml_bp.post("/trip-cost-estimate")
def trip_cost_estimate():
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return jsonify(status="error", error="A JSON object of experimental trip cost inputs is required."), 400
    required_strings = {"destination_city": 120, "destination_country": 100,
                        "meal_plan": 80, "transportation_type": 80}
    for key, max_len in required_strings.items():
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip() or len(value) > max_len:
            return jsonify(status="error", error=f"{key} is required and must be at most {max_len} characters."), 400
    numeric = {"travellers": (1, 15), "adults": (1, 15), "children": (0, 7), "rooms": (1, 8),
               "nights": (2, 10), "lead_days": (0, 500), "travel_month": (1, 12), "travel_dayofweek": (0, 6)}
    values = {}
    for key, (minimum, maximum) in numeric.items():
        value = payload.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
            return jsonify(status="error", error=f"{key} must be an integer from {minimum} to {maximum}."), 400
        values[key] = value
    hotel_rating = payload.get("hotel_rating")
    if isinstance(hotel_rating, bool) or not isinstance(hotel_rating, (int, float)) or not 1 <= hotel_rating <= 5:
        return jsonify(status="error", error="hotel_rating must be a number from 1 to 5.") , 400
    if values["travellers"] != values["adults"] + values["children"]:
        return jsonify(status="error", error="travellers must equal adults plus children."), 400
    source = Path(__file__).resolve().parents[1] / "Data" / "Travel And Tourism.csv"
    try:
        with source.open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        source_pair = next((row for row in rows if normalize_city(row["Destination_City"]) == normalize_city(payload["destination_city"])
                            and normalize_city(row["Destination_Country"]) == normalize_city(payload["destination_country"])), None)
        if source_pair is None:
            return jsonify(status="error", error="This destination/country pair is not represented in the cost source."), 400
        for column, key in (("Meal_Plan", "meal_plan"), ("Transportation_Type", "transportation_type")):
            if payload[key] not in {row[column] for row in rows}:
                return jsonify(status="error", error=f"{key} is not represented in the source data."), 400
        travel_row = {"Destination_City": source_pair["Destination_City"],
                      "Destination_Country": source_pair["Destination_Country"],
                      "Meal_Plan": payload["meal_plan"], "Transportation_Type": payload["transportation_type"],
                      "Number_of_Travellers": values["travellers"], "Number_of_Adults": values["adults"],
                      "Number_of_Children": values["children"], "Number_of_Rooms": values["rooms"],
                      "Number_of_Nights": values["nights"], "Hotel_Rating": float(hotel_rating),
                      "lead_days": values["lead_days"], "travel_month": values["travel_month"],
                      "travel_dayofweek": values["travel_dayofweek"]}
        return jsonify(status="ok", data=trip_cost_prediction(travel_row))
    except FileNotFoundError as exc:
        return jsonify(status="error", error=str(exc)), 503
    except (OSError, KeyError, ValueError) as exc:
        return jsonify(status="error", error="Trip cost source or model is unavailable."), 503
