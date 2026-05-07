"""Package entrypoint.

Run with:
    python -m weather_guard
or simply:
    python __main__.py
"""

from application import WeatherGuardApplication

if __name__ == "__main__":
    WeatherGuardApplication().run()
