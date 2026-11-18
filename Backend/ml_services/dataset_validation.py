"""Read-only schema and quality checks for the source datasets and artifacts.

Run from Backend with ``python -m ml_services.dataset_validation``. The command
reports issues and never changes source files or model artifacts.
"""
import csv
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

from ml_services.tourism import _xlsx_rows
from ml_services.destinations import destination_profiles
from ml_services.city_directory import directory_coverage, hotel_directory_search
from ml_services.destination_estimates import _temperature_range

DATA = Path(__file__).resolve().parents[1] / "Data"
ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parent

CSV_COLUMNS = {
    "Destinations.csv": ["DestinationID", "Name", "State", "Type", "Popularity", "BestTimeToVisit"],
    "tourism_statistics.csv": ["destination", "state", "category", "best_season", "months_best_for",
                               "avg_budget_inr_per_person", "avg_trip_duration_days", "crowd_level",
                               "temperature_range_c", "nearest_major_city", "popular_with", "region"],
    "destination_details.csv": ["HistoryID", "UserID", "DestinationID", "VisitDate", "ExperienceRating"],
    "hotel_bookings_updated_2024.csv": ["hotel", "is_canceled", "lead_time", "arrival_date_year",
        "arrival_date_month", "arrival_date_week_number", "arrival_date_day_of_month",
        "stays_in_weekend_nights", "stays_in_week_nights", "adults", "children", "babies", "meal",
        "country", "market_segment", "distribution_channel", "is_repeated_guest", "previous_cancellations",
        "previous_bookings_not_canceled", "reserved_room_type", "assigned_room_type", "booking_changes",
        "deposit_type", "agent", "company", "days_in_waiting_list", "customer_type", "adr",
        "required_car_parking_spaces", "total_of_special_requests", "reservation_status",
        "reservation_status_date", "city"],
    "hotels.csv": ["S.No.", "State", "City", "Category", "Alcohol", "Hotel Name", "Address",
                   "Start Date", "Expiry Date", "Total Rooms"],
    "india-tourism-food-dataset.csv": ["City", "Tourist Spot 1", "Tourist Spot 2", "Tourist Spot 3",
        "Breakfast Spot 1", "Breakfast Spot 2", "Breakfast Spot 3", "Dinner Spot 1", "Dinner Spot 2", "Dinner Spot 3"],
    "Travel And Tourism.csv": ["Booking_ID", "Booking_Date", "Travel_Date", "Return_Date", "Customer_ID",
        "Customer_Name", "Customer_Age", "Gender", "Customer_City", "Customer_Country", "Destination_City",
        "Destination_Country", "Number_of_Travellers", "Number_of_Adults", "Number_of_Children", "Hotel_Name",
        "Hotel_Rating", "Number_of_Rooms", "Number_of_Nights", "Meal_Plan", "Payment_Method", "Booking_Status",
        "Cancellation_Status", "Cancellation_Reason", "Discount_Amount", "Customer_Rating",
        "Customer_Review_Comment", "Total_Trip_Cost", "Transportation_Type"],
}
XLSX_COLUMNS = ["Month", "State", "Domestic Tourists", "Foreign Tourists", "Total Tourists",
                "Tourism Revenue (INR Crore)", "Purpose of Visit", "Growth % (Approx.)"]
EXPECTED_ROWS = {"Destinations.csv": 1000, "tourism_statistics.csv": 110, "destination_details.csv": 999,
                 "user_visits.xlsx": 432, "hotel_bookings_updated_2024.csv": 119390, "hotels.csv": 1212,
                 "india-tourism-food-dataset.csv": 68, "Travel And Tourism.csv": 1000}
