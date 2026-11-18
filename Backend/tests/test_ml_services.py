import unittest
from unittest.mock import patch

from ml_services.destinations import _candidate, destination_profiles, recommend
from ml_services.experience import experience_summary
from ml_services.tourism import government_overview, tourism_summary
from ml_services.city_directory import food_directory, hotel_directory, normalize_city, directory_coverage
from ml_services.city_directory import hotel_directory_search
from ml_services.destination_estimates import estimate_destination_month, _temperature_range
from ml_services.trip_estimator import estimate_trip_cost


class DestinationServiceTests(unittest.TestCase):
    def test_alias_join_restores_all_catalog_concepts(self):
        result = destination_profiles()
        coverage = result["coverage"]
        self.assertEqual(5, coverage["catalog_unique_destinations"])
        self.assertEqual(5, coverage["matched_unique_catalog_destinations"])
        self.assertEqual(0, coverage["unmatched_catalog_destinations"])
        self.assertEqual(110, len(result["profiles"]))
        self.assertEqual(5, sum(bool(row["catalog_match"]) for row in result["profiles"]))

    def test_profiles_remain_useful_if_optional_ratings_are_missing(self):
        with patch("ml_services.experience.experience_summary", side_effect=OSError("missing ratings")):
            result = destination_profiles()
        self.assertEqual(110, len(result["profiles"]))
        self.assertTrue(all(row["observed_rating"] is None for row in result["profiles"]))

    def test_filters_rank_and_relax_when_no_full_match(self):
        exact = recommend({"region": "North", "season": "Winter"})
        self.assertEqual("matched_results", exact["mode"])
        self.assertTrue(exact["recommendations"])
        self.assertTrue(all("region" in row["matched_criteria"] for row in exact["recommendations"]))
        relaxed = recommend({"budget": 0, "region": "not-a-region"})
        self.assertEqual("relaxed_alternatives", relaxed["mode"])
        self.assertTrue(relaxed["relaxed_criteria"])
        self.assertTrue(all("alternative_notice" in row for row in relaxed["recommendations"]))

    def test_unknown_attributes_are_not_failed(self):
        candidate = _candidate({"destination": "Unknown", "state": "Unknown"},
                               {"budget": 5000, "region": "North", "interests": ["hiking"]}, None)
        self.assertEqual([], candidate["not_matched_criteria"])
        self.assertEqual(["budget", "interests", "region"], sorted(candidate["unknown_criteria"]))


class AggregateDataTests(unittest.TestCase):
    def test_rating_summary_is_aggregate_only(self):
        result = experience_summary()
        self.assertEqual("observed_rating_summary", result["kind"])
        self.assertEqual(999, result["observations"])
        self.assertEqual(0, result["destination_join_coverage"]["unmatched_rating_rows"])
        self.assertTrue(all("UserID" not in row and "HistoryID" not in row for row in result["destination_ratings"]))

    def test_monthly_statistics_are_not_forecasts(self):
        result = tourism_summary()
        self.assertEqual("historical_monthly_summary", result["kind"])
        self.assertFalse(result["data_coverage"]["year_available"])
        self.assertIsNone(result["evaluation"])
        self.assertEqual(12, len(result["series"]))
        overview = government_overview()
        self.assertEqual(432, overview["coverage"]["records"])
        self.assertTrue(overview["totals_consistent"])

    def test_empty_tourism_source_keeps_empty_buckets_explicit(self):
        with patch("ml_services.tourism._tourism_rows", return_value=[]):
            result = tourism_summary()
        self.assertEqual(0, result["data_coverage"]["records"])
        self.assertTrue(all(point["value"] is None and point["observations"] == 0 for point in result["series"]))


