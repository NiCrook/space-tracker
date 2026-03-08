from dataclasses import dataclass
from datetime import date, datetime, timezone
from enum import Enum
from pathlib import Path
from typing import NamedTuple


class EventType(Enum):
    CONJUNCTION = "Conjunction"
    OPPOSITION = "Opposition"
    METEOR_SHOWER = "Meteor Shower"
    ECLIPSE = "Eclipse"


@dataclass
class CelestialEvent:
    event_type: EventType
    name: str
    date_peak: date
    date_end: date | None
    description: str


# --- Meteor Showers ---


class MeteorShowerInfo(NamedTuple):
    name: str
    peak_month: int
    peak_day: int
    end_month: int
    end_day: int
    zhr: int
    parent: str


METEOR_SHOWERS: list[MeteorShowerInfo] = [
    MeteorShowerInfo("Quadrantids", 1, 4, 1, 5, 110, "2003 EH1"),
    MeteorShowerInfo("Lyrids", 4, 22, 4, 23, 18, "C/1861 G1 Thatcher"),
    MeteorShowerInfo("Eta Aquariids", 5, 6, 5, 7, 50, "1P/Halley"),
    MeteorShowerInfo("Delta Aquariids", 7, 30, 7, 31, 25, "96P/Machholz"),
    MeteorShowerInfo("Perseids", 8, 12, 8, 13, 100, "109P/Swift-Tuttle"),
    MeteorShowerInfo("Draconids", 10, 8, 10, 9, 10, "21P/Giacobini-Zinner"),
    MeteorShowerInfo("Orionids", 10, 21, 10, 22, 20, "1P/Halley"),
    MeteorShowerInfo("Leonids", 11, 17, 11, 18, 15, "55P/Tempel-Tuttle"),
    MeteorShowerInfo("Geminids", 12, 14, 12, 15, 150, "3200 Phaethon"),
    MeteorShowerInfo("Ursids", 12, 22, 12, 23, 10, "8P/Tuttle"),
]


def get_meteor_showers(year: int) -> list[CelestialEvent]:
    events = []
    for s in METEOR_SHOWERS:
        events.append(CelestialEvent(
            event_type=EventType.METEOR_SHOWER,
            name=s.name,
            date_peak=date(year, s.peak_month, s.peak_day),
            date_end=date(year, s.end_month, s.end_day),
            description=f"ZHR ~{s.zhr}, parent: {s.parent}",
        ))
    return events


# --- Eclipses (2024-2030, from NASA published data) ---


class EclipseInfo(NamedTuple):
    name: str
    year: int
    month: int
    day: int
    description: str


