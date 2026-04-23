# WeatherGuard

A B2B planning tool for companies in weather-dependent industries — construction, event logistics, and delivery services. Firms register their sites and get automatic alerts when critical weather conditions are forecast at their locations.

Built with Python, NiceGUI, SQLite (via SQLModel ORM), the SRF Meteo API v2 (SRG SSR Developer Portal), and the Leaflet.js map library.

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
NiceGUI Dashboard (Frontend)
        │
        ├── Leaflet.js Map  →  user picks coordinates by clicking
        │
        ▼
AuthService (Login / Session)
        │
        ▼
RiskAnalyzer (Business Logic)
   ├── SRFWeatherService  →  SRF Meteo API
   ├── AlertStatistics    →  aggregations for history charts
   └── DB Session         →  SQLite
        ├── User
        ├── Location
        ├── WeatherThreshold
        └── Alert
```

---

## Project Structure

```
weather_guard/
├── main.py
├── config.py                  # API credentials – not in repo
├── models/
│   ├── user.py
│   ├── location.py
│   ├── threshold.py
│   └── alert.py
├── services/
│   ├── weather_service.py     # SRF API + WeatherForecast
│   ├── risk_analyzer.py       # threshold checks, alert creation, deduplication
│   ├── alert_statistics.py    # aggregations for history charts
│   └── auth_service.py        # login, session, password hashing
├── database/
│   └── db.py
├── ui/
│   ├── dashboard.py
│   ├── history.py             # alert history view with charts
│   ├── location_form.py       # includes interactive map picker
│   └── login.py
└── requirements.txt
```

---

## Setup

```bash
git clone https://github.com/YOUR-USERNAME/weather-guard.git
cd weather-guard
pip install -r requirements.txt
```

Create `config.py`:
```python
SRF_CLIENT_ID = "your_client_id"
SRF_CLIENT_SECRET = "your_client_secret"
SECRET_KEY = "your_session_secret"
```

```bash
python main.py
# Open http://localhost:8080
```

API keys: [developer.srgssr.ch](https://developer.srgssr.ch) → SRF-MeteoProductFreemium

> `config.py` and `*.db` are in `.gitignore` and will not be committed to the repository.
