# Tourisense backend: code and API guide

This guide describes the backend files currently present in this repository and how requests move through them. It was prepared by reading the source tree; it does not start the server, connect to MySQL, execute the notebooks, or modify source datasets. The only file added for this task is this guide.

## 1. What the backend does

Tourisense's backend is a Flask JSON API. It has two kinds of data paths:

1. **Operational records** use SQLAlchemy models and the configured MySQL database. Authentication, user profiles, check-ins, and the operational hotel, restaurant, and transport catalogs use this path.
2. **Analytics and reference data** are read directly from CSV/XLSX files under `Backend/Data`. Destination profiles, recommendations, tourism summaries, hotel directory search, food guides, and estimates use this path. These files are not automatically imported into MySQL.

Some features have similarly named but distinct implementations. The tourist trip planner uses configured, rules-based INR rates. A separate experimental trip-cost model predicts an undocumented source cost unit. Hotel directory CSV rows are not the same thing as operational hotel rows in MySQL. Read the endpoint descriptions below with those distinctions in mind.

## 2. Request flow and shared infrastructure

`app.py` creates the Flask app, loads `Config`, enables CORS for the listed local frontend origins, initializes SQLAlchemy, Flask-Migrate, and JWT, registers five route blueprints, installs JWT error responses, and starts a scheduler outside testing. The scheduler runs a three-minute placeholder that only logs that data refresh is not configured; it does not scrape or change data. The module exports a ready-to-use `app` and supports `python app.py` for local development.

The `seed-admin` Flask CLI command creates one active admin account from `ADMIN_EMAIL`, `ADMIN_PASSWORD`, and optional `ADMIN_NAME` environment variables. It refuses to overwrite an existing account. `/api/health` checks app responsiveness; `/api/health/db` executes `SELECT 1` and reports a generic connected/disconnected result.

`extensions.py` defines unbound shared `db`, `jwt`, and `migrate` extension objects. `config.py` loads `Backend/.env` if present and reads `DATABASE_URL`, `JWT_SECRET_KEY`, and token lifetime from the environment. It also defines the local CORS origins. Configuration values are not hard-coded database credentials.

`auth_utils.py` holds reusable request/auth helpers: email normalization and validation, the password policy, a safe public user representation, JWT identity lookup, role enforcement, JSON errors, and claim access. `require_roles` is used by admin analytics endpoints. `models.py` is the SQLAlchemy schema described in section 5.

## 3. HTTP API reference

All routes return JSON. Unless noted, successful API responses use `status: "ok"` and an error response uses `status: "error"` with an explanatory `error`. Protected routes expect `Authorization: Bearer <JWT>`.

### Health and identity

| Method and path | Access | Purpose |
| --- | --- | --- |
| `GET /` | Public | Minimal backend identity response. |
| `GET /api/health` | Public | Confirms the Flask process responds. It does not check database health. |
| `GET /api/health/db` | Public | Runs a simple database connection query; returns 503 if SQLAlchemy cannot connect. |

### Authentication and profile

| Method and path | Access | Purpose and behavior |
| --- | --- | --- |
| `POST /api/auth/register` | Public | Accepts `name`, `email`, and `password`; creates a tourist account with a password hash, then returns a JWT and safe user data. Rejects malformed email, weak password, duplicate email, and the reserved `admin@gmail.com` address. |
| `POST /api/auth/login` | Public | Accepts email/password; verifies the password hash and active status; returns a JWT and safe user data. Invalid login details produce a generic 401. |
| `GET /api/users/me` | JWT | Looks up the token's user and returns safe profile data. Inactive or missing users are rejected. |
| `PATCH /api/users/me` | JWT | Updates the caller's `name` and/or `email`. Role, ID, active state, and password hash cannot be edited here. Email format, reservation, and uniqueness are checked. |

JWT identities are stored as stringified user IDs. Tokens also carry a role claim. The app normalizes missing, invalid, expired, and revoked-token errors in `app.py`.

### Catalog and source directories

