"""Controllers — Vermittler zwischen UI und Daten/Services.

Jeder Controller kapselt die Logik für einen Aufgabenbereich:
- AuthController:     Login, Registrierung, Passwort
- LocationController: Standorte verwalten
- AlertController:    Wetter-Analyse laufen lassen
- HistoryController:  Statistiken & Charts

Die Controller liegen bewusst ausserhalb von `ui/`, weil sie keine
NiceGUI-Komponenten kennen. Sie könnten genauso gut von einer
CLI oder einem REST-API-Layer aufgerufen werden.
"""

from controllers.auth_controller import AuthController
from controllers.location_controller import LocationController, BRANCH_PRESETS
from controllers.alert_controller import AlertController
from controllers.history_controller import (
    HistoryController,
    PARAM_TO_TYPE,
    TYPE_COLORS,
    DAY_NAMES,
)

__all__ = [
    "AuthController",
    "LocationController",
    "AlertController",
    "HistoryController",
    "BRANCH_PRESETS",
    "PARAM_TO_TYPE",
    "TYPE_COLORS",
    "DAY_NAMES",
]
