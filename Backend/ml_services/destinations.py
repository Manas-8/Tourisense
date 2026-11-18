"""Transparent destination matching and content based ranking."""
import csv
import re
from collections import defaultdict
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "Data"

# These are verified naming variants in the supplied data, not fuzzy matches.
DESTINATION_ALIASES = {
    "taj mahal": "agra",            # landmark represented by the Agra city profile
    "goa beaches": "goa",          # catalog beach-region entry represented by Goa profile
    "jaipur city": "jaipur",       # catalog city label represented by the Jaipur profile
}
STATE_ALIASES = {
    "jammu and kashmir": "jammu and kashmir",
    "jammu kashmir": "jammu and kashmir",
}
INTEREST_ALIASES = {
    "history": {"historical", "historic", "heritage", "cultural", "culture"},
    "heritage": {"historical", "historic", "heritage", "cultural", "culture"},
    "culture": {"cultural", "culture", "heritage", "historical", "historic"},
    "beach": {"beach", "coastal"}, "beaches": {"beach", "coastal"},
    "nature": {"nature", "wildlife", "hill station", "ecotourism"},
    "adventure": {"adventure", "trekking", "outdoor"},
    "spiritual": {"spiritual", "religious", "pilgrimage"},
    "families": {"families", "family"}, "family": {"families", "family"},
    "solo": {"solo"},
}


def _rows(filename):
    with (DATA / filename).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _norm(value):
    value = (value or "").casefold().replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def _state_key(value):
    value = _norm(value)
    return STATE_ALIASES.get(value, value)


def _num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _catalog_index():
    """Verified metadata key -> source catalog rows, using exact or named aliases."""
    metadata = _rows("tourism_statistics.csv")
    catalog = _rows("Destinations.csv")
    meta_by_key = defaultdict(list)
    for row in metadata:
        meta_by_key[(_norm(row.get("destination")), _state_key(row.get("state")))].append(row)
    catalog_by_key = defaultdict(list)
    for row in catalog:
        name = _norm(row.get("Name"))
        canonical_name = _norm(DESTINATION_ALIASES.get(name, name))
        canonical_state = _state_key(row.get("State"))
        catalog_by_key[(canonical_name, canonical_state)].append(row)
    return metadata, catalog, meta_by_key, catalog_by_key


def _matched_catalog(metadata, catalog, meta_by_key, catalog_by_key):
    grouped = {}
    unmatched_catalog = set(catalog_by_key)
    ambiguous = 0
    for meta_key, meta_rows in meta_by_key.items():
        catalog_rows = catalog_by_key.get(meta_key, [])
        if len(meta_rows) != 1:
            ambiguous += 1
        if len(meta_rows) != 1 or not catalog_rows:
            continue
        unmatched_catalog.discard(meta_key)
        values = [_num(row.get("Popularity")) for row in catalog_rows]
        values = [value for value in values if value is not None]
        methods = []
        for row in catalog_rows:
            original = _norm(row.get("Name"))
            if _norm(DESTINATION_ALIASES.get(original, original)) != original:
                methods.append("named_alias")
            elif _state_key(row.get("State")) != _norm(row.get("State")):
                methods.append("state_alias")
            else:
                methods.append("exact_normalized")
        grouped[meta_key] = {
            "catalog_rows": len(catalog_rows),
            "popularity": sum(values) / len(values) if values else None,
            "catalog_name": catalog_rows[0].get("Name"),
            "catalog_state": catalog_rows[0].get("State"),
            "match_method": "named_alias" if "named_alias" in methods else ("state_alias" if "state_alias" in methods else "exact_normalized"),
        }
    coverage = {
        "catalog_rows": len(catalog),
        "catalog_unique_destinations": len(catalog_by_key),
        "metadata_rows": len(metadata),
        "metadata_unique_destinations": len(meta_by_key),
        "matched_catalog_rows": sum(info["catalog_rows"] for info in grouped.values()),
        "matched_unique_catalog_destinations": len(grouped),
        "unmatched_catalog_destinations": len(unmatched_catalog),
        "unmatched_catalog_keys": [" / ".join(key) for key in sorted(unmatched_catalog)],
        "unmatched_metadata_destinations": len(set(meta_by_key) - set(grouped)),
        "ambiguous_metadata_keys": ambiguous,
        "match_policy": "normalized exact keys plus documented, manually verified aliases; no fuzzy matching",
    }
    return grouped, coverage


def _rating_index():
    """Optional aggregate enrichment; catalog matching remains usable without ratings."""
    try:
        from ml_services.experience import experience_summary
        summary = experience_summary()
        return {(_norm(item["name"]), _state_key(item["state"])): item
                for item in summary["destination_ratings"]}
    except (OSError, KeyError, ValueError):
        return {}


def destination_profiles():
    metadata, catalog, meta_by_key, catalog_by_key = _catalog_index()
    matches, coverage = _matched_catalog(metadata, catalog, meta_by_key, catalog_by_key)
    catalog_ratings = _rating_index()
    profiles = []
    for row in metadata:
        key = (_norm(row.get("destination")), _state_key(row.get("state")))
        match = matches.get(key)
        catalog_key = (_norm(match["catalog_name"]), _state_key(match["catalog_state"])) if match else key
        rating = catalog_ratings.get(catalog_key) if match else None
        profiles.append({
            "id": "|".join(key), "name": row.get("destination"), "state": row.get("state"),
            "category": row.get("category") or None,
            "best_season": row.get("best_season") or None,
            "months_best_for": row.get("months_best_for") or None,
            "budget_inr": _num(row.get("avg_budget_inr_per_person")),
            "duration_days": _num(row.get("avg_trip_duration_days")),
            "crowd_level": row.get("crowd_level") or None,
            "temperature_range_c": row.get("temperature_range_c") or None,
            "nearest_major_city": row.get("nearest_major_city") or None,
            "popular_with": row.get("popular_with") or None,
            "region": row.get("region") or None,
            "catalog_match": bool(match),
            "catalog_match_method": match["match_method"] if match else None,
            "popularity": match["popularity"] if match else None,
            "observed_rating": rating["mean_rating"] if rating else None,
            "rating_observations": rating["observations"] if rating else 0,
        })
    return {"profiles": profiles, "coverage": coverage}


