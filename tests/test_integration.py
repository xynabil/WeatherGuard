from unittest.mock import MagicMock

from data_access.dao import LocationDAO, AlertDAO
from services.risk_analyzer import RiskAnalyzer
from ui.controllers import AlertController, HistoryController


# Hilfsfunktion: erstellt eine minimale Wetterprognose mit einer Temperatur
def make_forecast(temp):
    return {"days": [{"hours": [{"date_time": "2026-05-17T08:00:00", "TTT_C": temp}]}]}


# Test 10: Temperatur 1.5°C → Frost-Grenzwert überschritten → Alert wird gespeichert
def test_analysis_exceeded_threshold_creates_alert(database, seeded_db):
    # MagicMock ersetzt die echte Wetter-API mit simulierten Daten
    client = MagicMock()
    client.get_forecast.return_value = make_forecast(temp=1.5)  # 1.5°C < 5°C → Frost

    controller = AlertController(
        location_dao=LocationDAO(database.engine),
        alert_dao=AlertDAO(database.engine),
        weather_client=client,
    )
    locs = LocationDAO(database.engine).list_all()
    controller.run_analysis(locs[0].id)
    alerts = controller.list_alerts(user_id=locs[0].user_id)

    assert len(alerts) == 1
    assert alerts[0].severity == "critical"
    assert alerts[0].parameter == "TTT_C"


# Test 11: Temperatur 12°C → kein Grenzwert überschritten → keine Alerts
def test_analysis_no_threshold_exceeded_creates_no_alert(database, seeded_db):
    client = MagicMock()
    client.get_forecast.return_value = make_forecast(temp=12.0)  # 12°C > 5°C → kein Frost

    controller = AlertController(
        location_dao=LocationDAO(database.engine),
        alert_dao=AlertDAO(database.engine),
        weather_client=client,
    )
    locs = LocationDAO(database.engine).list_all()
    controller.run_analysis(locs[0].id)
    alerts = controller.list_alerts(user_id=locs[0].user_id)

    assert alerts == []


# Test 12: Nach Analyse mit einem Frost-Alert → KPIs prüfen
def test_history_kpis_after_analysis(database, seeded_db):
    client = MagicMock()
    client.get_forecast.return_value = make_forecast(temp=1.5)

    controller = AlertController(
        location_dao=LocationDAO(database.engine),
        alert_dao=AlertDAO(database.engine),
        weather_client=client,
    )
    locs = LocationDAO(database.engine).list_all()
    controller.run_analysis(locs[0].id)

    # KPIs aus der History auslesen und prüfen
    kpis = HistoryController(
        alert_dao=AlertDAO(database.engine),
    ).get_kpis(user_id=locs[0].user_id)

    assert kpis["total"]   == 1
    assert kpis["danger"]  == 1
    assert kpis["warning"] == 0
