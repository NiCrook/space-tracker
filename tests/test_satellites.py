from rich.text import Text

from space_tracker.api.celestrak import (
    SatelliteInfo,
    SatelliteStatus,
    _deduplicate,
)
from space_tracker.tabs.satellites import (
    format_satellite_row,
    format_satellite_row_styled,
    sort_satellites,
)


SAMPLE_CELESTRAK_JSON = [
    {
        "OBJECT_NAME": "ISS (ZARYA)",
        "OBJECT_ID": "1998-067A",
        "NORAD_CAT_ID": 25544,
        "EPOCH": "2026-03-13T10:00:00.000000",
        "MEAN_MOTION": 15.50103472,
        "ECCENTRICITY": 0.0007417,
        "INCLINATION": 51.6433,
        "RA_OF_ASC_NODE": 200.1234,
        "ARG_OF_PERICENTER": 130.5678,
        "MEAN_ANOMALY": 229.4321,
        "BSTAR": 0.00036139,
        "MEAN_MOTION_DOT": 0.00023456,
        "MEAN_MOTION_DDOT": 0,
        "REV_AT_EPOCH": 45000,
        "ELEMENT_SET_NO": 999,
        "EPHEMERIS_TYPE": 0,
        "CLASSIFICATION_TYPE": "U",
    },
    {
        "OBJECT_NAME": "HST",
        "OBJECT_ID": "1990-037B",
        "NORAD_CAT_ID": 20580,
        "EPOCH": "2026-03-13T08:00:00.000000",
        "MEAN_MOTION": 15.09,
        "ECCENTRICITY": 0.000285,
        "INCLINATION": 28.47,
        "RA_OF_ASC_NODE": 120.0,
        "ARG_OF_PERICENTER": 50.0,
        "MEAN_ANOMALY": 310.0,
        "BSTAR": 0.00005,
        "MEAN_MOTION_DOT": 0.00001,
        "MEAN_MOTION_DDOT": 0,
        "REV_AT_EPOCH": 30000,
        "ELEMENT_SET_NO": 999,
        "EPHEMERIS_TYPE": 0,
        "CLASSIFICATION_TYPE": "U",
    },
]


def _make_sat(
    name: str = "ISS (ZARYA)",
    norad_id: int = 25544,
    altitude_deg: float | None = 45.0,
    azimuth_deg: float | None = 220.0,
    distance_km: float | None = 800.0,
    orbital_height_km: float | None = 420.0,
    status: SatelliteStatus = SatelliteStatus.ABOVE_HORIZON,
    next_pass_utc: str | None = "12:30:00 UTC",
) -> SatelliteInfo:
    return SatelliteInfo(
        name=name,
        norad_id=norad_id,
        altitude_deg=altitude_deg,
        azimuth_deg=azimuth_deg,
        distance_km=distance_km,
        orbital_height_km=orbital_height_km,
        status=status,
        next_pass_utc=next_pass_utc,
    )


# --- Deduplication tests ---


def test_deduplicate_removes_duplicates():
    records = [
        {"NORAD_CAT_ID": 25544, "OBJECT_NAME": "ISS (first)"},
        {"NORAD_CAT_ID": 25544, "OBJECT_NAME": "ISS (second)"},
        {"NORAD_CAT_ID": 20580, "OBJECT_NAME": "HST"},
    ]
    result = _deduplicate(records)
    assert len(result) == 2
    assert result[0]["OBJECT_NAME"] == "ISS (first)"
    assert result[1]["OBJECT_NAME"] == "HST"


def test_deduplicate_all_unique():
    result = _deduplicate(SAMPLE_CELESTRAK_JSON)
    assert len(result) == 2


def test_deduplicate_empty():
    assert _deduplicate([]) == []


# --- Formatting tests ---


def test_format_satellite_row():
    sat = _make_sat()
    row = format_satellite_row(sat)
    assert row[0] == "ISS (ZARYA)"
    assert row[1] == "45.0"
    assert row[2] == "220.0"
    assert row[3] == "800"
    assert row[4] == "420"
    assert row[5] == "Above horizon"
    assert row[6] == "12:30:00 UTC"


def test_format_satellite_row_visible():
    sat = _make_sat(status=SatelliteStatus.VISIBLE)
    row = format_satellite_row(sat)
    assert row[5] == "Visible"


def test_format_satellite_row_below_horizon():
    sat = _make_sat(altitude_deg=-15.0, status=SatelliteStatus.BELOW_HORIZON)
    row = format_satellite_row(sat)
    assert row[1] == "-15.0"
    assert row[5] == "Below horizon"


def test_format_satellite_row_none_values():
    sat = _make_sat(
        altitude_deg=None,
        azimuth_deg=None,
        distance_km=None,
        orbital_height_km=None,
        next_pass_utc=None,
    )
    row = format_satellite_row(sat)
    assert row[1] == "---"
    assert row[2] == "---"
    assert row[3] == "---"
    assert row[4] == "---"
    assert row[6] == "---"


def test_format_satellite_row_styled_visible():
    sat = _make_sat(status=SatelliteStatus.VISIBLE)
    row = format_satellite_row_styled(sat)
    assert all(isinstance(cell, Text) for cell in row)
    assert all(cell.style == "bold green" for cell in row)


def test_format_satellite_row_styled_below_horizon():
    sat = _make_sat(status=SatelliteStatus.BELOW_HORIZON)
    row = format_satellite_row_styled(sat)
    assert all(isinstance(cell, Text) for cell in row)
    assert all(cell.style == "dim" for cell in row)


def test_format_satellite_row_styled_above_horizon():
    sat = _make_sat(status=SatelliteStatus.ABOVE_HORIZON)
    row = format_satellite_row_styled(sat)
    assert all(isinstance(cell, str) for cell in row)


# --- Sorting tests ---


def test_sort_satellites_by_status_then_altitude():
    sats = [
        _make_sat(name="Below", altitude_deg=-10.0, status=SatelliteStatus.BELOW_HORIZON),
        _make_sat(name="Above-low", altitude_deg=10.0, status=SatelliteStatus.ABOVE_HORIZON),
        _make_sat(name="Visible-high", altitude_deg=80.0, status=SatelliteStatus.VISIBLE),
        _make_sat(name="Visible-low", altitude_deg=30.0, status=SatelliteStatus.VISIBLE),
        _make_sat(name="Above-high", altitude_deg=60.0, status=SatelliteStatus.ABOVE_HORIZON),
    ]
    sorted_sats = sort_satellites(sats)
    names = [s.name for s in sorted_sats]
    assert names == [
        "Visible-high",
        "Visible-low",
        "Above-high",
        "Above-low",
        "Below",
    ]


def test_sort_satellites_empty():
    assert sort_satellites([]) == []