def _interest_matches(interests, row):
    categories = {_norm(token) for token in re.split(r"[;|,]", row.get("category") or "") if token.strip()}
    audience = {_norm(token) for token in re.split(r"[;|,]", row.get("popular_with") or "") if token.strip()}
    matches = []
    for interest in interests:
        normalized = _norm(interest)
        alternatives = INTEREST_ALIASES.get(normalized, {normalized})
        if alternatives & categories or alternatives & audience:
            matches.append(interest)
    return matches


def _candidate(row, filters, popularity, observed_rating=None):
    checks = {}
    reasons = []
    interest_matches = _interest_matches(filters.get("interests") or [], row)
    interest_unknown = not row.get("category") and not row.get("popular_with")
    if filters.get("region"):
        checks["region"] = None if not row.get("region") else _norm(row["region"]) == _norm(filters["region"])
        if checks["region"] is True: reasons.append(f"in your selected {row['region']} region")
    if filters.get("season"):
        checks["season"] = None if not row.get("best_season") else _norm(filters["season"]) == _norm(row["best_season"])
        if checks["season"] is True: reasons.append(f"best season matches {row['best_season']}")
    if filters.get("budget") is not None:
        budget = _num(row.get("avg_budget_inr_per_person"))
        checks["budget"] = None if budget is None else budget <= float(filters["budget"])
        if checks["budget"] is True: reasons.append("estimated per-person budget is within your limit")
    if filters.get("duration_days") is not None:
        days = _num(row.get("avg_trip_duration_days"))
        checks["duration"] = None if days is None else abs(days - float(filters["duration_days"])) <= 2
        if checks["duration"] is True: reasons.append("typical trip duration is within two days of your plan")
    if filters.get("crowd"):
        checks["crowd"] = None if not row.get("crowd_level") else _norm(row["crowd_level"]) == _norm(filters["crowd"])
        if checks["crowd"] is True: reasons.append(f"matches your {row['crowd_level'].lower()} crowd preference")
    if filters.get("interests"):
        checks["interests"] = None if interest_unknown else bool(interest_matches)
        for interest in interest_matches:
            reasons.append(f"matches your interest in {interest}")
    matched = [name for name, value in checks.items() if value is True]
    failed = [name for name, value in checks.items() if value is False]
    unknown = [name for name, value in checks.items() if value is None]
    score = len(matched) * 10 + (len(interest_matches) * 2)
    if popularity is not None:
        score += popularity / 100
    if not reasons:
        reasons.append("available destination profile; no selected preference attribute could be confirmed")
    return {
        "id": "|".join((_norm(row.get("destination")), _state_key(row.get("state")))),
        "name": row.get("destination"), "state": row.get("state"),
        "category": row.get("category") or None, "best_time": row.get("months_best_for") or None,
        "season": row.get("best_season") or None,
        "popularity": popularity, "region": row.get("region") or None,
        "budget_inr": _num(row.get("avg_budget_inr_per_person")),
        "duration_days": _num(row.get("avg_trip_duration_days")),
        "crowd_level": row.get("crowd_level") or None,
        "temperature_range_c": row.get("temperature_range_c") or None,
        "popular_with": row.get("popular_with") or None,
        "observed_rating": observed_rating["mean_rating"] if observed_rating else None,
        "rating_observations": observed_rating["observations"] if observed_rating else 0,
        "ranking_score": round(score, 2), "reasons": reasons,
        "matched_criteria": matched, "not_matched_criteria": failed,
        "unknown_criteria": unknown,
    }


def recommend(filters):
    metadata, catalog, meta_by_key, catalog_by_key = _catalog_index()
    catalog_matches, coverage = _matched_catalog(metadata, catalog, meta_by_key, catalog_by_key)
    ratings = _rating_index()
    candidates = []
    for row in metadata:
        key = (_norm(row.get("destination")), _state_key(row.get("state")))
        match = catalog_matches.get(key)
        rating_key = (_norm(match["catalog_name"]), _state_key(match["catalog_state"])) if match else None
        candidates.append(_candidate(row, filters, match["popularity"] if match else None,
                                     ratings.get(rating_key) if rating_key else None))
    strict = [candidate for candidate in candidates if not candidate["not_matched_criteria"]]
    relaxed = not strict
    if relaxed:
        candidates.sort(key=lambda item: (len(item["matched_criteria"]), item["ranking_score"]), reverse=True)
        output = candidates[:12]
        relaxed_criteria = sorted({criterion for candidate in output for criterion in candidate["not_matched_criteria"]})
        for candidate in output:
            candidate["alternative_notice"] = "Alternative result: this destination does not satisfy every selected filter."
    else:
        strict.sort(key=lambda item: (item["ranking_score"], item["popularity"] or 0), reverse=True)
        output = strict[:12]
        relaxed_criteria = []
    return {
        "method": "transparent_content_match",
        "ranking_score_description": "Weighted count of matched preferences plus source popularity tie-breaker; not a probability or rating.",
        "mode": "relaxed_alternatives" if relaxed else "matched_results",
        "relaxed_criteria": relaxed_criteria,
        "recommendations": output,
        "coverage": coverage,
        "notice": "Unknown destination attributes are shown as unknown and do not fail a filter. Popularity is only a source-scale tie-breaker, never a probability.",
    }
