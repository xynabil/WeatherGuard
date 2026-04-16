import os
from dotenv import load_dotenv

load_dotenv()

SRF_CONSUMER_KEY = os.getenv("SRF_CONSUMER_KEY")
SRF_CONSUMER_SECRET = os.getenv("SRF_CONSUMER_SECRET")
SRF_TOKEN_URL = "https://api.srgssr.ch/oauth/v1/accesstoken?grant_type=client_credentials"
SRF_BASE_URL = "https://api.srgssr.ch/srf-meteo/v2"

DATABASE_URL = "sqlite:///weather_guard.db"