| Method and path | Access | Purpose and source |
| --- | --- | --- |
| `GET /api/catalog/destinations` | Public | Returns metadata-based destination profiles, profile coverage, ratings where the source join is verified, and compatibility fields such as `location`, `budget`, and `bestTime`. Reads `tourism_statistics.csv`, related catalog/rating sources, and travel-cost match metadata. |
| `GET /api/catalog/hotels` | Public | Returns active `Hotel` rows from operational MySQL, with optional `q` and `location` substring filters. Not the CSV directory. |
| `GET /api/catalog/restaurants` | Public | Returns active operational MySQL restaurant rows, with the same filters. |
| `GET /api/catalog/transport` | Public | Returns active operational MySQL transport rows, with the same filters. |
| `GET /api/catalog/directory-hotels?city=...` | Public | Lists CSV hotel directory entries for a required city. Source dates are displayed but not used to assert current registration or availability. |
| `GET /api/catalog/hotel-directory` | Public | Searchable CSV directory. Optional `q`, `city`, `state`, `category`, `page` (default 1), and `page_size` (default 50, max 100). Keeps duplicate source records and returns facets and limitations. |
| `GET /api/catalog/food?city=...` | Public | Returns the source food/tourist spot guide for a required city. The source categories are tourist spots, breakfast spots, and dinner spots. |
| `GET /api/catalog/directory-coverage` | Public | Reports hotel/food row and city coverage and exact normalized city overlap. |

Operational listings query MySQL models and catch database errors, roll back the session, and return 503. Directory endpoints read files and return 503 when source data is unavailable. Neither kind of catalog should be interpreted as live inventory unless the source actually supports that claim.

### Recommendations, analytics, and estimates

| Method and path | Access | Purpose and inputs |
| --- | --- | --- |
| `GET /api/ml/status` | Public | Reports availability and source coverage for recommendation, tourism, experience, cost, crowd, temperature, and directory services, along with dataset row counts and limitations. Does not report model evaluation scores. |
| `POST /api/ml/recommendations` | Public | JSON filters: `interests` (up to 20 strings), optional `region`, `season`, `crowd`, `budget` (0–100,000,000), and `duration_days` (0–60). Returns transparent content-based ranking and explanations/relaxed alternatives. Scores are ranking values, not probabilities. |
| `GET /api/ml/profiles` | Public | Returns canonical destination profile data and source-join coverage. |
| `GET /api/ml/dashboard-overview` | Admin JWT | Aggregated historical tourism overview from the XLSX workbook. It is not a year-over-year dashboard or forecast. |
| `GET /api/ml/tourism?state=...&metric=...` | Public | Historical monthly/state summary. `state` is optional; metric defaults to `total_tourists`. Invalid metric/state inputs are validated by the service. No year means no future forecast. |
| `GET /api/ml/experience` | Admin JWT | Aggregated observed ratings by destination and overall. It does not return person-level visit history or predict ratings. |
| `GET /api/ml/model-status` | Admin JWT | Model artifact availability, unsupported occupancy status, and caveats. Evaluation metrics are intentionally not returned. |
| `GET /api/ml/destination-insights?destination_id=...` | Public | Returns a destination profile, metadata reference facts, best-effort hotel/food directory lookup using destination name or nearest major city, and an explicitly matched travel-cost sample destination if available. |
| `GET /api/ml/destination-estimates?destination_id=...&month=1..12` | Public | Estimates a monthly temperature band and crowd category from proxy models when available, otherwise rules. These are seasonal approximations, not observed weather or verified crowd forecasts. |
| `POST /api/ml/trip-estimate` | Public | Rules-based INR planning estimate. JSON: `destination` (profile ID or name), `transport_mode` (`bus`, `train`, `flight`), `travellers` (1–30), `duration_days` (1–60), `food_preference` (`budget`, `vegetarian`, `standard`, `premium`), optional `rooms` (1–15). |
| `POST /api/ml/trip-cost-estimate` | Public | Experimental supervised cost estimate. Requires destination city/country, meal plan, transportation type, counts, room/night/calendar inputs, and hotel rating. Inputs must be represented in `Travel And Tourism.csv`; result unit is source cost units because currency is unknown. It is not the planner's INR estimator. |
| `POST /api/trips/checkin` | JWT, multipart form | Saves a check-in for `activity_id`, optional `notes`, and optional `photo` upload. The image is saved under the app's `uploads` folder and the database stores its URL. |

