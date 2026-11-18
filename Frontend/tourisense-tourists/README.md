# TouriSense — Tourist Frontend

A polished React frontend for the tourist side of **PSAIAC_267 Tourism Analytics & Destination Management**. It is deliberately isolated from backend business logic and can run as a presentation-ready demo today.

## Stack

React, Vite, React Router, Axios, Lucide React, Tailwind (available for future component styling), Leaflet / React Leaflet, and Recharts.

## Run locally

```bash
npm install
copy .env.example .env
npm run dev
```

Build for production with `npm run build`.

## Demo mode

Set `VITE_USE_MOCK_DATA=true`. Any valid email and password with 6+ characters signs in; the prefilled demo account is `demo@tourisense.in` / `Demo@123`.

Use `admin@gmail.com` with any password containing at least six characters to open the demo Admin Dashboard. Every other email signs in as a tourist in demo mode.

## Structure

```text
src/
  context/AuthContext.jsx      Authentication state
  data/mockData.js            All demonstration content
  services/                   API boundary for backend integration
  App.jsx                     Routes, reusable UI, and pages
  index.css                   Responsive product visual system
```

## Backend integration contract

The central Axios client reads `VITE_API_BASE_URL`; no component contains an API URL. Set `VITE_USE_MOCK_DATA=false` once APIs are ready.

Expected shapes:

- `POST /auth/login` → `{ token, user: { id, name, email } }`
- `POST /auth/register` → `{ token, user }`
- `GET /destinations`, `GET /destinations/:id` → destination entries with `id`, `name`, `location`, optional `image`, `rating`, `coordinates`
- `GET/POST /trips`, `GET/PUT/DELETE /trips/:id` → trip fields plus `days: [{ day, date, title, activities }]`
- `GET /hotels`, `GET /transport`, `GET /restaurants` → lists suitable for the corresponding services
- `GET/PATCH /users/me` → tourist profile

The planner should POST `{ destination, startDate, days, travelers, budget, interests, transportPreference, accommodationPreference }` to the backend itinerary-generation endpoint once its contract is available. The frontend is ready to render a variable number of returned itinerary days and allows reliable move-up/down editing without drag-and-drop.

## Backend teammate checklist

1. Add the API base URL to `.env` and disable mock mode.
2. Confirm endpoint paths / response fields, then update only files in `src/services/`.
3. Replace the temporary demo persistence in `AuthContext` and trip screens with service calls.
4. Return nullable optional fields safely; the UI already has graceful textual fallbacks.
5. Provide a public share ID for any shared trip—never expose database IDs in public links.
