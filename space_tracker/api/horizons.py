import httpx
from dataclasses import dataclass

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

    # RA is next 11 chars, Dec is next 12 chars (after date + whitespace)
    rest = line[18:].split()

    # RA: HH MM SS.ff (3 tokens)
    ra = f"{rest[0]} {rest[1]} {rest[2]}"
    # Dec: sDD MM SS.f (3 tokens)
    dec = f"{rest[3]} {rest[4]} {rest[5]}"

    def to_float(val: str) -> float | None:
        if val == "n.a.":
            return None
        try:
            return float(val)
        except ValueError:
            return None

    azimuth = to_float(rest[6])
    elevation = to_float(rest[7])
    magnitude = to_float(rest[8])
    surface_brightness = to_float(rest[9])
    delta_au = to_float(rest[10])
    delta_dot = to_float(rest[11])
    # Solar elongation is second to last, last token is /L or /T
    solar_elongation = to_float(rest[12])

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
