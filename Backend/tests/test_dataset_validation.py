import unittest

from ml_services.dataset_validation import validate_datasets


class DatasetValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = validate_datasets()

    def test_expected_source_schemas_and_row_counts_are_reported(self):
        self.assertEqual("ok", self.result["status"])
        datasets = self.result["datasets"]
        self.assertEqual(1000, datasets["Destinations.csv"]["rows"])
        self.assertEqual(110, datasets["tourism_statistics.csv"]["rows"])
        self.assertEqual(432, datasets["user_visits.xlsx"]["rows"])
        self.assertEqual([], datasets["Travel And Tourism.csv"]["missing_required_columns"])
        self.assertEqual({}, datasets["hotel_bookings_updated_2024.csv"]["invalid_date_values_by_column"])
        self.assertTrue(self.result["expected_row_counts_are_audit_snapshots_not_enforced"])

    def test_relationships_and_local_image_manifest_are_explicit(self):
        datasets = self.result["datasets"]
        self.assertEqual(999, datasets["relationships"]["rating_destination_id_matches"])
        self.assertTrue(datasets["relationships"]["catalog_ids_unique"])
        self.assertEqual(0, datasets["relationships"]["ratings_outside_1_to_5"])
        self.assertEqual(110, datasets["relationships"]["destination_profile_resolution"]["metadata_rows"])
        self.assertEqual(50, datasets["relationships"]["hotel_food_city_coverage"]["matching"]["shared_unique_cities"])
        self.assertEqual(44, datasets["source_semantics"]["hotel_normalized_duplicate_name_rows"])
        self.assertTrue(datasets["source_semantics"]["tourism_state_month_pairs_unique"])
        self.assertEqual(0, datasets["source_semantics"]["tourism_totals_not_domestic_plus_foreign"])
        self.assertFalse(datasets["source_semantics"]["tourism_year_column_present"])
        self.assertGreater(datasets["destination_images"]["mapped_destinations"], 0)
        self.assertEqual([], datasets["destination_images"]["missing_mapped_files"])
        self.assertTrue(datasets["destination_images"]["fallback_available"])


if __name__ == "__main__":
    unittest.main()
