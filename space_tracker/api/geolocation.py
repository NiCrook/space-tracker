from dataclasses import dataclass

import httpx

from space_tracker.config import Location


@dataclass
class GeoResult:
    location: Location
    display_name: str


async def detect_location(client: httpx.AsyncClient) -> GeoResult | None:
    """Auto-detect user location via IP geolocation (ipinfo.io)."""
    try:
        response = await client.get("https://ipinfo.io/json", timeout=5.0)
        response.raise_for_status()
        data = response.json()
        lat_str, lon_str = data["loc"].split(",")
        location = Location(
            latitude=float(lat_str),
            longitude=float(lon_str),
        )
        city = data.get("city", "")
        region = data.get("region", "")
        parts = [p for p in (city, region) if p]
        display_name = ", ".join(parts) if parts else "Unknown"
        return GeoResult(location=location, display_name=display_name)
    except (httpx.HTTPError, KeyError, ValueError):
        return None