Validation errors generally return 400, unknown destination records 404, and unreadable source data or missing required resources 503. The exact response fields differ slightly for the older check-in endpoint, which uses `error`/`message` without the common status wrapper.

## 4. File-by-file guide

### Backend root files

- **`app.py`** — Flask application factory and local entry point. Wires settings, CORS, database, migrations, JWT callbacks, routes, scheduler placeholder, admin seeding command, and health endpoints.
- **`auth_utils.py`** — Shared validation and JWT authorization helpers. `safe_user` prevents password hashes and internal fields from leaking into responses; role checks protect admin routes.
- **`config.py`** — Environment-backed database/JWT configuration and allowed local frontend origins. Loads the backend `.env` when it exists.
- **`extensions.py`** — Creates extension instances before app initialization, avoiding circular ownership between app and models.
- **`models.py`** — Database schema for users, reference/operational destination catalog, trips and itinerary, saved places, and check-ins. Mixins provide timestamps; relationships and constraints encode ownership and uniqueness.
- **`README.md`** — Setup instructions for MySQL, environment variables, migrations, starting the server, admin seed command, and the original health/auth API overview. The README's statement that catalog/analytics APIs are absent is stale relative to the current route code; use this guide and current code for actual routes.
- **`ML_README.md`** — Explains source consumers, recommendation approach, proxy model caveats, planner-vs-experimental cost paths, evaluation and dataset validation commands.
- **`DATASET_INVENTORY.md`** — Data dictionary and audit notes for each source, row counts observed when checked, known join and quality limitations, plus UI/API consumer mapping.
- **`requirements.txt`** — Python package pins for Flask, JWT, CORS, migrations, SQLAlchemy, MySQL driver, dotenv, pandas, scikit-learn, and joblib.

### Route modules (`routes/`)

- **`routes/__init__.py`** — Empty package marker so routes can be imported as a Python package.
- **`routes/auth.py`** — Public registration and login endpoints. Hashes passwords with Werkzeug; issues JWTs with role claims; prevents public registration for the reserved admin address.
- **`routes/users.py`** — Authenticated self-profile read/update endpoints. Restricts profile editing to name/email and validates unique emails.
- **`routes/catalog.py`** — Combines metadata destination profiles with MySQL operational catalogs and CSV directories. Includes shared query/location filtering for operational lists, hotel directory pagination/search, food lookups, and city coverage.
- **`routes/ml.py`** — API adapter for recommendation and analytics services. Validates request payloads, maps service results to JSON and HTTP status codes, applies admin checks, and provides the status endpoint. It also contains the experimental endpoint's source-category checks before calling the model service.
- **`routes/trips.py`** — Authenticated multipart check-in creation. Accepts an activity ID, optional note/photo, saves the file and creates a `CheckIn` row.

### ML and data services (`ml_services/`)

