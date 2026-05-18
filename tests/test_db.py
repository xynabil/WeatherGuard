from datetime import datetime

from sqlmodel import select

from domain.models import Location, Alert


def test_seeded_location_is_queryable(seeded_db):
    locations = seeded_db.exec(select(Location)).all()

    assert len(locations) == 1
    assert locations[0].name == "Baustelle Zürich"


def test_saving_alert_persists_in_db(db, seeded_db):
    loc = seeded_db.exec(select(Location)).first()

    alert = Alert(
        location_id=loc.id,
        threshold_label="Frost",
        severity="critical",
        parameter="TTT_C",
        actual_value=1.5,
        threshold_value=5.0,
        forecast_time=datetime(2026, 5, 17, 8, 0),
    )
    db.add(alert)
    db.commit()

    alerts = db.exec(select(Alert).where(Alert.location_id == loc.id)).all()

    assert len(alerts) == 1


def test_empty_db_returns_no_alerts(db):
    alerts = db.exec(select(Alert)).all()

    assert alerts == []
