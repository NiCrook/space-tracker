from datetime import datetime
from dataclasses import dataclass
from time import monotonic

import httpx

from space_tracker.config import Location


BASE_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"

PLANET_COMMANDS = {
    "Sun": "10",
    "Moon": "301",
    "Mercury": "199",
    "Venus": "299",
    "Mars": "499",
    "Jupiter": "599",
    "Saturn": "699",
    "Uranus": "799",
    "Neptune": "899",
}


@dataclass
class EphemerisRow:
    datetime: str
    ra: str
    dec: str
    azimuth: float | None
    elevation: float | None
    magnitude: float | None
    surface_brightness: float | None
    delta_au: float | None
    delta_dot: float | None
    solar_elongation: float | None


@dataclass
class RiseTransitSet:
    rise: str | None
    transit: str | None
    transit_elevation: float | None
    set_time: str | None


def _parse_datetime(dt_str: str) -> datetime:
    """Parse Horizons datetime string like '2026-Mar-07 00:00'."""
    return datetime.strptime(dt_str, "%Y-%b-%d %H:%M")


def _format_time(dt: datetime) -> str:
    """Format datetime as HH:MM UTC."""
    return dt.strftime("%H:%M UTC")


def compute_rise_transit_set(rows: list[EphemerisRow]) -> RiseTransitSet:
    """Compute rise/transit/set from a series of ephemeris rows."""
    if not rows:
        return RiseTransitSet(None, None, None, None)

    rise: str | None = None
    set_time: str | None = None
    transit: str | None = None
    transit_elevation: float | None = None
    max_elev = -999.0

    for i, row in enumerate(rows):
        elev = row.elevation
        if elev is None:
            continue

        # Track max elevation for transit
        if elev > 0 and elev > max_elev:
            max_elev = elev
            transit_elevation = elev
            transit = row.datetime

        # Check for sign changes with previous row
        if i > 0:
            prev_elev = rows[i - 1].elevation
            if prev_elev is None:
                continue

            if prev_elev <= 0 < elev and rise is None:
                # Negative→positive = rise, interpolate
                t1 = _parse_datetime(rows[i - 1].datetime)
                t2 = _parse_datetime(row.datetime)
                frac = abs(prev_elev) / (abs(prev_elev) + abs(elev))
                crossing = t1 + (t2 - t1) * frac
                rise = _format_time(crossing)

            if prev_elev >= 0 > elev and set_time is None:
                # Positive→negative = set, interpolate
                t1 = _parse_datetime(rows[i - 1].datetime)
                t2 = _parse_datetime(row.datetime)
                frac = abs(prev_elev) / (abs(prev_elev) + abs(elev))
                crossing = t1 + (t2 - t1) * frac
                set_time = _format_time(crossing)

    # Format transit time
    if transit is not None:
        transit = _format_time(_parse_datetime(transit))

    return RiseTransitSet(
        rise=rise,
        transit=transit,
        transit_elevation=transit_elevation,
        set_time=set_time,
    )


def parse_ephemeris(result_text: str) -> list[EphemerisRow]:
    """Parse the text blob between $$SOE and $$EOE markers."""
    lines = result_text.split("\n")
    in_data = False
    rows: list[EphemerisRow] = []

    for line in lines:
        stripped = line.strip()
        if stripped == "$$SOE":
            in_data = True
            continue
        if stripped == "$$EOE":
            break
        if not in_data or not stripped:
            continue

        rows.append(_parse_observer_row(stripped))

    return rows


def _parse_observer_row(line: str) -> EphemerisRow:
    """Parse a single OBSERVER ephemeris row.

    Expected QUANTITIES='1,4,9,20,23' producing columns:
      Date__(UT)__HR:MN  R.A._(ICRF)_DEC  Azi_(a-app)_Elev  APmag  S-brt  delta  deldot  S-O-T/r
    """
    # Date is first 18 chars: " 2026-Mar-07 00:00"
    datetime_str = line[:18].strip()

    rest = line[18:].split()

    # Skip leading solar-presence marker (* or similar non-numeric tokens)
    offset = 0
    while offset < len(rest) and not rest[offset][0].isdigit() and rest[offset][0] not in "-+":
        offset += 1

    # RA: HH MM SS.ff (3 tokens)
    ra = f"{rest[offset]} {rest[offset+1]} {rest[offset+2]}"
    # Dec: sDD MM SS.f (3 tokens)
    dec = f"{rest[offset+3]} {rest[offset+4]} {rest[offset+5]}"

    def to_float(val: str) -> float | None:
        if val == "n.a.":
            return None
        try:
            return float(val)
        except ValueError:
            return None

    azimuth = to_float(rest[offset+6])
    elevation = to_float(rest[offset+7])
    magnitude = to_float(rest[offset+8])
    surface_brightness = to_float(rest[offset+9])
    delta_au = to_float(rest[offset+10])
    delta_dot = to_float(rest[offset+11])
    # Solar elongation is second to last, last token is /L or /T
    solar_elongation = to_float(rest[offset+12])

    return EphemerisRow(
        datetime=datetime_str,
        ra=ra,
        dec=dec,
        azimuth=azimuth,
        elevation=elevation,
        magnitude=magnitude,
        surface_brightness=surface_brightness,
        delta_au=delta_au,
        delta_dot=delta_dot,
        solar_elongation=solar_elongation,
    )


