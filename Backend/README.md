# Tourisense Backend

This Flask backend now includes the initial Tourisense relational schema and MySQL migration support, plus JWT-based user authentication. It still does not include destinations, hotels, restaurants, transport, trips, itineraries, saved places, AI, or analytics APIs.

## MySQL prerequisites

Install and start the local MySQL Server. The default configuration expects:

- host: `localhost`
- port: `3306`
- database: `tourisense`

In Windows, confirm that the MySQL service is running through **Services** (`services.msc`), or start it from an elevated PowerShell prompt if its installed service name is `MySQL80`:

```powershell
Start-Service MySQL80
```

## Configure the local environment

`Backend/.env` is created locally and ignored by Git. Replace `YOUR_PASSWORD` in that file with your local MySQL password; never place the password in source code or this README.

```env
DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/tourisense
JWT_SECRET_KEY=replace-with-a-long-random-secret
JWT_ACCESS_TOKEN_EXPIRES_HOURS=24
```

If a password contains URL-reserved characters such as `@`, `:`, `/`, or `#`, URL-encode it before placing it in `DATABASE_URL`.

## Create the empty database

After configuring the password, use the MySQL client locally. It prompts for the password rather than putting it into the command:

```powershell
mysql -u root -p -h localhost -P 3306 -e "CREATE DATABASE IF NOT EXISTS tourisense;"
```

This command creates only the empty `tourisense` database. It creates no tables.

## Initial schema and migrations

The backend uses Flask-Migrate and Alembic to manage the schema. The first migration creates these tables:

- `users`
- `destinations`
- `attractions`
- `hotels`
- `restaurants`
- `transport_options`
- `trips`
- `trip_interests`
- `itinerary_days`
- `itinerary_activities`
- `saved_places`

To apply the schema to MySQL:

```powershell
cd E:\Toursense\Backend
.\venv\Scripts\python.exe -m flask --app app db upgrade
```

To create new migrations later after model changes:

```powershell
cd E:\Toursense\Backend
.\venv\Scripts\python.exe -m flask --app app db migrate -m "describe the change"
```

## Activate the existing virtual environment (Windows PowerShell)

```powershell
cd E:\Toursense\Backend
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution, run the server with the virtual environment's Python directly instead:

```powershell
E:\Toursense\Backend\venv\Scripts\python.exe E:\Toursense\Backend\app.py
```

## Start the backend

```powershell
python app.py
```

## Create the development administrator

Add the following values to your local `Backend/.env` (the file is ignored by Git), then run the command once. The command creates an `admin` user in the existing `users` table and never changes an existing account.

```env
ADMIN_EMAIL=admin@gmail.com
ADMIN_PASSWORD=use-a-strong-development-password
ADMIN_NAME=Government Administrator
```

```powershell
cd E:\Tourisense\Backend
.\venv\Scripts\python.exe -m flask --app app seed-admin
```

The server listens at `http://127.0.0.1:5000` by default.

## Endpoints

- `GET /` returns a basic backend identity message.
- `GET /api/health` returns:

  ```json
  {
    "message": "Tourisense backend is running",
    "status": "ok"
  }
  ```
- `GET /api/health/db` attempts a MySQL connection and returns either:

  ```json
  {
    "database": "connected",
    "status": "ok"
  }
  ```

  or HTTP `503` without exposing connection details:

  ```json
  {
    "database": "disconnected",
    "status": "error"
  }
  ```

- `POST /api/auth/register` creates a tourist account and returns `{ token, user }`.
- `POST /api/auth/login` authenticates a user and returns `{ token, user }`.
- `GET /api/users/me` returns the current user profile and requires a Bearer token.
- `PATCH /api/users/me` updates the current user name and/or email and requires a Bearer token.

Test the health endpoints in a browser or PowerShell at:

```text
http://127.0.0.1:5000/api/health
http://127.0.0.1:5000/api/health/db

## Notes on the schema

- `users` is prepared for authentication with `name`, `email`, `password_hash`, `role`, and `active`.
- `destinations` carries the frontend-facing fields such as `slug`, `city`, `state_region`, `country`, `category`, `tagline`, `best_time_to_visit`, `budget_info`, `rating`, `image_url`, and coordinates.
- `saved_places` is designed to support destinations now and can later extend to hotels and restaurants without a redesign.
- JWT tokens are stored locally in the frontend as `tourisense-token`, and the active user is stored as `tourisense-user`.
```
