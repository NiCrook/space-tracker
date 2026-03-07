from dataclasses import dataclass
from pathlib import Path
import json


CONFIG_DIR = Path.home() / ".config" / "space-tracker"
CONFIG_FILE = CONFIG_DIR / "config.json"


@dataclass
class Location:
    latitude: float
    longitude: float
    elevation_km: float = 0.0

    @property
    def horizons_coord(self) -> str:
        """Format as Horizons SITE_COORD: 'lon,lat,elev_km' (East-positive)."""
        return f"{self.longitude},{self.latitude},{self.elevation_km}"


@dataclass
class Config:
    location: Location | None = None

    def save(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        data = {}
        if self.location:
            data["location"] = {
                "latitude": self.location.latitude,
                "longitude": self.location.longitude,
                "elevation_km": self.location.elevation_km,
            }
        CONFIG_FILE.write_text(json.dumps(data, indent=2))

    @classmethod
    def load(cls) -> "Config":
        if not CONFIG_FILE.exists():
            return cls()
        data = json.loads(CONFIG_FILE.read_text())
        location = None
        if "location" in data:
            loc = data["location"]
            location = Location(
                latitude=loc["latitude"],
                longitude=loc["longitude"],
                elevation_km=loc.get("elevation_km", 0.0),
            )
        return cls(location=location)
