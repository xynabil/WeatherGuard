from sqlmodel import SQLModel, create_engine, Session

from config import DATABASE_URL


engine = create_engine(DATABASE_URL, echo=False)


def init_db():
    # Wichtig: Models importieren, damit SQLModel die Tabellen kennt
    from models.location import Location  # noqa: F401
    from models.threshold import WeatherThreshold  # noqa: F401
    from models.alert import Alert  # noqa: F401
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    return Session(engine)