NUMERIC_FIELDS = {
    "Destinations.csv": ["DestinationID", "Popularity"],
    "tourism_statistics.csv": ["avg_budget_inr_per_person", "avg_trip_duration_days"],
    "destination_details.csv": ["HistoryID", "UserID", "DestinationID", "ExperienceRating"],
    "user_visits.xlsx": ["Domestic Tourists", "Foreign Tourists", "Total Tourists", "Tourism Revenue (INR Crore)", "Growth % (Approx.)"],
    "hotel_bookings_updated_2024.csv": ["is_canceled", "lead_time", "arrival_date_year", "arrival_date_week_number",
        "arrival_date_day_of_month", "stays_in_weekend_nights", "stays_in_week_nights", "adults", "children", "babies",
        "is_repeated_guest", "previous_cancellations", "previous_bookings_not_canceled", "booking_changes",
        "days_in_waiting_list", "agent", "company", "adr", "required_car_parking_spaces", "total_of_special_requests"],
    "hotels.csv": ["S.No.", "Total Rooms"],
    "Travel And Tourism.csv": ["Customer_Age", "Number_of_Travellers", "Number_of_Adults", "Number_of_Children",
        "Hotel_Rating", "Number_of_Rooms", "Number_of_Nights", "Discount_Amount", "Customer_Rating", "Total_Trip_Cost"],
}
DATE_FIELDS = {
    "destination_details.csv": {"VisitDate": "%Y-%m-%d"},
    "hotels.csv": {"Start Date": "%d/%m/%Y", "Expiry Date": "%d/%m/%Y"},
    "hotel_bookings_updated_2024.csv": {"reservation_status_date": "iso_datetime"},
    "Travel And Tourism.csv": {"Booking_Date": "%Y-%m-%d", "Travel_Date": "%Y-%m-%d", "Return_Date": "%Y-%m-%d"},
}


def _inspect_rows(name, path, rows, columns):
    missing_columns = [column for column in columns if column not in (rows[0].keys() if rows else [])]
    missing_cells = {column: sum(not str(row.get(column, "") or "").strip() for row in rows)
                     for column in columns if column in (rows[0].keys() if rows else [])}
    missing_cells = {column: count for column, count in missing_cells.items() if count}
    numeric_errors = {}
    for column in NUMERIC_FIELDS.get(name, []):
        errors = 0
        for row in rows:
            value = str(row.get(column, "") or "").strip()
            if not value:
                continue
            try:
                float(value)
            except (TypeError, ValueError):
                errors += 1
        if errors:
            numeric_errors[column] = errors
    date_errors = {}
    for column, date_format in DATE_FIELDS.get(name, {}).items():
        errors = 0
        for row in rows:
            value = str(row.get(column, "") or "").strip()
            if value:
                try:
                    if date_format == "iso_datetime":
                        datetime.fromisoformat(value.replace("Z", "+00:00"))
                    else:
                        datetime.strptime(value, date_format)
                except ValueError:
                    errors += 1
        if errors:
            date_errors[column] = errors
    exact_duplicates = len(rows) - len({tuple(row.get(column, "") for column in columns) for row in rows})
    expected = EXPECTED_ROWS.get(name)
    return {"path": str(path.relative_to(PROJECT)), "format": path.suffix.lstrip("."),
            "rows": len(rows), "expected_rows_at_audit": expected,
            "row_count_matches_audit": expected is None or len(rows) == expected,
            "columns": list(rows[0].keys()) if rows else [], "missing_required_columns": missing_columns,
            "missing_cells_by_column": missing_cells, "invalid_numeric_values_by_column": numeric_errors,
            "invalid_date_values_by_column": date_errors,
            "exact_duplicate_rows": exact_duplicates}


