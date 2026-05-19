"""Einstellungen der App.

Wir sammeln hier alle Einstellungen an einem Ort, damit man sie
nicht im Code suchen muss.
"""

# Wo wird die SQLite-Datenbank gespeichert?
DATABASE_URL = "sqlite:///weatherguard.db"

# Geheimschlüssel für die Browser-Session (NiceGUI storage)
STORAGE_SECRET = "weatherguard-secret"
