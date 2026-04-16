import requests
from datetime import datetime

from config import SRF_CONSUMER_KEY, SRF_CONSUMER_SECRET, SRF_TOKEN_URL, SRF_BASE_URL


class WeatherClient:
    """Client für die SRF Weather API V2."""

    def __init__(self):
        self._token: str | None = None
        self._token_expires: datetime | None = None

    def _authenticate(self):
        """Holt einen OAuth2 Bearer Token."""
        response = requests.post(
            SRF_TOKEN_URL,
            auth=(SRF_CONSUMER_KEY, SRF_CONSUMER_SECRET),
        )
        response.raise_for_status()
        data = response.json()
        self._token = data["access_token"]
        expires_in = int(data.get("expires_in", 3600))
        self._token_expires = datetime.now().timestamp() + expires_in

    def _get_headers(self) -> dict:
        if self._token is None or datetime.now().timestamp() >= self._token_expires:
            self._authenticate()
        return {"Authorization": f"Bearer {self._token}"}

    def get_geolocation_id(self, latitude: float, longitude: float) -> str:
        """Findet die Geolocation-ID für Koordinaten."""
        response = requests.get(
            f"{SRF_BASE_URL}/geolocations",
            headers=self._get_headers(),
            params={"latitude": latitude, "longitude": longitude},
        )
        response.raise_for_status()
        data = response.json()
        return data[0]["id"]

    def get_forecast(self, latitude: float, longitude: float) -> dict:
        """Holt die Wetterprognose für Koordinaten.

        Returns:
            Dict mit 'geolocation' und 'days' (je mit 'hours'-Liste).
            Stündliche Felder: TTT_C, FF_KMH, FX_KMH, RRR_MM, PROBPCP_PERCENT,
                              FRESHSNOW_CM, RELHUM_PERCENT, etc.
        """
        geolocation_id = self.get_geolocation_id(latitude, longitude)
        response = requests.get(
            f"{SRF_BASE_URL}/forecastpoint/{geolocation_id}",
            headers=self._get_headers(),
        )
        response.raise_for_status()
        return response.json()