async def fetch_ephemeris(
    client: httpx.AsyncClient,
    command: str,
    location: Location,
    start_time: str,
    stop_time: str,
    step_size: str = "60 min",
    quantities: str = "1,4,9,20,23",
) -> list[EphemerisRow]:
    """Fetch ephemeris data from JPL Horizons for an observer location."""
    params = {
        "format": "json",
        "COMMAND": f"'{command}'",
        "EPHEM_TYPE": "'OBSERVER'",
        "CENTER": "'coord@399'",
        "COORD_TYPE": "'GEODETIC'",
        "SITE_COORD": f"'{location.horizons_coord}'",
        "START_TIME": f"'{start_time}'",
        "STOP_TIME": f"'{stop_time}'",
        "STEP_SIZE": f"'{step_size}'",
        "QUANTITIES": f"'{quantities}'",
    }
    response = await client.get(BASE_URL, params=params)
    response.raise_for_status()

    data = response.json()
    return parse_ephemeris(data["result"])


@dataclass
class _CacheEntry:
    rows: list[EphemerisRow]
    timestamp: float


class EphemerisCache:
    """TTL cache for Horizons API responses, keyed by request parameters."""

    def __init__(self, default_ttl: float = 120.0) -> None:
        self._cache: dict[str, _CacheEntry] = {}
        self._default_ttl = default_ttl

    @staticmethod
    def _make_key(
        command: str,
        coord: str,
        start_time: str,
        stop_time: str,
        step_size: str,
        quantities: str,
    ) -> str:
        return f"{command}|{coord}|{start_time}|{stop_time}|{step_size}|{quantities}"

    def get(
        self,
        command: str,
        location: Location,
        start_time: str,
        stop_time: str,
        step_size: str = "60 min",
        quantities: str = "1,4,9,20,23",
        ttl: float | None = None,
    ) -> list[EphemerisRow] | None:
        key = self._make_key(
            command, location.horizons_coord, start_time, stop_time, step_size, quantities
        )
        entry = self._cache.get(key)
        if entry is None:
            return None
        age = monotonic() - entry.timestamp
        if age > (ttl if ttl is not None else self._default_ttl):
            del self._cache[key]
            return None
        return entry.rows

    def put(
        self,
        rows: list[EphemerisRow],
        command: str,
        location: Location,
        start_time: str,
        stop_time: str,
        step_size: str = "60 min",
        quantities: str = "1,4,9,20,23",
    ) -> None:
        key = self._make_key(
            command, location.horizons_coord, start_time, stop_time, step_size, quantities
        )
        self._cache[key] = _CacheEntry(rows=rows, timestamp=monotonic())

    async def fetch(
        self,
        client: httpx.AsyncClient,
        command: str,
        location: Location,
        start_time: str,
        stop_time: str,
        step_size: str = "60 min",
        quantities: str = "1,4,9,20,23",
        ttl: float | None = None,
    ) -> list[EphemerisRow]:
        """Fetch with cache — returns cached result if fresh, otherwise fetches and caches."""
        cached = self.get(
            command, location, start_time, stop_time, step_size, quantities, ttl=ttl
        )
        if cached is not None:
            return cached
        rows = await fetch_ephemeris(
            client, command, location, start_time, stop_time, step_size, quantities
        )
        self.put(rows, command, location, start_time, stop_time, step_size, quantities)
        return rows

    async def fetch_batch(
        self,
        client: httpx.AsyncClient,
        commands: dict[str, str],
        location: Location,
        start_time: str,
        stop_time: str,
        step_size: str = "60 min",
        quantities: str = "1,4,9,20,23",
        ttl: float | None = None,
    ) -> dict[str, list[EphemerisRow]]:
        """Fetch multiple objects serially, using cache for each."""
        results: dict[str, list[EphemerisRow]] = {}
        for name, command in commands.items():
            rows = await self.fetch(
                client, command, location, start_time, stop_time,
                step_size, quantities, ttl=ttl,
            )
            results[name] = rows
        return results
