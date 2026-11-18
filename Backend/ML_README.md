# TouriSense data and machine-learning services

This document describes the current sources and their actual consumers. Source CSV/XLSX files are read in place; the application does not import them into operational MySQL tables. See [DATASET_INVENTORY.md](DATASET_INVENTORY.md) for each complete source schema, validation observations, and consumer mapping.

## Canonical destination profiles and source matching

`tourism_statistics.csv` contains 110 unique destination metadata profiles. These are the canonical profiles shown in the catalog, details pages, and recommendation results. `Destinations.csv` has 1,000 unique row IDs but only five distinct name/state concepts repeated 200 times each. It is not treated as a 1,000-place catalog. The service groups those repeated rows by normalized exact name/state, averages the available `Popularity` values for the group, and uses the source IDs only to join visit ratings. Three reviewed aliases connect `Taj Mahal` to Agra, `Goa Beaches` to Goa, and `Jaipur City` to Jaipur. No fuzzy or row-order match is used.

Current destination resolution covers all five unique catalog concepts and all 1,000 source catalog rows; only five of the 110 metadata profiles have a verified catalog-ID relationship. The other 105 metadata profiles remain available for content recommendations and details, with catalog-derived popularity and ratings unknown. Profiles use stable normalized name/state keys rather than repeated source IDs.

`destination_details.csv` contains 999 valid 1–5 `ExperienceRating` observations and every row's `DestinationID` matches a catalog ID. The service returns overall and destination aggregates only; it does not return user IDs, visit dates, or individual history. There is no trained rating prediction model.

Recommendations use transparent content matching on region, season, budget, duration, crowd label, category, and audience interests. The weighted score is a **ranking score**, not a probability, model confidence, or predicted likelihood of visiting. Unknown attributes do not fail filters; relaxed alternatives identify unmet criteria. Source popularity is only a minor tie-breaker where a verified catalog join exists.

## Historical tourism, monthly estimates, and limitations

`user_visits.xlsx` has 432 state/month records (36 states × 12 months) and no year. `tourism_statistics.csv` is destination metadata, despite its filename. The workbook supports month-grouped historical profiles only: no chronological forecast, latest-year label, or future tourism prediction is produced. Totals reconcile to domestic plus foreign tourists in every source row. Government analytics label these as historical/cross-sectional values and expose covered states/observations.

Monthly destination temperature uses the Random Forest pipeline saved at `artifacts/destination_temperature_rf.joblib`; crowd uses the Logistic Regression pipeline saved at `artifacts/destination_crowd_logistic.joblib`. Both are trained in `ML_Notebooks/random_forest_regressor.ipynb` and `ML_Notebooks/logistic_regression.ipynb` and loaded once per backend process. Their targets are proxies derived from source temperature ranges, regional month adjustments, destination crowd metadata, and the year-free tourism profile. No observed monthly temperature targets or verified month-specific crowd labels exist, so notebook metrics measure agreement with proxy rules, not real-world forecast accuracy. The website displays an estimated temperature band no wider than 3°C and one of Low, Medium, or High for crowd. Missing artifacts use explicitly labelled rules-based fallbacks. Models are not trained at startup or during requests.

The hotel-booking dataset is retained for source validation/reference only. Cancellation classification and booking-row demand experiments have been removed; no booking model is trained or deployed by the project. Booking rows would not equal visitors, room occupancy, or availability, and there is no reconciled capacity denominator. The supplied hotel directory's `Total Rooms` is directory metadata, not live room availability.

## Trip cost

The tourist planner uses the existing rules-based `POST /api/ml/trip-estimate` service and `Backend/config/trip_cost_rates.json`. It returns a labelled approximate INR planning breakdown with round-trip transport. This path remains the user-facing estimator.

