import math
from dataclasses import dataclass
from time import monotonic

import httpx

CAD_API_URL = "https://ssd-api.jpl.nasa.gov/cad.api"

AU_PER_LD = 0.00257


@dataclass
class CloseApproach:
    designation: str
    fullname: str
    close_approach_date: str
    distance_au: float
    distance_ld: float
    v_rel: float
    h_mag: float | None
    diameter_min_m: float | None
    diameter_max_m: float | None


def estimate_diameter(h_mag: float | None) -> tuple[float, float] | None:
    """Convert absolute magnitude H to estimated diameter range (min_m, max_m).

    Uses albedo range 0.25 (bright, smaller) to 0.05 (dark, larger).
    Formula: D_km = 1329 / sqrt(albedo) * 10^(-H/5)
    """
    if h_mag is None:
        return None
    factor = 10 ** (-h_mag / 5)
    d_km_min = 1329 / math.sqrt(0.25) * factor  # high albedo = smaller
    d_km_max = 1329 / math.sqrt(0.05) * factor  # low albedo = larger
    return (d_km_min * 1000, d_km_max * 1000)


def parse_close_approaches(data: dict) -> list[CloseApproach]:
    """Parse CAD API JSON response into CloseApproach objects."""
    if data.get("data") is None:
        return []

    fields = [f.lower() for f in data["fields"]]
    rows = data["data"]

    def idx(name: str) -> int:
        return fields.index(name)

    has_fullname = "fullname" in fields

    results = []
    for row in rows:
        des = row[idx("des")]
        fullname = row[idx("fullname")].strip() if has_fullname and row[idx("fullname")] else des
        cd = row[idx("cd")]
        dist_au = float(row[idx("dist")])
        dist_ld = dist_au / AU_PER_LD
        v_rel = float(row[idx("v_rel")])

        h_str = row[idx("h")]
        h_mag = float(h_str) if h_str is not None else None

        diameters = estimate_diameter(h_mag)
        diameter_min_m = diameters[0] if diameters else None
        diameter_max_m = diameters[1] if diameters else None

        results.append(CloseApproach(
            designation=des,
            fullname=fullname,
            close_approach_date=cd,
            distance_au=dist_au,
            distance_ld=dist_ld,
            v_rel=v_rel,
            h_mag=h_mag,
            diameter_min_m=diameter_min_m,
            diameter_max_m=diameter_max_m,
        ))

    return results


# Module-level TTL cache
_cache: dict[str, tuple[float, list[CloseApproach]]] = {}
_CACHE_TTL = 900  # 15 minutes


async def fetch_close_approaches(
    client: httpx.AsyncClient,
    date_min: str | None = None,
    date_max: str | None = None,
    dist_max: str = "0.05",
) -> list[CloseApproach]:
    """Fetch close approach data from JPL CAD API with TTL cache."""
    cache_key = f"{date_min}|{date_max}|{dist_max}"
    now = monotonic()

    if cache_key in _cache:
        ts, cached = _cache[cache_key]
        if now - ts < _CACHE_TTL:
            return cached

    params: dict[str, str] = {"dist-max": dist_max, "fullname": "true"}
    if date_min:
        params["date-min"] = date_min
    if date_max:
        params["date-max"] = date_max

    response = await client.get(CAD_API_URL, params=params)
    response.raise_for_status()

    results = parse_close_approaches(response.json())
    _cache[cache_key] = (now, results)
    return results
