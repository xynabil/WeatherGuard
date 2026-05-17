from datetime import datetime

from sqlmodel import select

from domain.models import User, Location, WeatherThreshold, Alert


# Test 7: Standort aus der Datenbank abfragen → wird korrekt gefunden
def test_seeded_location_is_queryable(seeded_db):
    locations = seeded_db.exec(select(Location)).all()

    assert len(locations) == 1
    assert locations[0].name == "Baustelle Zürich"


# Test 8: Alert manuell speichern → wird danach in der Datenbank gefunden
def test_saving_alert_persists_it(db, seeded_db):
    # Standort aus der Datenbank laden um die ID zu bekommen
    loc = seeded_db.exec(select(Location)).first()

    alert = Alert(
        location_id=loc.id,
        threshold_label="Frost",
        severity="critical",
        parameter="TTT_C",
        actual_value=1.5,       # gemessene Temperatur
        threshold_value=5.0,    # Grenzwert
        forecast_time=datetime(2026, 5, 17, 8, 0),
    )
    db.add(alert)
    db.commit()

    # Alert wieder aus der Datenbank lesen
    alerts = db.exec(select(Alert).where(Alert.location_id == loc.id)).all()

    assert len(alerts) == 1


# Test 9: Leere Datenbank → keine Alerts vorhanden
def test_empty_db_returns_no_alerts(db):
    alerts = db.exec(select(Alert)).all()

    assert alerts == []