ECLIPSES: list[EclipseInfo] = [
    # 2024
    EclipseInfo("Penumbral Lunar Eclipse", 2024, 3, 25, "Americas, Europe, Africa"),
    EclipseInfo("Total Solar Eclipse", 2024, 4, 8, "Mexico, US, Canada"),
    EclipseInfo("Partial Lunar Eclipse", 2024, 9, 18, "Americas, Europe, Africa"),
    EclipseInfo("Annular Solar Eclipse", 2024, 10, 2, "S. America"),
    # 2025
    EclipseInfo("Total Lunar Eclipse", 2025, 3, 14, "Americas, Europe, Africa"),
    EclipseInfo("Partial Solar Eclipse", 2025, 3, 29, "NW Africa, Europe, N. Russia"),
    EclipseInfo("Total Lunar Eclipse", 2025, 9, 7, "Europe, Africa, Asia, Australia"),
    EclipseInfo("Partial Solar Eclipse", 2025, 9, 21, "S. Pacific, NZ, Antarctica"),
    # 2026
    EclipseInfo("Annular Solar Eclipse", 2026, 2, 17, "S. America, Africa, Antarctica"),
    EclipseInfo("Total Lunar Eclipse", 2026, 3, 3, "E. Asia, Australia, Pacific, Americas"),
    EclipseInfo("Total Solar Eclipse", 2026, 8, 12, "Arctic, Greenland, Iceland, Spain"),
    EclipseInfo("Partial Lunar Eclipse", 2026, 8, 28, "E. Americas, Europe, Africa, Asia"),
    # 2027
    EclipseInfo("Penumbral Lunar Eclipse", 2027, 2, 20, "Americas, Europe, Africa"),
    EclipseInfo("Annular Solar Eclipse", 2027, 2, 6, "S. America, Africa, Antarctica"),
    EclipseInfo("Total Solar Eclipse", 2027, 8, 2, "Spain, N. Africa, Middle East"),
    EclipseInfo("Penumbral Lunar Eclipse", 2027, 8, 17, "Americas, Europe, Africa"),
    # 2028
    EclipseInfo("Partial Lunar Eclipse", 2028, 1, 12, "Americas, Europe, Africa"),
    EclipseInfo("Annular Solar Eclipse", 2028, 1, 26, "E. Pacific, S. America"),
    EclipseInfo("Total Lunar Eclipse", 2028, 7, 6, "Americas, Europe, Africa"),
    EclipseInfo("Total Solar Eclipse", 2028, 7, 22, "Australia, NZ"),
    EclipseInfo("Partial Lunar Eclipse", 2028, 12, 31, "Europe, Africa, Asia, Australia"),
    # 2029
    EclipseInfo("Partial Solar Eclipse", 2029, 1, 14, "N. America"),
    EclipseInfo("Total Lunar Eclipse", 2029, 6, 26, "Americas, Europe, Africa"),
    EclipseInfo("Partial Solar Eclipse", 2029, 7, 11, "S. tip of S. America"),
    EclipseInfo("Partial Lunar Eclipse", 2029, 12, 20, "Americas, Europe, Africa, Asia"),
    # 2030
    EclipseInfo("Annular Solar Eclipse", 2030, 6, 1, "N. Africa, Europe, N. Asia"),
    EclipseInfo("Partial Lunar Eclipse", 2030, 6, 15, "Americas, Europe, Africa"),
    EclipseInfo("Total Solar Eclipse", 2030, 11, 25, "S. Africa, S. Indian Ocean, Australia"),
    EclipseInfo("Penumbral Lunar Eclipse", 2030, 12, 9, "Americas, Europe, Africa, Asia"),
]


def get_eclipses(year: int) -> list[CelestialEvent]:
    return [
        CelestialEvent(
            event_type=EventType.ECLIPSE,
            name=e.name,
            date_peak=date(e.year, e.month, e.day),
            date_end=None,
            description=e.description,
        )
        for e in ECLIPSES
        if e.year == year
    ]


# --- Skyfield helpers ---

SKYFIELD_DIR = Path.home() / ".config" / "space-tracker" / "skyfield"

_PLANET_PAIRS = [
    ("Venus", "Jupiter barycenter"),
    ("Venus", "Mars barycenter"),
    ("Venus", "Saturn barycenter"),
    ("Venus", "Mercury"),
    ("Jupiter barycenter", "Saturn barycenter"),
    ("Jupiter barycenter", "Mars barycenter"),
    ("Mars barycenter", "Saturn barycenter"),
]

_OUTER_PLANETS = [
    "Mars barycenter",
    "Jupiter barycenter",
    "Saturn barycenter",
    "Uranus barycenter",
    "Neptune barycenter",
]


def _planet_display_name(skyfield_name: str) -> str:
    return skyfield_name.replace(" barycenter", "")


def _get_skyfield_loader():
    from skyfield.api import Loader
    SKYFIELD_DIR.mkdir(parents=True, exist_ok=True)
    return Loader(str(SKYFIELD_DIR))


