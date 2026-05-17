import pytest
from sqlmodel import Session, SQLModel

from data_access.db import Database
from domain.models import User, Location, WeatherThreshold


# Erstellt eine leere In-Memory-Datenbank für jeden Test neu
@pytest.fixture(scope="function")
def database():
    db = Database("sqlite:///:memory:")
    SQLModel.metadata.create_all(db.engine)
    yield db
    SQLModel.metadata.drop_all(db.engine)  # nach dem Test wieder löschen


# Öffnet eine Datenbank-Session für direkten Zugriff in Tests
@pytest.fixture(scope="function")
def db(database):
    with Session(database.engine) as session:
        yield session


# Füllt die Datenbank mit einem Testuser, einem Standort und einem Grenzwert
@pytest.fixture
def seeded_db(db):
    user = User(username="testuser", password="secret", company="Test AG")
    db.add(user)
    db.commit()
    db.refresh(user)

    loc = Location(
        user_id=user.id, name="Baustelle Zürich",
        latitude=47.38, longitude=8.54,
        branch="Bau", company="Test AG",
    )
    threshold = WeatherThreshold(
        parameter="TTT_C", operator="<", value=5.0,  # Alarm wenn Temperatur unter 5°C
        label="Frost", severity="critical",
    )
    loc.thresholds.append(threshold)
    db.add(loc)
    db.commit()
    db.refresh(loc)

    return db


# Fertiger Frost-Grenzwert für Unit-Tests (wiederverwendbar)
@pytest.fixture
def sample_threshold():
    return WeatherThreshold(
        parameter="TTT_C", operator="<", value=5.0,
        label="Frost", severity="critical",
    )
