import os
from dataclasses import dataclass
from time import monotonic

import httpx

DONKI_BASE_URL = "https://api.nasa.gov/DONKI"


def _api_key() -> str:
    return os.environ.get("NASA_API_KEY", "DEMO_KEY")


@dataclass
class SolarFlare:
    flr_id: str
    begin_time: str
    peak_time: str | None
    end_time: str | None
    class_type: str
    source_location: str | None
    active_region_num: int | None


@dataclass
class GeomagneticStorm:
    gst_id: str
    start_time: str
    kp_index_max: float


@dataclass
class CoronalMassEjection:
    activity_id: str
    start_time: str
    source_location: str | None
    active_region_num: int | None
    speed: float | None
    half_angle: float | None
    cme_type: str | None


def parse_solar_flares(data: list[dict]) -> list[SolarFlare]:
    results = []
    for item in data:
        begin = item.get("beginTime") or item.get("begineTime") or ""
        results.append(SolarFlare(
            flr_id=item["flrID"],
            begin_time=begin,
            peak_time=item.get("peakTime"),
            end_time=item.get("endTime"),
            class_type=item.get("classType", ""),
            source_location=item.get("sourceLocation"),
            active_region_num=item.get("activeRegionNum"),
        ))
    return results


def parse_geomagnetic_storms(data: list[dict]) -> list[GeomagneticStorm]:
    results = []
    for item in data:
        kp_list = item.get("allKpIndex") or []
        if kp_list:
            kp_max = max(entry.get("kpIndex", 0) for entry in kp_list)
        else:
            kp_max = 0.0
        results.append(GeomagneticStorm(
            gst_id=item["gstID"],
            start_time=item.get("startTime", ""),
            kp_index_max=float(kp_max),
        ))
    return results


def parse_cmes(data: list[dict]) -> list[CoronalMassEjection]:
    results = []
    for item in data:
        analyses = item.get("cmeAnalyses") or []
        speed = None
        half_angle = None
        cme_type = None

        if analyses:
            best = None
            for a in analyses:
                if a.get("isMostAccurate"):
                    best = a
                    break
            if best is None:
                best = analyses[-1]
            speed = best.get("speed")
            half_angle = best.get("halfAngle")
            cme_type = best.get("type")

        results.append(CoronalMassEjection(
            activity_id=item["activityID"],
            start_time=item.get("startTime", ""),
            source_location=item.get("sourceLocation"),
            active_region_num=item.get("activeRegionNum"),
            speed=float(speed) if speed is not None else None,
            half_angle=float(half_angle) if half_angle is not None else None,
            cme_type=cme_type,
        ))
    return results


# Module-level TTL cache
_cache: dict[str, tuple[float, list]] = {}
_CACHE_TTL = 900  # 15 minutes


async def _fetch_donki(
    client: httpx.AsyncClient,
    endpoint: str,
    start_date: str,
    end_date: str,
) -> list[dict]:
    cache_key = f"{endpoint}|{start_date}|{end_date}"
    now = monotonic()

    if cache_key in _cache:
        ts, cached = _cache[cache_key]
        if now - ts < _CACHE_TTL:
            return cached

    params = {
        "startDate": start_date,
        "endDate": end_date,
        "api_key": _api_key(),
    }
    response = await client.get(f"{DONKI_BASE_URL}/{endpoint}", params=params)
    response.raise_for_status()

    # DONKI may return empty string instead of []
    text = response.text.strip()
    if not text:
        data = []
    else:
        data = response.json()

    _cache[cache_key] = (now, data)
    return data


async def fetch_solar_flares(
    client: httpx.AsyncClient, start_date: str, end_date: str
) -> list[SolarFlare]:
    data = await _fetch_donki(client, "FLR", start_date, end_date)
    return parse_solar_flares(data)


async def fetch_geomagnetic_storms(
    client: httpx.AsyncClient, start_date: str, end_date: str
) -> list[GeomagneticStorm]:
    data = await _fetch_donki(client, "GST", start_date, end_date)
    return parse_geomagnetic_storms(data)


async def fetch_cmes(
    client: httpx.AsyncClient, start_date: str, end_date: str
) -> list[CoronalMassEjection]:
    data = await _fetch_donki(client, "CME", start_date, end_date)
    return parse_cmes(data)