class CityDirectoryTests(unittest.TestCase):
    def test_documented_city_aliases_are_conservative(self):
        self.assertEqual(normalize_city("Bangalore"), normalize_city(" Bengaluru "))
        self.assertNotEqual(normalize_city("Jaipur"), normalize_city("Jaipur Rural"))

    def test_hotel_dates_are_displayed_without_unverified_validity_filter(self):
        result = hotel_directory("Bengaluru")
        self.assertGreater(result["count"], 0)
        self.assertFalse(result["date_filter_applied"])
        self.assertTrue(all("rooms" in row and "start_date" in row for row in result["items"]))

    def test_food_categories_are_source_labels_and_unknown_city_is_explicit(self):
        result = food_directory("Delhi")
        self.assertTrue(result["available"])
        self.assertEqual(["Tourist Spot", "Breakfast Spot", "Dinner Spot"], [group["category"] for group in result["groups"]])
        missing = food_directory("Not a source city")
        self.assertFalse(missing["available"])
        self.assertEqual([], missing["groups"])

    def test_directory_coverage_has_exact_city_join_method(self):
        coverage = directory_coverage()
        self.assertIn("no fuzzy matching", coverage["matching"]["method"])

    def test_hotel_directory_search_keeps_duplicate_names_and_filters_case_insensitively(self):
        result = hotel_directory_search(page=1, page_size=4)
        self.assertEqual(1212, result["total_source_rows"])
        sample = result["items"][0]
        found = hotel_directory_search(query=sample["name"].swapcase(), city=sample["city"].swapcase(),
                                       state=sample["state"].swapcase(), category=sample["category"].swapcase())
        self.assertGreater(found["total_filtered"], 0)
        self.assertGreater(result["duplicate_normalized_hotel_names_in_source"], 0)


class EstimateServiceTests(unittest.TestCase):
    def test_temperature_parser_preserves_negative_values_and_rejects_bad_ranges(self):
        self.assertEqual((-15.0, -5.0), _temperature_range("-15--5°C"))
        self.assertEqual((-5.0, 8.0), _temperature_range("-5–8 C"))
        self.assertIsNone(_temperature_range("unknown"))

    def test_month_estimates_are_deterministic_and_destination_month_sensitive(self):
        profiles = destination_profiles()["profiles"]
        profile = next(row for row in profiles if row.get("temperature_range_c") and row.get("crowd_level"))
        january = estimate_destination_month(profile["id"], 1)
        july = estimate_destination_month(profile["id"], 7)
        self.assertEqual(january, estimate_destination_month(profile["id"], 1))
        self.assertNotEqual(january["temperature"]["range"], july["temperature"]["range"])
        self.assertLessEqual(january["temperature"]["range"][1] - january["temperature"]["range"][0], 3)
        self.assertLessEqual(july["temperature"]["range"][1] - july["temperature"]["range"][0], 3)
        self.assertAlmostEqual(january["temperature"]["central_estimate"],
                               sum(january["temperature"]["range"]) / 2, places=1)
        self.assertIn(january["temperature"]["kind"], {
            "random_forest_proxy_estimate", "rules_based_approximate_estimate"})
        self.assertIn(january["crowd"]["kind"], {
            "logistic_regression_proxy_classification", "rules_based_approximate_estimate"})
        self.assertIn(january["crowd"]["level"], {"Low", "Medium", "High"})
        with self.assertRaises(ValueError):
            estimate_destination_month(profile["id"], 0)
        with self.assertRaises(LookupError):
            estimate_destination_month("missing-destination", 1)

    def test_missing_destination_model_artifacts_use_labeled_rules_fallback(self):
        profile = next(row for row in destination_profiles()["profiles"]
                       if row.get("temperature_range_c") and row.get("crowd_level"))
        with patch("ml_services.destination_models._load", return_value=None):
            result = estimate_destination_month(profile["id"], 2)
        self.assertEqual("rules_based_approximate_estimate", result["temperature"]["kind"])
        self.assertEqual("rules_based_approximate_estimate", result["crowd"]["kind"])
        self.assertIn(result["crowd"]["level"], {"Low", "Medium", "High"})

    def test_trip_cost_fallback_calculates_documented_round_trip_components(self):
        estimate = estimate_trip_cost("Unlisted city", "train", 3, 2, "vegetarian", 2)
        self.assertEqual("INR", estimate["currency"])
        self.assertEqual("round trip per traveller", estimate["transport_scope"])
        self.assertEqual(2, estimate["rooms_assumed"])
        self.assertEqual(estimate["total_inr"], sum(estimate["breakdown_inr"].values()))
        for bad in (("", "bus", 2, 3, "budget"), ("City", "car", 2, 3, "budget"),
                    ("City", "bus", 0, 3, "budget"), ("City", "bus", 2, 0, "budget"),
                    ("City", "bus", 2, 3, "other")):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                estimate_trip_cost(*bad)


if __name__ == "__main__":
    unittest.main()
