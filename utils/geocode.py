# utils/geocode.py

import requests

def get_city_from_coordinates(lat: float, lon: float) -> str:
    try:
        response = requests.get(
            f"https://nominatim.openstreetmap.org/reverse",
            params={"lat": lat, "lon": lon, "format": "json"},
            headers={"User-Agent": "yandex-bot"}
        )
        data = response.json()
        city = (
            data.get("address", {}).get("city") or
            data.get("address", {}).get("town") or
            data.get("address", {}).get("village") or
            "город не определён"
        )
        return city
    except Exception:
        return "город не определён"
