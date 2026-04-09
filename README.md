# WeatherGuard

Weather monitoring dashboard for construction sites and outdoor events. Automatically alerts when wind, frost, or rain exceed defined thresholds.

Built with Python, NiceGUI, SQLite (via SQLModel), and the SRF Meteo API v2.

---

## User Stories

| # | As a... | I want to... | So that... |
|---|---|---|---|
| 1 | site manager | add a construction site or event with a location | I can monitor it individually |
| 2 | site manager | set custom thresholds (max wind speed, min temperature) per site | alerts match my specific safety requirements |
| 3 | site manager | see current weather for all my sites on one dashboard | I get a quick overview without checking each one manually |
| 4 | site manager | receive a warning when wind exceeds my threshold | I can stop crane operations in time |
| 5 | site manager | receive a frost alert when temperatures drop near 0°C | I can protect fresh concrete or reschedule outdoor work |
| 6 | site manager | receive a rain alert during heavy precipitation | I can protect materials or postpone the event |
| 7 | site manager | see a history of past alerts per site | I can document incidents and review patterns |

---

## Data Types, Inputs & Expected Outputs

### Site (input)

| Field | Type | Example |
|---|---|---|
| `name` | `str` | `"Baustelle Olten Zentrum"` |
| `location` | `str` | `"Olten"` |
| `latitude` | `float` | `47.3523` |
| `longitude` | `float` | `7.9043` |
| `site_type` | `str` | `"baustelle"` or `"event"` |
| `max_wind_speed` | `float` | `40.0` (km/h) |
| `min_temperature` | `float` | `2.0` (°C) |
| `is_active` | `bool` | `True` |

### CurrentWeather (from SRF Meteo API)

| Field | Type | Example |
|---|---|---|
| `temperature` | `float` | `3.5` (°C) |
| `wind_speed` | `float` | `67.0` (km/h) |
| `precipitation` | `float` | `12.3` (mm) |
| `weather_description` | `str` | `"34"` (SRF symbol code) |
| `location` | `str` | `"Olten"` |

### Alert (output)

| Field | Type | Example |
|---|---|---|
| `site_id` | `int` | `1` |
| `alert_type` | `str` | `"wind"`, `"frost"`, `"rain"` |
| `message` | `str` | `"Wind 67 km/h – limit 40 km/h"` |
| `severity` | `str` | `"warning"` or `"danger"` |
| `triggered_at` | `datetime` | `2026-04-09 14:32:00` |
| `is_read` | `bool` | `False` |

---

## Class Diagram

```
┌─────────────────────────────────────┐
│               Site                  │
├─────────────────────────────────────┤
│ + id: int                           │
│ + name: str                         │
│ + location: str                     │
│ + latitude: float                   │
│ + longitude: float                  │
│ + site_type: str                    │
│ + max_wind_speed: float             │
│ + min_temperature: float            │
│ + is_active: bool                   │
└──────────────────┬──────────────────┘
                   │ 1 triggers 0..*
                   ▼
┌─────────────────────────────────────┐
│               Alert                 │
├─────────────────────────────────────┤
│ + id: int                           │
│ + site_id: int (FK)                 │
│ + alert_type: str                   │
│ + message: str                      │
│ + severity: str                     │
│ + triggered_at: datetime            │
│ + is_read: bool                     │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│          SRFWeatherService          │
├─────────────────────────────────────┤
│ - _client_id: str                   │
│ - _client_secret: str               │
│ - _token: str | None                │
├─────────────────────────────────────┤
│ + get_current_weather(lat, lon,     │
│     location) → CurrentWeather      │
│ - _fetch_token() → str              │
│ - _get_headers() → dict             │
│ - _parse_response(data, location)   │
│     → CurrentWeather                │
└──────────────────┬──────────────────┘
                   │ returns
                   ▼
┌─────────────────────────────────────┐
│          CurrentWeather             │
├─────────────────────────────────────┤
│ + temperature: float                │
│ + wind_speed: float                 │
│ + precipitation: float              │
│ + weather_description: str          │
│ + location: str                     │
│ + fetched_at: datetime              │
├─────────────────────────────────────┤
│ + __str__() → str                   │
│ + __repr__() → str                  │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│           AlertService              │
├─────────────────────────────────────┤
│ - _weather_service: SRFWeatherSvc   │
├─────────────────────────────────────┤
│ + check_site(site)                  │
│     → tuple[list[Alert],            │
│             CurrentWeather]         │
│ + check_all_sites_and_save()        │
│     → list[Alert]                   │
└─────────────────────────────────────┘
```

---

## Project Structure

```
weather_guard/
├── main.py
├── config.py               # API credentials – not in repo
├── models/
│   ├── site.py
│   └── alert.py
├── services/
│   ├── weather_service.py
│   └── alert_service.py
├── database/
│   └── db.py
├── ui/
│   ├── dashboard.py
│   └── site_form.py
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
```

```bash
python main.py
# Open http://localhost:8080
```

API keys: [developer.srgssr.ch](https://developer.srgssr.ch) → SRF-MeteoProductFreemium

> `config.py` and `*.db` are in `.gitignore` and will not be pushed to the repository.
