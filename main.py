from nicegui import ui

from database import init_db
from ui.alert_history import build_alert_history_page

# Datenbank initialisieren (erstellt Tabellen beim ersten Start)
init_db()

# Alert-History-Seite aufbauen (neues Dark-Theme-Layout)
build_alert_history_page()

# NiceGUI starten
ui.run(title="WeatherGuard", port=8080, reload=False, dark=True)
