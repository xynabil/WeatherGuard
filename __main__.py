"""Alternativer Startpunkt.

Erlaubt den Aufruf:
    python -m WeatherGuard

Macht genau das Gleiche wie main.py.
"""

from application import WeatherGuardApplication


if __name__ == "__main__":
    app = WeatherGuardApplication()
    app.run()