def validate_datasets():
    """Return a current inventory and lightweight structural checks."""
    reports, errors = {}, []
    for name, columns in CSV_COLUMNS.items():
        path = DATA / name
        try:
            with path.open(encoding="utf-8-sig", newline="") as stream:
                rows = list(csv.DictReader(stream))
            report = _inspect_rows(name, path, rows, columns)
            reports[name] = report
            if report["missing_required_columns"]:
                errors.append(f"{name}: missing required columns {report['missing_required_columns']}")
        except (OSError, UnicodeError, csv.Error) as exc:
            errors.append(f"{name}: unavailable or unreadable ({type(exc).__name__})")

    workbook = DATA / "user_visits.xlsx"
    try:
        rows = _xlsx_rows(workbook)
        reports[workbook.name] = _inspect_rows(workbook.name, workbook, rows, XLSX_COLUMNS)
        if reports[workbook.name]["missing_required_columns"]:
            errors.append(f"{workbook.name}: missing required columns {reports[workbook.name]['missing_required_columns']}")
    except (OSError, KeyError, ValueError, IndexError, csv.Error) as exc:
        errors.append(f"{workbook.name}: unavailable or unreadable ({type(exc).__name__})")

    structured = {
        "Backend/config/trip_cost_rates.json": ROOT / "config" / "trip_cost_rates.json",
        "Backend/artifacts/evaluation.json": ROOT / "artifacts" / "evaluation.json",
        "Frontend/tourisense-tourists/public/images/destination-manifest.json":
            PROJECT / "Frontend" / "tourisense-tourists" / "public" / "images" / "destination-manifest.json",
    }
    for label, path in structured.items():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            reports[label] = {"path": label, "format": "json", "available": True,
                              "top_level_type": type(data).__name__,
                              "entries": len(data) if isinstance(data, dict) else None}
        except (OSError, ValueError) as exc:
            reports[label] = {"path": label, "format": "json", "available": False,
                              "error": type(exc).__name__}
            errors.append(f"{label}: unavailable or invalid JSON")

    manifest_path = structured["Frontend/tourisense-tourists/public/images/destination-manifest.json"]
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            image_root = manifest_path.parent
            missing_images = [value for value in manifest.values()
                              if not (image_root / unquote(str(value).removeprefix("/images/"))).is_file()]
            reports["destination_images"] = {"mapped_destinations": len(manifest),
                                              "missing_mapped_files": missing_images,
                                              "fallback_available": (image_root / "destination-fallback.svg").is_file()}
        except (OSError, ValueError, TypeError) as exc:
            reports["destination_images"] = {"available": False, "error": type(exc).__name__}

    artifact = ROOT / "artifacts" / "trip_cost.joblib"
    reports["Backend/artifacts/trip_cost.joblib"] = {
        "path": str(artifact.relative_to(PROJECT)), "format": "joblib", "available": artifact.is_file(),
        "bytes": artifact.stat().st_size if artifact.is_file() else None,
        "validation": "file presence only; artifact is not deserialized by this read-only validator"}
    try:
        profiles = destination_profiles()
        visits_path = DATA / "destination_details.csv"
        catalog_path = DATA / "Destinations.csv"
        with visits_path.open(encoding="utf-8-sig", newline="") as stream:
            visits = list(csv.DictReader(stream))
        with catalog_path.open(encoding="utf-8-sig", newline="") as stream:
            catalog = list(csv.DictReader(stream))
        catalog_ids = {row.get("DestinationID") for row in catalog}
        rating_values = []
        for row in visits:
            try:
                rating_values.append(int(row["ExperienceRating"]))
            except (KeyError, TypeError, ValueError):
                pass
        reports["relationships"] = {
            "rating_rows": len(visits),
            "rating_destination_id_matches": sum(row.get("DestinationID") in catalog_ids for row in visits),
            "catalog_ids_unique": len(catalog_ids) == len(catalog),
            "history_ids_unique": len({row.get("HistoryID") for row in visits}) == len(visits),
            "ratings_outside_1_to_5": sum(not 1 <= value <= 5 for value in rating_values),
            "destination_profile_resolution": profiles["coverage"],
            "hotel_food_city_coverage": directory_coverage(),
        }
    except (OSError, KeyError, ValueError) as exc:
        reports["relationships"] = {"available": False, "error": type(exc).__name__}
    try:
        tourism_rows = _xlsx_rows(DATA / "user_visits.xlsx")
        state_month_pairs = [(row.get("State"), row.get("Month")) for row in tourism_rows]
        travel_rows = _read_csv_rows(DATA / "Travel And Tourism.csv")
        total_mismatches = 0
        for row in tourism_rows:
            try:
                total_mismatches += int(row["Total Tourists"]) != (int(row["Domestic Tourists"]) + int(row["Foreign Tourists"]))
            except (KeyError, TypeError, ValueError):
                total_mismatches += 1
        reports["source_semantics"] = {
            "tourism_state_month_pairs_unique": len(set(state_month_pairs)) == len(state_month_pairs),
            "tourism_totals_not_domestic_plus_foreign": total_mismatches,
            "tourism_year_column_present": any("year" in str(column).casefold() for column in (tourism_rows[0].keys() if tourism_rows else [])),
            "unparseable_destination_temperature_ranges": sum(
                _temperature_range(row.get("temperature_range_c")) is None
                for row in _read_csv_rows(DATA / "tourism_statistics.csv")),
            "travel_booking_ids_unique": len({row.get("Booking_ID") for row in travel_rows}) == len(travel_rows),
            "travel_customer_ids_unique": len({row.get("Customer_ID") for row in travel_rows}) == len(travel_rows),
            "hotel_normalized_duplicate_name_rows": hotel_directory_search(page=1, page_size=1)["duplicate_normalized_hotel_names_in_source"],
        }
    except (OSError, KeyError, ValueError) as exc:
        reports["source_semantics"] = {"available": False, "error": type(exc).__name__}
    return {"status": "error" if errors else "ok", "datasets": reports,
            "expected_row_counts_are_audit_snapshots_not_enforced": True, "errors": errors}


def _read_csv_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def main():
    result = validate_datasets()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
