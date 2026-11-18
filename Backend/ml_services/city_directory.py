"""Read-only access to the supplied hotel directory and food guide."""
import csv
import re
import unicodedata
from datetime import datetime
from functools import lru_cache
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "Data"
CITY_ALIASES = {
    "bangalore": "bengaluru", "bengaluru": "bengaluru",
    "mysore": "mysuru", "mysuru": "mysuru",
    "new delhi": "delhi", "delhi": "delhi",
    "ahmednagar": "ahilyanagar", "ahilyanagar": "ahilyanagar",
    "aurangabad": "chhatrapati sambhajinagar", "chhatrapati sambhajinagar": "chhatrapati sambhajinagar",
    "calicut": "kozhikode", "kozhikode": "kozhikode",
    "alleppey": "alappuzha", "alappuzha": "alappuzha",
}
FOOD_COLUMNS = {
    "Tourist Spot": ["Tourist Spot 1", "Tourist Spot 2", "Tourist Spot 3"],
    "Breakfast Spot": ["Breakfast Spot 1", "Breakfast Spot 2", "Breakfast Spot 3"],
    "Dinner Spot": ["Dinner Spot 1", "Dinner Spot 2", "Dinner Spot 3"],
}
TRAVEL_DESTINATION_ALIASES = {
    "leh ladakh": "leh",
    "andaman islands": "andaman and nicobar",
}


def normalize_city(value):
    text = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode("ascii").casefold()
    text = re.sub(r"[^a-z0-9]+", " ", text).strip()
    return CITY_ALIASES.get(text, text)


