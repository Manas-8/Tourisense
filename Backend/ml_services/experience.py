import csv
from collections import Counter, defaultdict
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "Data"


def experience_summary():
    with (DATA / "destination_details.csv").open(encoding="utf-8-sig", newline="") as stream:
        visits = list(csv.DictReader(stream))
    with (DATA / "Destinations.csv").open(encoding="utf-8-sig", newline="") as stream:
        catalog = {item["DestinationID"]: (item["Name"], item["State"]) for item in csv.DictReader(stream)}
    ratings = []
    per_destination = defaultdict(list)
    unmatched_ids = 0
    for row in visits:
        try:
            rating = int(row["ExperienceRating"])
            if 1 <= rating <= 5:
                ratings.append(rating)
                destination = catalog.get(row.get("DestinationID"))
                if destination:
                    per_destination[destination].append(rating)
                else:
                    unmatched_ids += 1
        except (KeyError, ValueError, TypeError):
            pass
    counts = Counter(ratings)
    average = round(sum(ratings) / len(ratings), 2) if ratings else None
    # History is anonymized to aggregates: no IDs, dates or per-user records are returned.
    return {"kind": "observed_rating_summary", "label": "Observed visitor ratings",
            "observations": len(ratings), "mean_rating": average,
            "rating_scale": {"min": 1, "max": 5},
            "distribution": [{"rating": n, "count": counts.get(n, 0)} for n in range(1, 6)],
            "destinations_with_ratings": len(per_destination),
            "model": None, "prediction": None,
            "destination_ratings": [{"name": name, "state": state, "observations": len(values),
                                     "mean_rating": round(sum(values) / len(values), 2)}
                                    for (name, state), values in sorted(per_destination.items())],
            "destination_join_coverage": {"matched_rating_rows": len(ratings) - unmatched_ids,
                                          "unmatched_rating_rows": unmatched_ids},
            "limitation": "No rating model is reported: user and destination identifiers are excluded as features, and the remaining supplied visit fields do not provide validated trip preference attributes. This is an aggregate of observed ratings only."}
