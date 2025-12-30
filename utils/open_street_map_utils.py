import logging

import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

logger = logging.getLogger(__name__)


def coords_to_address(lat: float, lon: float) -> str:
    """
    Reverse geocode latitude and longitude to a street address using Nominatim.
    """
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "format": "jsonv2",
            "lat": lat,
            "lon": lon,
            "zoom": 18,
            "addressdetails": 1
        }
        headers = {"User-Agent": "PiFrame/1.0"}  # Nominatim requires a custom User-Agent
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data.get("display_name", "")
    except Exception as e:
        logger.error(f"Reverse geocoding failed: {e}")
        return ""
