from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from config import DATABASE_URL


class Base(DeclarativeBase):
    pass


engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    from models.location import Location
    from models.threshold import WeatherThreshold
    from models.alert import Alert
    Base.metadata.create_all(bind=engine)


def get_session():
    return SessionLocal()