def compute_conjunctions(year: int, threshold_deg: float = 5.0) -> list[CelestialEvent]:
    from skyfield.api import load as sf_load

    loader = _get_skyfield_loader()
    eph = loader('de421.bsp')
    ts = sf_load.timescale()

    earth = eph['earth']
    days_in_year = 366 if _is_leap_year(year) else 365
    t = ts.utc(year, 1, range(1, days_in_year + 1))

    events = []
    for name_a, name_b in _PLANET_PAIRS:
        body_a = eph[name_a]
        body_b = eph[name_b]

        astrometric_a = earth.at(t).observe(body_a).apparent()
        astrometric_b = earth.at(t).observe(body_b).apparent()

        ra_a, dec_a, _ = astrometric_a.radec()
        ra_b, dec_b, _ = astrometric_b.radec()

        sep = _angular_separation_deg(
            ra_a._degrees, dec_a.degrees,
            ra_b._degrees, dec_b.degrees,
        )

        for i in range(1, len(sep) - 1):
            if sep[i] < sep[i - 1] and sep[i] < sep[i + 1] and sep[i] < threshold_deg:
                dt = t[i].utc_datetime()
                disp_a = _planet_display_name(name_a)
                disp_b = _planet_display_name(name_b)
                events.append(CelestialEvent(
                    event_type=EventType.CONJUNCTION,
                    name=f"{disp_a}-{disp_b} Conjunction",
                    date_peak=dt.date(),
                    date_end=None,
                    description=f"{sep[i]:.1f}° separation",
                ))

    return events


def compute_oppositions(year: int) -> list[CelestialEvent]:
    from skyfield.api import load as sf_load

    loader = _get_skyfield_loader()
    eph = loader('de421.bsp')
    ts = sf_load.timescale()

    earth = eph['earth']
    sun = eph['sun']
    days_in_year = 366 if _is_leap_year(year) else 365
    t = ts.utc(year, 1, range(1, days_in_year + 1))

    astrometric_sun = earth.at(t).observe(sun).apparent()
    ra_sun, dec_sun, _ = astrometric_sun.radec()

    events = []
    for planet_name in _OUTER_PLANETS:
        body = eph[planet_name]
        astrometric = earth.at(t).observe(body).apparent()
        ra_planet, dec_planet, _ = astrometric.radec()

        elongation = _angular_separation_deg(
            ra_sun._degrees, dec_sun.degrees,
            ra_planet._degrees, dec_planet.degrees,
        )

        for i in range(1, len(elongation) - 1):
            if (elongation[i] > elongation[i - 1]
                    and elongation[i] > elongation[i + 1]
                    and elongation[i] > 150.0):
                dt = t[i].utc_datetime()
                disp = _planet_display_name(planet_name)
                events.append(CelestialEvent(
                    event_type=EventType.OPPOSITION,
                    name=f"{disp} Opposition",
                    date_peak=dt.date(),
                    date_end=None,
                    description=f"Elongation {elongation[i]:.1f}°",
                ))

    return events


def _angular_separation_deg(ra1_deg, dec1_deg, ra2_deg, dec2_deg):
    import numpy as np

    ra1 = np.radians(ra1_deg)
    dec1 = np.radians(dec1_deg)
    ra2 = np.radians(ra2_deg)
    dec2 = np.radians(dec2_deg)

    cos_sep = (np.sin(dec1) * np.sin(dec2)
               + np.cos(dec1) * np.cos(dec2) * np.cos(ra1 - ra2))
    cos_sep = np.clip(cos_sep, -1.0, 1.0)
    return np.degrees(np.arccos(cos_sep))


def _is_leap_year(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


# --- Combined ---

_cache: dict[int, tuple[float, list[CelestialEvent]]] = {}
_CACHE_TTL = 3600.0


def get_all_events(year: int) -> list[CelestialEvent]:
    now = datetime.now(timezone.utc).timestamp()
    if year in _cache:
        cached_time, cached_events = _cache[year]
        if now - cached_time < _CACHE_TTL:
            return cached_events

    events: list[CelestialEvent] = []
    events.extend(get_meteor_showers(year))
    events.extend(get_eclipses(year))
    events.extend(compute_conjunctions(year))
    events.extend(compute_oppositions(year))
    events.sort(key=lambda e: e.date_peak)

    _cache[year] = (now, events)
    return events