- **`ml_services/__init__.py`** — Empty package marker.
- **`ml_services/destinations.py`** — Reads destination CSV sources, normalizes names/states, joins metadata to the repeated-ID catalog only through exact keys and reviewed aliases, computes observed rating aggregates, builds profiles, applies recommendation filters, scores content matches, and returns ranked candidates with criteria explanations. It is transparent content ranking, not a fitted recommendation model.
- **`ml_services/tourism.py`** — Reads the first worksheet of `user_visits.xlsx` using ZIP/XML parsing (so it does not rely on Excel automation), normalizes monthly records, computes tourism summaries by state/metric, and creates government overview aggregates. The workbook has month but no year.
- **`ml_services/experience.py`** — Reads the destination ratings source and produces aggregate observed-rating summaries. Personal identifiers and visit-level history are not returned.
- **`ml_services/city_directory.py`** — Shared CSV-backed city services. Normalizes city spellings with a small explicit alias list, searches and paginates hotel directory records, reads city food guide categories, reports city coverage, and matches a destination to the experimental travel cost sample with exact normalized/explicit-alias matching.
- **`ml_services/trip_estimator.py`** — Tourist-facing estimate calculator. Validates inputs, resolves a destination profile to an economy/standard/premium tier, loads JSON rates, estimates transport, rooms, meals, local transport, and activities, rounds components, and returns a labeled INR estimate with method caveats.
- **`ml_services/destination_estimates.py`** — Builds month-specific destination estimates. It combines destination reference temperature, region/month offsets, state or all-state tourism seasonality, crowd reference labels, and optional proxy model outputs. Explicitly labels when unavailable or approximate.
- **`ml_services/destination_models.py`** — Cached loading and inference for two serialized proxy pipelines. Builds the feature rows expected by temperature/crowd models and gracefully falls back when files cannot load or predict.
- **`ml_services/supervised.py`** — Loads the experimental trip-cost model artifact and stored evaluation report. Prepares one prediction row and returns a source-unit cost prediction with model/evaluation metadata and caveat; missing artifacts are unavailable, not retrained during requests.
- **`ml_services/train_models.py`** — Offline training/retraining workflow for the experimental trip cost regression pipeline. Creates a chronological holdout, fits preprocessing/model on training rows, computes metrics/baseline, and may write the model and evaluation JSON. Running it changes generated artifacts.
- **`ml_services/evaluate_models.py`** — Command-line wrapper for fresh cost-model evaluation that prints metrics without intentionally refreshing saved artifacts.
- **`ml_services/dataset_validation.py`** — Read-only source audit: required headers, row counts, missing/duplicate/invalid values, joins, city coverage, JSON availability, and local image mapping. It reports current counts rather than enforcing a frozen count and avoids deserializing model files.

### Database migrations (`migrations/`)

- **`migrations/alembic.ini`** — Alembic configuration template for migration generation and execution.
- **`migrations/env.py`** — Connects Alembic to the Flask app's SQLAlchemy engine/metadata and runs migrations online or offline.
- **`migrations/README`** — Standard Alembic-generated migration notes.
- **`migrations/script.py.mako`** — Template used when Alembic creates a new revision file.
- **`migrations/versions/0683d0e5d8fa_initial_schema.py`** — Initial schema migration, creating the first relational tables and constraints.
- **`migrations/versions/6f5facefb68d_.py`** — Follow-up migration after the initial schema; inspect its `upgrade`/`downgrade` operations to see the precise delta for a target database version.

### Tests (`tests/`)

- **`tests/test_ml_api.py`** — Flask test-client coverage for routes, role gates, validation, source-unavailable behavior, directory filtering, and model endpoint behavior. It uses a test configuration and mocks where needed.
- **`tests/test_ml_services.py`** — Unit-level expectations for source matching, recommendation ranking, tourism/rating aggregates, city normalization, directory behavior, monthly estimates, and trip-cost calculation.
- **`tests/test_dataset_validation.py`** — Checks the dataset validator reports schemas/counts and documents relationship/image-manifest information.
- **`tests/test_evaluation_metrics.py`** — Checks that regression metric calculation includes its expected metrics.

## 5. Database model map

The model classes in `models.py` describe tables; routes do not automatically populate these tables from CSV files.

- **`User`** stores name, unique email, password hash, role, and active flag. It owns trips, saved places, and check-ins.
- **`Destination`** is the operational relational destination table (slug, city/state/country/category, descriptions, schedule/budget, rating, image and coordinates). Current destination profile API data is sourced from CSV metadata and should not be assumed to have been imported here.
- **`Attraction`** belongs to a destination and can be linked to itinerary activities.
- **`Hotel`** and **`Restaurant`** belong to a destination and hold operational catalog fields. They are separate from `hotels.csv` and the food guide.
- **`TransportOption`** optionally belongs to a destination and stores type, route, starting cost, and duration text.
- **`Trip`** belongs to a user and destination; carries dates, duration, travelers, preferences, status, and a random share ID.
- **`TripInterest`** stores unique interest labels per trip.
- **`ItineraryDay`** stores an ordered day for a trip; **`ItineraryActivity`** stores ordered activities, optional attraction link, timing, duration, and cost.
- **`SavedPlace`** links a user to exactly one destination, hotel, or restaurant. Check and unique constraints enforce a single target and prevent duplicate saves per type.
- **`CheckIn`** associates a user and itinerary activity with optional photo URL and notes.
- **`TimestampMixin`** supplies UTC creation/update fields to the models that inherit it. `generate_share_id()` creates random hex IDs for trip sharing.

