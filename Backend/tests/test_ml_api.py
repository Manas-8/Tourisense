import unittest
from unittest.mock import patch

from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash

from app import create_app
from extensions import db
from models import User


class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = "test-only-key-long-enough-for-sha256-tests"
    CORS_ORIGINS = ("http://localhost:5173", "http://localhost:5174")


class MLApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app(TestConfig)
        cls.client = cls.app.test_client()
        with cls.app.app_context():
            db.create_all()
            cls.admin = User(name="Admin", email="admin@test.invalid", password_hash=generate_password_hash("unused"), role="admin", active=True)
            cls.tourist = User(name="Tourist", email="tourist@test.invalid", password_hash=generate_password_hash("unused"), role="tourist", active=True)
            db.session.add_all([cls.admin, cls.tourist])
            db.session.commit()
            cls.admin_token = create_access_token(identity=str(cls.admin.id))
            cls.tourist_token = create_access_token(identity=str(cls.tourist.id))

    @classmethod
    def tearDownClass(cls):
        with cls.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_catalog_and_recommendation_api_use_real_source(self):
        catalog = self.client.get("/api/catalog/destinations")
        self.assertEqual(200, catalog.status_code)
        self.assertEqual(110, catalog.json["data"]["count"])
        self.assertEqual(5, catalog.json["data"]["coverage"]["matched_unique_catalog_destinations"])
        recs = self.client.post("/api/ml/recommendations", json={"budget": 12000, "interests": ["Culture"]})
        self.assertEqual(200, recs.status_code)
        self.assertEqual("transparent_content_match", recs.json["data"]["method"])
        self.assertIn("not a probability", recs.json["data"]["ranking_score_description"].lower())
        bad = self.client.post("/api/ml/recommendations", json={"budget": -1})
        self.assertEqual(400, bad.status_code)
        tourism = self.client.get("/api/ml/tourism?metric=total_tourists")
        self.assertEqual(200, tourism.status_code)
        self.assertEqual("historical_monthly_summary", tourism.json["data"]["kind"])
        self.assertFalse(tourism.json["data"]["data_coverage"]["year_available"])

    def test_missing_recommendation_source_returns_error_not_substitute(self):
        with patch("ml_services.destinations._rows", side_effect=OSError("missing source")):
            response = self.client.post("/api/ml/recommendations", json={})
        self.assertEqual(503, response.status_code)
        self.assertEqual("error", response.json["status"])
        self.assertNotIn("recommendations", response.json)

    def test_experience_summary_requires_admin_and_returns_aggregates(self):
        self.assertEqual(401, self.client.get("/api/ml/experience").status_code)
        denied = self.client.get("/api/ml/experience", headers={"Authorization": f"Bearer {self.tourist_token}"})
        self.assertEqual(403, denied.status_code)
        response = self.client.get("/api/ml/experience", headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(200, response.status_code)
        self.assertEqual(999, response.json["data"]["observations"])
        self.assertNotIn("UserID", str(response.json))
        self.assertNotIn("HistoryID", str(response.json))

    def test_dashboard_aggregate_requires_admin(self):
        self.assertEqual(401, self.client.get("/api/ml/dashboard-overview").status_code)
        response = self.client.get("/api/ml/dashboard-overview", headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(200, response.status_code)
        self.assertFalse(response.json["data"]["coverage"]["year_available"])

    def test_operational_catalogs_return_real_empty_lists(self):
        for endpoint in ("hotels", "restaurants", "transport"):
            with self.subTest(endpoint=endpoint):
                response = self.client.get(f"/api/catalog/{endpoint}")
                self.assertEqual(200, response.status_code)
                self.assertEqual([], response.json["data"]["items"])

    def test_destination_insights_and_month_estimates_validate_and_recalculate(self):
        profiles = self.client.get("/api/ml/profiles").json["data"]["profiles"]
        destination = profiles[0]
        response = self.client.get(f"/api/ml/destination-insights?destination_id={destination['id']}")
        self.assertEqual(200, response.status_code)
        self.assertIn("groups", response.json["data"]["directory"]["food"])
        self.assertEqual(400, self.client.get(f"/api/ml/destination-estimates?destination_id={destination['id']}&month=13").status_code)
        winter = self.client.get(f"/api/ml/destination-estimates?destination_id={destination['id']}&month=1")
        summer = self.client.get(f"/api/ml/destination-estimates?destination_id={destination['id']}&month=7")
        self.assertEqual(200, winter.status_code)
        self.assertEqual(200, summer.status_code)
        self.assertEqual(1, winter.json["data"]["selected_month"]["number"])
        self.assertNotEqual(winter.json["data"]["temperature"]["range"], summer.json["data"]["temperature"]["range"])
        self.assertLessEqual(winter.json["data"]["temperature"]["range"][1] - winter.json["data"]["temperature"]["range"][0], 3)
        self.assertIn("not daily weather extremes", winter.json["data"]["temperature"]["range_label"])
        self.assertLessEqual(round(winter.json["data"]["temperature"]["range"][1] - winter.json["data"]["temperature"]["range"][0], 2), 3)
        self.assertIn(winter.json["data"]["crowd"]["level"], {"Low", "Medium", "High"})
        self.assertEqual(winter.json, self.client.get(f"/api/ml/destination-estimates?destination_id={destination['id']}&month=1").json)

    def test_rules_based_trip_estimates_cover_modes_food_choices_and_unknown_city(self):
        for mode in ("bus", "train", "flight"):
            for food in ("budget", "vegetarian", "standard", "premium"):
                with self.subTest(mode=mode, food=food):
                    response = self.client.post("/api/ml/trip-estimate", json={
                        "destination": "No City In Lookup", "transport_mode": mode, "travellers": 3,
                        "duration_days": 4, "food_preference": food, "rooms": 2,
                    })
                    self.assertEqual(200, response.status_code)
                    data = response.json["data"]
                    self.assertEqual("INR", data["currency"])
                    self.assertEqual("round trip per traveller", data["transport_scope"])
                    self.assertEqual(data["total_inr"], sum(data["breakdown_inr"].values()))
                    self.assertGreater(data["per_person_inr"], 0)
        self.assertEqual(400, self.client.post("/api/ml/trip-estimate", json={"destination":"x","transport_mode":"bus","travellers":0,"duration_days":1,"food_preference":"budget"}).status_code)
        self.assertEqual(400, self.client.post("/api/ml/trip-estimate", json={"destination":"x","transport_mode":"car","travellers":1,"duration_days":1,"food_preference":"budget"}).status_code)
        self.assertEqual(400, self.client.post("/api/ml/trip-estimate", json=[]).status_code)

    def test_hotel_directory_filters_paginates_and_retains_duplicate_records(self):
        first = self.client.get("/api/catalog/hotel-directory?page=1&page_size=3")
        self.assertEqual(200, first.status_code)
        data = first.json["data"]
        self.assertEqual(1212, data["total_source_rows"])
        self.assertEqual(3, len(data["items"]))
        second = self.client.get("/api/catalog/hotel-directory?page=2&page_size=3")
        self.assertEqual(200, second.status_code)
        self.assertNotEqual([item["id"] for item in data["items"]], [item["id"] for item in second.json["data"]["items"]])
        sample = data["items"][0]
        filtered = self.client.get(f"/api/catalog/hotel-directory?q={sample['name']}&city={sample['city']}&state={sample['state']}&category={sample['category']}")
        self.assertGreater(filtered.json["data"]["total_filtered"], 0)
        self.assertEqual(400, self.client.get("/api/catalog/hotel-directory?page=0").status_code)

    def test_status_handles_missing_directory_source(self):
        with patch("ml_services.city_directory._csv", side_effect=OSError("source absent")):
            response = self.client.get("/api/ml/status")
        self.assertEqual(200, response.status_code)
        self.assertFalse(response.json["data"]["services"]["directories"]["available"])
        self.assertIsNone(response.json["data"]["datasets"]["directory_coverage"])

    def test_directory_endpoints_validate_city_and_show_unavailable(self):
        self.assertEqual(400, self.client.get("/api/catalog/food").status_code)
        response = self.client.get("/api/catalog/food?city=NoSourceCity")
        self.assertEqual(200, response.status_code)
        self.assertFalse(response.json["data"]["available"])
        hotels = self.client.get("/api/catalog/directory-hotels?city=Bengaluru")
        self.assertEqual(200, hotels.status_code)
        self.assertGreater(hotels.json["data"]["count"], 0)
        with patch("ml_services.city_directory._csv", side_effect=OSError("source missing")):
            missing = self.client.get("/api/catalog/food?city=Delhi")
        self.assertEqual(503, missing.status_code)

    def test_model_status_is_admin_only_and_does_not_expose_evaluation_metrics(self):
        self.assertEqual(401, self.client.get("/api/ml/model-status").status_code)
        self.assertEqual(403, self.client.get("/api/ml/model-status", headers={"Authorization": f"Bearer {self.tourist_token}"}).status_code)
        response = self.client.get("/api/ml/model-status", headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(200, response.status_code)
        self.assertNotIn("evaluation", response.json["data"])
        self.assertNotIn("metrics", response.json["data"])
        self.assertIn("trip_cost_model_available", response.json["data"])
        self.assertTrue(response.json["data"]["crowd_prediction_available"])
        self.assertTrue(response.json["data"]["temperature_prediction_available"])

    def test_destination_insights_do_not_expose_model_metrics(self):
        response = self.client.get("/api/catalog/destinations")
        destination_id = response.json["data"]["items"][0]["id"]
        details = self.client.get(f"/api/ml/destination-insights?destination_id={destination_id}")
        self.assertEqual(200, details.status_code)
        self.assertNotIn("booking_volume_model", details.json["data"])
        self.assertNotIn("evaluation", str(details.json))

    def test_trip_cost_input_validation_and_prediction_output(self):
        invalid = self.client.post("/api/ml/trip-cost-estimate", json={})
        self.assertEqual(400, invalid.status_code)
        self.assertEqual(400, self.client.post("/api/ml/trip-cost-estimate", json=["invalid-shape"]).status_code)
        response = self.client.post("/api/ml/trip-cost-estimate", json={
            "destination_city": "Leh", "destination_country": "India", "meal_plan": "Breakfast Included",
            "transportation_type": "Flight", "travellers": 5, "adults": 3, "children": 2,
            "rooms": 3, "nights": 3, "hotel_rating": 4.6, "lead_days": 54,
            "travel_month": 4, "travel_dayofweek": 5,
        })
        self.assertEqual(200, response.status_code)
        self.assertEqual("source cost units (currency not recorded)", response.json["data"]["unit"])
        self.assertNotIn("INR", response.json["data"]["unit"])

    def test_trip_cost_endpoint_reports_missing_artifact_as_unavailable(self):
        from pathlib import Path
        with patch("ml_services.supervised.COST_MODEL_PATH", Path("missing-cost-model-joblib")):
            response = self.client.post("/api/ml/trip-cost-estimate", json={
                "destination_city": "Leh", "destination_country": "India", "meal_plan": "Breakfast Included",
                "transportation_type": "Flight", "travellers": 2, "adults": 2, "children": 0,
                "rooms": 1, "nights": 2, "hotel_rating": 4.0, "lead_days": 30,
                "travel_month": 4, "travel_dayofweek": 3,
            })
        self.assertEqual(503, response.status_code)
        self.assertEqual("error", response.json["status"])

    def test_cost_prediction_without_artifact_is_unavailable(self):
        from ml_services import supervised
        from pathlib import Path
        with patch.object(supervised, "COST_MODEL_PATH", Path("missing-cost-model-joblib")):
            with self.assertRaises(FileNotFoundError):
                supervised.trip_cost_prediction({})


if __name__ == "__main__":
    unittest.main()
