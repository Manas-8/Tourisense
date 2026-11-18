
from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError

from extensions import db
from ml_services.city_directory import directory_coverage, food_directory, hotel_directory, hotel_directory_search, travel_cost_match
from ml_services.destinations import destination_profiles
from models import Hotel, Restaurant, TransportOption

catalog_bp = Blueprint("catalog_bp", __name__, url_prefix="/api/catalog")

def _number(value):
    return float(value) if value is not None else None


def _page(items, kind):
    query = (request.args.get("q") or "").strip().casefold()
    location = (request.args.get("location") or "").strip().casefold()
    filtered = []
    for item in items:
        if query and query not in " ".join(str(value or "") for value in item.values()).casefold():
            continue
        if location and location not in " ".join(str(item.get(key) or "") for key in ("location", "city", "state", "route")).casefold():
            continue
        filtered.append(item)
    return jsonify(status="ok", data={"items": filtered, "count": len(filtered), "source": kind})


@catalog_bp.get("/destinations")
def destinations():
    try:
        data = destination_profiles()
        profiles = []
        for row in data["profiles"]:
            cost_city = travel_cost_match(row.get("name"), "India")
            profiles.append({
                **row,
                "location": ", ".join(value for value in (row.get("nearest_major_city"), row.get("state")) if value),
                "bestTime": row.get("months_best_for") or row.get("best_season"),
                "budget": row.get("budget_inr"),
                "rating": row.get("observed_rating"),
                "description": None,
                "image": None,
                "cost_source_destination": cost_city,
            })
        return jsonify(status="ok", data={"items": profiles, "count": len(profiles), "coverage": data["coverage"], "source": "destination_metadata"})
    except (OSError, KeyError, ValueError) as exc:
        return jsonify(status="error", error="Destination source data could not be read."), 503


@catalog_bp.get("/hotels")
def hotels():
    try:
        rows = Hotel.query.filter_by(is_active=True).order_by(Hotel.name.asc()).all()
        items = [{"id": row.id, "name": row.name, "location": row.location,
                  "city": row.destination.city if row.destination else None,
                  "state": row.destination.state_region if row.destination else None,
                  "description": row.description, "price_per_night": _number(row.price_per_night),
                  "rating": _number(row.rating), "image": row.image_url, "amenities": row.amenities}
                 for row in rows]
        return _page(items, "operational_mysql")
    except (SQLAlchemyError, RuntimeError):
        db.session.rollback()
        return jsonify(status="error", error="Hotel catalog is currently unavailable."), 503


@catalog_bp.get("/restaurants")
def restaurants():
    try:
        rows = Restaurant.query.filter_by(is_active=True).order_by(Restaurant.name.asc()).all()
        items = [{"id": row.id, "name": row.name, "location": row.location,
                  "city": row.destination.city if row.destination else None,
                  "state": row.destination.state_region if row.destination else None,
                  "description": row.description, "cuisine": row.cuisine, "price_tier": row.price_tier,
                  "rating": _number(row.rating), "image": row.image_url}
                 for row in rows]
        return _page(items, "operational_mysql")
    except (SQLAlchemyError, RuntimeError):
        db.session.rollback()
        return jsonify(status="error", error="Restaurant catalog is currently unavailable."), 503


@catalog_bp.get("/transport")
def transport():
    try:
        rows = TransportOption.query.filter_by(is_active=True).order_by(TransportOption.name.asc()).all()
        items = [{"id": row.id, "name": row.name, "type": row.transport_type,
                  "location": row.destination.city if row.destination else None,
                  "state": row.destination.state_region if row.destination else None,
                  "route": row.route, "cost": _number(row.cost_from),
                  "duration": row.duration_text, "image": row.image_url}
                 for row in rows]
        return _page(items, "operational_mysql")
    except (SQLAlchemyError, RuntimeError):
        db.session.rollback()
        return jsonify(status="error", error="Transport catalog is currently unavailable."), 503


@catalog_bp.get("/directory-hotels")
def directory_hotels():
    city = (request.args.get("city") or "").strip()
    if not city or len(city) > 120:
        return jsonify(status="error", error="city is required and must be at most 120 characters."), 400
    try:
        return jsonify(status="ok", data=hotel_directory(city))
    except (OSError, KeyError, ValueError):
        return jsonify(status="error", error="Hotel directory could not be read."), 503


@catalog_bp.get("/hotel-directory")
def searchable_hotel_directory():
    args = request.args
    for key in ("q", "city", "state", "category"):
        if len(args.get(key, "")) > 120:
            return jsonify(status="error", error=f"{key} must be at most 120 characters."), 400
    try:
        page = int(args.get("page", "1"))
        page_size = int(args.get("page_size", "50"))
        if page < 1 or not 1 <= page_size <= 100:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify(status="error", error="page must be positive and page_size must be from 1 to 100."), 400
    try:
        result = hotel_directory_search(args.get("q", ""), args.get("city", ""), args.get("state", ""),
                                        args.get("category", ""), page, page_size)
        return jsonify(status="ok", data=result)
    except (OSError, KeyError, ValueError):
        return jsonify(status="error", error="Hotel directory source could not be read."), 503


@catalog_bp.get("/food")
def food():
    city = (request.args.get("city") or "").strip()
    if not city or len(city) > 120:
        return jsonify(status="error", error="city is required and must be at most 120 characters."), 400
    try:
        return jsonify(status="ok", data=food_directory(city))
    except (OSError, KeyError, ValueError):
        return jsonify(status="error", error="Food directory could not be read."), 503


@catalog_bp.get("/directory-coverage")
def directory_city_coverage():
    try:
        return jsonify(status="ok", data=directory_coverage())
    except (OSError, KeyError, ValueError):
        return jsonify(status="error", error="Directory coverage could not be read."), 503


