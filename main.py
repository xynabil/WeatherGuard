from nicegui import ui

from database import init_db
from ui.dashboard import build_dashboard

# Datenbank initialisieren (erstellt Tabellen beim ersten Start)
init_db()

# Dashboard aufbauen
build_dashboard()

# NiceGUI starten
ui.run(title="Weather Guard — B2B Logistics", port=8080, reload=False)