`Travel And Tourism.csv` feeds a separate experimental Random Forest endpoint, `POST /api/ml/trip-cost-estimate`. Its `Total_Trip_Cost` has no documented currency or confirmed quoted/paid semantics. The endpoint reports **source cost units (currency not recorded)** and must not be combined with INR rates or presented as an INR quote. It is not called by the tourist frontend. The stored artifact is [`artifacts/trip_cost.joblib`](artifacts/trip_cost.joblib); inference loads it without retraining. If it is missing, inference returns unavailable.

The hotel cancellation and booking-demand models are not part of this project’s active ML workflows. The hotel booking CSV is not used to train a model, serve predictions, or populate dashboard metrics.

## Stored evaluation results

Evaluation metrics are terminal-only and are not shown in either frontend or returned by APIs. Use the fresh evaluation commands below; they recompute diagnostics without writing artifacts or `artifacts/evaluation.json`.

The remaining trip-cost evaluation uses a chronological `Booking_Date` split. Preprocessing is fit as part of its training pipeline on the training partition only.

Run from `Backend` with the project virtual environment activated:

```powershell
python -m ml_services.evaluate_models trip-cost
```

This command recomputes the experimental trip-cost Random Forest evaluation and prints regression metrics and its baseline to stdout. Cancellation and booking-demand evaluations are no longer available. Trip cost remains in source units because its currency is undocumented.

## APIs and authentication

* `GET /api/catalog/destinations` — 110 metadata profiles, join coverage, optional observed rating aggregates.
* `POST /api/ml/recommendations` — content ranking with criteria explanations and relaxed-alternative labels.
* `GET /api/ml/destination-insights?destination_id=...` — reference metadata and explicitly qualified directory lookups.
* `GET /api/ml/destination-estimates?destination_id=...&month=1` ? proxy-trained temperature and crowd estimates when artifacts are available; explicitly labelled rules-based fallback otherwise; month must be 1?12.
* `POST /api/ml/trip-estimate` — configured approximate INR estimate.
* `POST /api/ml/trip-cost-estimate` — experimental source-unit model endpoint; not used by the tourist frontend.
* `GET /api/ml/tourism` and `GET /api/ml/dashboard-overview` — historical workbook aggregations. The dashboard overview is admin-only.
* `GET /api/ml/experience` and `GET /api/ml/model-status` — aggregate ratings and model availability/limitations; both admin-only. Evaluation metrics are not returned by APIs.
* `GET /api/catalog/hotel-directory` and `/api/catalog/food` — CSV hotel directory and food/attraction guide.
* `/api/catalog/hotels`, `/restaurants`, and `/transport` — operational MySQL listings, separate from CSV references. Live database contents were not verified for this documentation update.

Trip drafts, saved places, and itinerary state in the tourist frontend remain in browser `localStorage`; they are not presented as database-synced records. The map control opens an OpenStreetMap search by destination text; source coordinates and custom map markers are unavailable. The current build manifest maps 109 of 110 profile names to local destination images; the remaining name uses the local fallback.

## Validation and safe refresh

Run the read-only dataset checks from `Backend`:

```powershell
.\venv\Scripts\Activate.ps1
python -m ml_services.dataset_validation
```

The validator reports required headers, current row counts, blank cells, exact duplicates, numeric/date parse issues, rating/catalog ID joins, destination resolution coverage, city-directory overlap, JSON availability, and local image mappings. Snapshot row counts are informational and are not enforced as fixed values. It does not modify source files or deserialize the model artifact.

To refresh the experimental cost model and its evaluation report, run from `Backend`:

```powershell
python -m ml_services.train_models
```

Unlike the evaluation-only command, this retraining workflow writes `artifacts/evaluation.json` and may replace the experimental cost artifact when its chronological holdout MAE beats baseline. Use it only when intentionally refreshing saved outputs. Prediction requests do not train models. Review provenance, headers, dates, joins, missingness, leakage, target semantics, and currency before treating results as useful. Never import these CSVs into operational tables without an explicit identity and ownership mapping.
