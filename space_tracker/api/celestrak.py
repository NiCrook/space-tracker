from dataclasses import dataclass
from enum import Enum
from time import monotonic

import httpx

CELESTRAK_GP_URL = "https://celestrak.org/NORAD/elements/gp.php"

SATELLITE_GROUPS = ["stations", "visual"]


class SatelliteStatus(Enum):
    VISIBLE = "Visible"
    ABOVE_HORIZON = "Above horizon"
    BELOW_HORIZON = "Below horizon"


@dataclass
class SatelliteInfo:
    """Computed satellite position and visibility from observer's location."""

    name: str
    norad_id: int
    altitude_deg: float | None
    azimuth_deg: float | None
    distance_km: float | None
    orbital_height_km: float | None
    status: SatelliteStatus
    next_pass_utc: str | None


# Module-level TTL cache
_cache: dict[str, tuple[float, list[dict]]] = {}
_CACHE_TTL = 7200  # 2 hours — CelesTrak minimum


async def fetch_satellite_group(
    client: httpx.AsyncClient,
    group: str,
) -> list[dict]:
    """Fetch a satellite group from CelesTrak GP API with TTL cache."""
    now = monotonic()
    if group in _cache:
        ts, cached = _cache[group]
        if now - ts < _CACHE_TTL:
            return cached

    params = {"GROUP": group, "FORMAT": "JSON"}
    response = await client.get(CELESTRAK_GP_URL, params=params)
    response.raise_for_status()
    data = response.json()

    _cache[group] = (now, data)
    return data


def _deduplicate(records: list[dict]) -> list[dict]:
    """Deduplicate OMM records by NORAD catalog ID, keeping first occurrence."""
    seen: set[int] = set()
    unique: list[dict] = []
    for rec in records:
        norad_id = rec.get("NORAD_CAT_ID", 0)
        if norad_id not in seen:
            seen.add(norad_id)
            unique.append(rec)
    return unique


async def fetch_all_satellites(
    client: httpx.AsyncClient,
    groups: list[str] | None = None,
) -> list[dict]:
    """Fetch and merge multiple satellite groups, deduplicated by NORAD ID."""
    if groups is None:
        groups = SATELLITE_GROUPS

    all_records: list[dict] = []
    for group in groups:
        raw = await fetch_satellite_group(client, group)
        all_records.extend(raw)

    return _deduplicate(all_records)


def compute_satellite_positions(
    omm_dicts: list[dict],
    latitude: float,
    longitude: float,
    elevation_km: float,
) -> list[SatelliteInfo]:
    """Compute current position, visibility, and next pass for each satellite."""
    from skyfield.api import EarthSatellite, load as sf_load, wgs84

    from space_tracker.api.events import _get_skyfield_loader

    loader = _get_skyfield_loader()
    eph = loader("de421.bsp")
    ts = sf_load.timescale()
    t = ts.now()

    observer = wgs84.latlon(latitude, longitude, elevation_m=elevation_km * 1000)

    # Sun altitude determines if observer is in twilight (satellite visibility)
    earth = eph["earth"]
    sun = eph["sun"]
    sun_alt_deg = (
        (earth + observer).at(t).observe(sun).apparent().altaz()[0].degrees
    )
    observer_in_twilight = -18.0 <= sun_alt_deg <= -6.0

    # Time window for next-pass computation (24 hours)
    t1 = ts.tt_jd(t.tt + 1.0)

    results: list[SatelliteInfo] = []
    for omm in omm_dicts:
        try:
            sat = EarthSatellite.from_omm(ts, omm)

            # Observer-relative position
            topo = (sat - observer).at(t)
            alt, az, dist = topo.altaz()
            alt_deg = alt.degrees
            az_deg = az.degrees
            dist_km = dist.km

            # Orbital height above Earth
            geocentric = sat.at(t)
            orbital_height_km = wgs84.height_of(geocentric).km

            # Visibility
            sunlit = bool(geocentric.is_sunlit(eph))
            above = alt_deg >= 0
            if above and sunlit and observer_in_twilight:
                status = SatelliteStatus.VISIBLE
            elif above:
                status = SatelliteStatus.ABOVE_HORIZON
            else:
                status = SatelliteStatus.BELOW_HORIZON

            # Next pass (rise event)
            next_pass: str | None = None
            t_events, events = sat.find_events(
                observer, t, t1, altitude_degrees=10.0
            )
            for t_ev, ev in zip(t_events, events):
                if ev == 0:  # rise
                    dt = t_ev.utc_datetime()
                    next_pass = dt.strftime("%H:%M:%S UTC")
                    break

            results.append(
                SatelliteInfo(
                    name=omm.get("OBJECT_NAME", "Unknown"),
                    norad_id=int(omm.get("NORAD_CAT_ID", 0)),
                    altitude_deg=alt_deg,
                    azimuth_deg=az_deg,
                    distance_km=dist_km,
                    orbital_height_km=orbital_height_km,
                    status=status,
                    next_pass_utc=next_pass,
                )
            )
        except Exception:
            continue

    return results