## 6. Data, model artifacts, and notebook files

Source data lives under `Data/`; callers resolve paths relative to the backend, so the app reads these files in place. Key sources are:

- **`Data/tourism_statistics.csv`** — 110 destination metadata profiles, despite the filename. Canonical content for destination cards, recommendation features, and reference facts.
- **`Data/Destinations.csv`** — 1,000 ID rows but only five repeated destination concepts. Used for carefully verified joins and popularity tie-breaking, not a 1,000-destination catalog.
- **`Data/destination_details.csv`** — Visit-level ratings; service outputs aggregates only.
- **`Data/user_visits.xlsx`** — 432 state/month tourism rows without year; historical/cross-sectional summaries and seasonal ratios only.
- **`Data/hotels.csv`** — Directory records, not live booking or availability data.
- **`Data/india-tourism-food-dataset.csv`** — City food/tourist-spot labels returned as source guidance.
- **`Data/Travel And Tourism.csv`** — Separate booking-like cost sample used for experimental regression and destination matching. Currency/target meaning is undocumented.
- **`Data/hotel_bookings_updated_2024.csv`** — Retained for validation/reference; there is no active deployed booking/cancellation model.

Other files:

- **`config/trip_cost_rates.json`** — Editable INR assumptions for the rules-based planner, including transport round-trip allowances, destination tiers, per-person meals/activities/local transport, room capacity, and rounding.
- **`artifacts/trip_cost.joblib`** — Serialized experimental trip-cost preprocessing/model pipeline loaded for inference.
- **`artifacts/evaluation.json`** — Saved experimental model evaluation report produced by the explicit training refresh workflow.
- **`artifacts/destination_temperature_rf.joblib`** — Random Forest pipeline for a temperature proxy estimate.
- **`artifacts/destination_crowd_logistic.joblib`** — Logistic Regression pipeline for a crowd proxy category.
- **`ML_Notebooks/random_forest_regressor.ipynb`** and **`ML_Notebooks/logistic_regression.ipynb`** — Notebook development/training material for the temperature and crowd proxy models. Their target labels are constructed proxies, not observed weather/crowd outcomes.

`venv/` is the local Python environment and contains third-party packages, executables, and their own test/data files. It is not Tourisense application source and is intentionally not described file by file here. `__pycache__/` files are generated Python bytecode and are also omitted.

## 7. Important behavior and limits to keep in mind

1. CSV/XLSX analytics sources are read in place; they are not synchronized into relational tables by the inspected backend.
2. Destination recommendations are explainable content matching. A ranking score is not a probability or confidence value.
3. Tourism workbook rows have no year, so they cannot support chronological or future forecasts.
4. Temperature and crowd models learn proxy labels derived from metadata and seasonal rules. Their outputs are not verified forecasts.
5. The tourist estimator returns approximate INR planning costs from editable assumptions, not live quotes. The experimental regression endpoint has no known currency and is separate.
6. Hotel room counts and source dates are directory fields, not current availability or occupancy. Booking data cannot be reconciled to directory hotel identities/capacity.
7. MySQL-backed operational catalogs can be empty even when CSV directory sources contain rows.
8. The current root README predates some routes. For active behavior, inspect `app.py` and the route modules; `ML_README.md` and `DATASET_INVENTORY.md` provide current analytics context.

## 8. Suggested reading order

To learn the request path, read `app.py` → the relevant file under `routes/` → the service it calls under `ml_services/` → `models.py` (for database-backed paths) or `DATASET_INVENTORY.md` (for file-backed paths). For a first end-to-end example, follow `POST /api/ml/trip-estimate` from `routes/ml.py` to `ml_services/trip_estimator.py` and then `config/trip_cost_rates.json`.
