import logging

import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

logger = logging.getLogger(__name__)


def coords_to_address(lat: float, lon: float) -> str:
    """
    Reverse geocode latitude and longitude to a short English address using Nominatim.
    """
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "format": "jsonv2",
            "lat": lat,
            "lon": lon,
            "zoom": 18,
            "addressdetails": 1,
            "accept-language": "en"  # Force English
        }
        headers = {"User-Agent": "PiFrame/1.0"}
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()

        # Use structured address for shorter display
        address = data.get("address", {})
        short_address = ", ".join(
            filter(None, [address.get("road"), address.get("city") or address.get("town") or address.get("village"), address.get("country")])
        )
        return short_address or data.get("display_name", "")

    except Exception as e:
        logger.error(f"Reverse geocoding failed: {e}")
        return ""