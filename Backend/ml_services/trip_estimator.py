"""Rules-based INR planning estimates with explicit, editable rates."""
import json
import math
from pathlib import Path

from ml_services.destinations import destination_profiles

RATES_PATH = Path(__file__).resolve().parents[1] / "config" / "trip_cost_rates.json"


def _rates():
    return json.loads(RATES_PATH.read_text(encoding="utf-8"))


def estimate_trip_cost(destination, transport_mode, travellers, duration_days, food_preference, rooms=None):
    if not isinstance(destination, str) or not destination.strip() or len(destination) > 160:
        raise ValueError("destination is required and must be at most 160 characters.")
    if not isinstance(transport_mode, str) or transport_mode not in {"bus", "train", "flight"}:
        raise ValueError("transport_mode must be bus, train, or flight.")
    if isinstance(travellers, bool) or not isinstance(travellers, int) or not 1 <= travellers <= 30:
        raise ValueError("travellers must be an integer from 1 to 30.")
    if isinstance(duration_days, bool) or not isinstance(duration_days, int) or not 1 <= duration_days <= 60:
        raise ValueError("duration_days must be an integer from 1 to 60.")
    if rooms is not None and (isinstance(rooms, bool) or not isinstance(rooms, int) or not 1 <= rooms <= 15):
        raise ValueError("rooms must be an integer from 1 to 15.")
    rates = _rates()
    if not isinstance(food_preference, str) or food_preference not in rates["food_person_day_inr"]:
        raise ValueError("food_preference must be budget, vegetarian, standard, or premium.")

    profiles = destination_profiles()["profiles"]
    profile = next((row for row in profiles if str(row.get("id")) == destination.strip()), None)
    if not profile:
        key = " ".join(destination.casefold().split())
        profile = next((row for row in profiles if " ".join(row.get("name", "").casefold().split()) == key), None)
    budget = profile.get("budget_inr") if profile else None
    tiers = rates["destination_tiers"]
    if budget is None:
        tier_name = "standard"
        tier_source = "documented standard fallback; destination metadata match unavailable"
    elif budget <= tiers["economy"]["maximum_source_budget_inr"]:
        tier_name = "economy"
        tier_source = f"destination source budget tier (reference INR {budget:g})"
    elif budget <= tiers["standard"]["maximum_source_budget_inr"]:
        tier_name = "standard"
        tier_source = f"destination source budget tier (reference INR {budget:g})"
    else:
        tier_name = "premium"
        tier_source = f"destination source budget tier (reference INR {budget:g})"
    tier = tiers[tier_name]
    nights = max(1, duration_days - 1)
    rooms = rooms if rooms is not None else math.ceil(travellers / rates["room_capacity_people"])
    factor = tier["rate_factor"]
    breakdown = {
        "transport": rates["transport_round_trip"][transport_mode] * factor * travellers,
        "accommodation": tier["room_night_inr"] * factor * rooms * nights,
        "food": rates["food_person_day_inr"][food_preference] * factor * travellers * duration_days,
        "local_transport": tier["local_transport_person_day_inr"] * factor * travellers * duration_days,
        "activities": tier["activity_person_day_inr"] * factor * travellers * duration_days,
    }
    rounding = rates["rounding_unit_inr"]
    breakdown = {key: int(round(value / rounding) * rounding) for key, value in breakdown.items()}
    total = sum(breakdown.values())
    return {"kind": "rules_based_approximate_estimate", "label": rates["estimate_label"], "currency": "INR",
            "destination": profile["name"] if profile else destination.strip(),
            "destination_tier": tier_name, "destination_tier_source": tier_source,
            "transport_mode": transport_mode, "transport_scope": "round trip per traveller",
            "travellers": travellers, "duration_days": duration_days, "nights_charged": nights,
            "rooms_assumed": rooms, "food_preference": food_preference,
            "breakdown_inr": breakdown, "total_inr": total,
            "per_person_inr": int(round(total / travellers / rounding) * rounding),
            "method": "Editable rates in Backend/config/trip_cost_rates.json. Source budget only selects an economy/standard/premium tier; it is not treated as an observed hotel price. Transport rates are round-trip planning allowances. All components are approximate assumptions, not live quotes or availability."}