def _csv(name):
    with (DATA / name).open(encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def _rows_by_city(filename, city_field):
    return _csv(filename), city_field


def hotel_directory(city):
    rows, field = _rows_by_city("hotels.csv", "City")
    key = normalize_city(city)
    matches = []
    for row in rows:
        if normalize_city(row.get(field)) != key:
            continue
        try:
            start = datetime.strptime(row["Start Date"].strip(), "%d/%m/%Y").date().isoformat()
            expiry = datetime.strptime(row["Expiry Date"].strip(), "%d/%m/%Y").date().isoformat()
            dates_parseable = True
        except (KeyError, ValueError, TypeError):
            start = expiry = None
            dates_parseable = False
        try:
            rooms = int(row["Total Rooms"])
        except (KeyError, ValueError, TypeError):
            rooms = None
        matches.append({
            "id": row.get("S.No."), "state": row.get("State"), "city": row.get("City"),
            "category": row.get("Category"), "name": (row.get("Hotel Name") or "").strip() or None,
            "address": (row.get("Address") or "").strip() or None,
            "start_date": start, "expiry_date": expiry, "rooms": rooms,
            "source_dates_parseable": dates_parseable,
            "date_semantics": "Source start/expiry dates; registration meaning and current operating status are unverified.",
        })
    return {"city": city, "items": matches, "count": len(matches),
            "source": "hotels.csv", "date_filter_applied": False,
            "limitation": "This directory is not a live availability or occupancy feed. Source dates are displayed without filtering because their operational semantics are undocumented."}


def hotel_directory_search(query="", city="", state="", category="", page=1, page_size=50):
    rows = _csv("hotels.csv")
    normalized_query = " ".join(str(query or "").casefold().split())
    city_key = normalize_city(city) if city else ""
    state_key = normalize_city(state) if state else ""
    category_key = " ".join(str(category or "").casefold().split())
    items = []
    normalized_names = []
    for row in rows:
        name = (row.get("Hotel Name") or "").strip() or None
        duplicate_key = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode("ascii").casefold()
        normalized_names.append(re.sub(r"[^a-z0-9]+", " ", duplicate_key).strip())
        if city_key and normalize_city(row.get("City")) != city_key:
            continue
        if state_key and normalize_city(row.get("State")) != state_key:
            continue
        if category_key and " ".join((row.get("Category") or "").casefold().split()) != category_key:
            continue
        searchable = " ".join(str(row.get(key) or "") for key in ("Hotel Name", "City", "State", "Category", "Address")).casefold()
        if normalized_query and normalized_query not in " ".join(searchable.split()):
            continue
        def date_value(key):
            raw = (row.get(key) or "").strip()
            if not raw:
                return None, None
            try:
                return datetime.strptime(raw, "%d/%m/%Y").date().isoformat(), None
            except ValueError:
                return None, raw
        start, invalid_start = date_value("Start Date")
        expiry, invalid_expiry = date_value("Expiry Date")
        raw_rooms = (row.get("Total Rooms") or "").strip()
        try:
            rooms = int(raw_rooms) if raw_rooms else None
        except ValueError:
            rooms = None
        items.append({"id": row.get("S.No."), "name": name, "city": row.get("City") or None,
                      "state": row.get("State") or None, "category": row.get("Category") or None,
                      "address": (row.get("Address") or "").strip() or None, "rooms": rooms,
                      "start_date": start, "expiry_date": expiry,
                      "invalid_start_date": invalid_start, "invalid_expiry_date": invalid_expiry})
    duplicates = len(normalized_names) - len(set(value for value in normalized_names if value))
    facets = {"cities": sorted({(row.get("City") or "").strip() for row in rows if (row.get("City") or "").strip()}, key=str.casefold),
              "states": sorted({(row.get("State") or "").strip() for row in rows if (row.get("State") or "").strip()}, key=str.casefold),
              "categories": sorted({(row.get("Category") or "").strip() for row in rows if (row.get("Category") or "").strip()}, key=str.casefold)}
    total = len(items)
    first = (page - 1) * page_size
    return {"items": items[first:first + page_size], "page": page, "page_size": page_size,
            "total_filtered": total, "total_source_rows": len(rows), "pages": (total + page_size - 1) // page_size,
            "duplicate_normalized_hotel_names_in_source": duplicates,
            "facets": facets,
            "filters": {"query": query, "city": city, "state": state, "category": category},
            "source": "Backend/Data/hotels.csv",
            "limitations": ["Duplicate names are retained as separate source records.",
                            "Invalid dates are returned as null with the original invalid value in a diagnostic field.",
                            "Room counts do not indicate current availability; date meanings and operating status are unverified."]}


def food_directory(city):
    rows = _csv("india-tourism-food-dataset.csv")
    key = normalize_city(city)
    row = next((item for item in rows if normalize_city(item.get("City")) == key), None)
    if not row:
        return {"city": city, "available": False, "groups": [], "source": "india-tourism-food-dataset.csv",
                "limitation": "No source row matches this city after conservative normalization and documented aliases."}
    groups = []
    for source_category, columns in FOOD_COLUMNS.items():
        places = [{"name": (row.get(column) or "").strip(), "source_column": column}
                  for column in columns if (row.get(column) or "").strip()]
        groups.append({"category": source_category, "places": places})
    return {"city": row["City"], "available": True, "groups": groups,
            "source": "india-tourism-food-dataset.csv",
            "limitation": "Source place names are listed as supplied; current existence, opening hours, and ratings are not verified."}


def directory_coverage():
    hotels = _csv("hotels.csv")
    foods = _csv("india-tourism-food-dataset.csv")
    hotel_cities = {normalize_city(row.get("City")) for row in hotels if row.get("City")}
    food_cities = {normalize_city(row.get("City")) for row in foods if row.get("City")}
    return {
        "hotels": {"rows": len(hotels), "unique_cities": len(hotel_cities), "cities": sorted(hotel_cities)},
        "food": {"rows": len(foods), "unique_cities": len(food_cities), "cities": sorted(food_cities)},
        "matching": {"shared_unique_cities": len(hotel_cities & food_cities),
                     "hotel_without_food_city": len(hotel_cities - food_cities),
                     "food_without_hotel_city": len(food_cities - hotel_cities),
                     "method": "normalized exact city names plus the explicit aliases in city_directory.py; no fuzzy matching"},
        "hotel_date_semantics_confirmed": False,
        "source_provenance": "Not documented in repository; directory/food records are not treated as real-time listings.",
    }


@lru_cache(maxsize=1)
def _travel_destination_index():
    rows = _csv("Travel And Tourism.csv")
    return {(normalize_city(row.get("Destination_City")), normalize_city(row.get("Destination_Country"))):
            (row.get("Destination_City"), row.get("Destination_Country")) for row in rows}


def travel_cost_match(destination_name, country="India"):
    """Only return a verified exact/explicit-alias destination pair in the travel sample."""
    target = TRAVEL_DESTINATION_ALIASES.get(normalize_city(destination_name), normalize_city(destination_name))
    match = _travel_destination_index().get((target, normalize_city(country)))
    if not match:
        return None
    return {"city": match[0], "country": match[1],
            "match_method": "explicit_alias" if normalize_city(destination_name) != target else "normalized_exact"}
