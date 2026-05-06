# WeatherGuard

A B2B planning tool for companies in weather-dependent industries — construction, event logistics, and delivery services. Firms register their sites and get automatic alerts when critical weather conditions are forecast at their locations.

Built with Python, NiceGUI, SQLite (via SQLModel ORM), the Open-Meteo weather API, and the Leaflet.js map library.

---

## The Problem

Outdoor teams — crane operators, concrete crews, event builders — lose time and money when weather hits unexpectedly. WeatherGuard monitors forecasts against company-defined thresholds and alerts before conditions become critical, enabling active risk management instead of reactive damage control.

---

## User Stories

| # | As a... | I want to... | So that... |
|---|---|---|---|
| 1 | operations manager | register company locations and construction sites | I can monitor all of them in one place |
| 2 | operations manager | define custom weather thresholds per location (e.g. frost < 2°C, wind > 40 km/h) | alerts match the specific requirements of each job |
| 3 | operations manager | see a live dashboard with all locations and their current risk status | I get an immediate overview without checking each site manually |
| 4 | field team lead | receive a wind alert before crane or tent operations | I can halt or reschedule in time |
| 5 | field team lead | receive a frost alert before concrete is poured | I can protect the pour or adjust the schedule |
| 6 | field team lead | receive a rain alert during heavy precipitation | I can protect materials or postpone outdoor work |
| 7 | operations manager | review a history of past alerts per location | I can document incidents and improve future planning |
| 8 | operations manager | pick a location on an interactive map instead of entering coordinates manually | I can add sites faster and without errors |
| 9 | user | log in with my own account | my locations and alerts are separate from other companies |
| 10 | operations manager | see charts of alert frequency and type in the history view | I can spot patterns and identify high-risk periods |

---

## Class Diagram

![WeatherGuard Class Diagram](docs/class_diagram.png)

---

## Architecture

```
NiceGUI Frontend (Browser)
        │
        ├── Leaflet.js Map  →  user picks coordinates by clicking or searching
        │
        ▼
Login / Session (app.storage.user)
        │
        ▼
RiskAnalyzer (Business Logic)
   ├── WeatherClient  →  Open-Meteo API (free, no key required)
   └── DB Session     →  SQLite
        ├── User
        ├── Location
        ├── WeatherThreshold
        └── Alert
```

---

## APIs Used

| API | Purpose | Cost | Key required |
|-----|---------|------|--------------|
| [Open-Meteo](https://open-meteo.com) | 3-day hourly weather forecast (temperature, wind, gusts, rain, snow, humidity) | Free | No |
| [Nominatim / OpenStreetMap](https://nominatim.openstreetmap.org) | Geocoding — converts place names to coordinates | Free | No |
| [Leaflet.js](https://leafletjs.com) | Interactive map with clickable marker for location picking | Free | No |

---

## Project Structure

The structure mirrors the pizza reference project exactly.

```
WeatherGuard/
├── main.py                    # Entrypoint — python main.py
├── application.py             # WeatherGuardApplication (composition root)
├── data_access/
│   ├── db.py                  # Database class (engine, schema init, sessions)
│   ├── dao.py                 # UserDAO, LocationDAO, AlertDAO (CRUD)
│   └── seed.py                # WeatherSeeder (demo data on first run)
├── domain/
│   └── models.py              # All ORM models: User, Location, WeatherThreshold, Alert
├── services/
│   ├── weather_client.py      # Open-Meteo API → internal forecast format
│   └── risk_analyzer.py       # Threshold checks, deduplication, alert creation
├── ui/
│   ├── controllers.py         # AuthController, LocationController, AlertController, HistoryController
│   └── pages.py               # Pages class — registers all NiceGUI routes + UI code
├── weatherguard.db            # SQLite database (pre-seeded with demo data)
└── requirements.txt
```

---

## OOP Concepts Used

| Concept | Where |
|---------|-------|
| **Classes & Objects** | `User`, `Location`, `WeatherThreshold`, `Alert`, `WeatherClient`, `RiskAnalyzer` |
| **Encapsulation** | `threshold.is_exceeded(value)`, `user.check_password(pw)` hide internal logic |
| **Relationships / Associations** | `Location` has a list of `WeatherThreshold`, each `Alert` belongs to a `Location` |
| **Separation of concerns** | Models (data), Services (logic), UI (presentation) are in separate modules |
| **DRY principle** | `_sidebar()` helper called from every page in `pages.py` — defined once, reused everywhere |

---

## Setup

```bash
git clone https://github.com/YOUR-USERNAME/WeatherGuard.git
cd WeatherGuard
pip install -r requirements.txt
python main.py
# Open http://localhost:8080
```

The database (`weatherguard.db`) is included in the repo and already contains demo data — no setup needed.

---

## Demo Login

| Username | Password |
|----------|----------|
| `admin`  | `admin123` |

---

## Demo Data

The seeded database includes:

| Location | Type | Example Thresholds |
|----------|------|--------------------|
| Baustelle Zürich HB | Construction site | Wind > 50 km/h, Frost < 2°C |
| Open-Air Luzern | Event | Rain > 5 mm, Wind gusts > 60 km/h |
| Lieferroute Basel | Delivery | Snow > 2 cm, Ice risk < 1°C |

10 historical alerts are spread across the last 7 days so charts and history are visible immediately after cloning.
