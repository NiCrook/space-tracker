from rich.text import Text

from space_tracker.api.horizons import EphemerisRow
from space_tracker.tabs.sky_now import format_row, format_row_styled, sort_rows


def _make_row(
    elevation: float | None = 45.0,
    azimuth: float | None = 220.0,
    magnitude: float | None = -2.1,
    ra: str = "05 32 12.3",
    dec: str = "+22 05 30.1",
    delta_au: float | None = 4.5678,
    solar_elongation: float | None = 120.3,
) -> EphemerisRow:
    return EphemerisRow(
        datetime="2026-Mar-07 00:00",
        ra=ra,
        dec=dec,
        azimuth=azimuth,
        elevation=elevation,
        magnitude=magnitude,
        surface_brightness=3.5,
        delta_au=delta_au,
        delta_dot=-1.0,
        solar_elongation=solar_elongation,
    )


def test_format_row_values():
    row = _make_row()
    result = format_row("Jupiter", row)
    assert result == (
        "Jupiter",
        "45.0",
        "220.0",
        "-2.1",
        "05 32 12.3",
        "+22 05 30.1",
        "4.5678",
        "120.3",
    )


def test_format_row_none_values():
    row = _make_row(elevation=None, azimuth=None, magnitude=None, delta_au=None, solar_elongation=None)
    result = format_row("Sun", row)
    assert result[1] == "---"  # Alt
    assert result[2] == "---"  # Az
    assert result[3] == "---"  # Mag
    assert result[6] == "---"  # Distance
    assert result[7] == "---"  # Elongation


def test_sort_rows_by_altitude_descending():
    rows = [
        ("Mars", _make_row(elevation=10.0)),
        ("Jupiter", _make_row(elevation=60.0)),
        ("Venus", _make_row(elevation=35.0)),
        ("Saturn", _make_row(elevation=-5.0)),
    ]
    sorted_result = sort_rows(rows)
    names = [name for name, _ in sorted_result]
    assert names == ["Jupiter", "Venus", "Mars", "Saturn"]


def test_sort_rows_none_elevation_last():
    rows = [
        ("Mars", _make_row(elevation=10.0)),
        ("Moon", _make_row(elevation=None)),
        ("Jupiter", _make_row(elevation=60.0)),
    ]
    sorted_result = sort_rows(rows)
    names = [name for name, _ in sorted_result]
    assert names == ["Jupiter", "Mars", "Moon"]


def test_format_row_styled_above_horizon():
    row = _make_row(elevation=45.0)
    result = format_row_styled("Jupiter", row)
    assert all(isinstance(cell, str) for cell in result)


def test_format_row_styled_below_horizon():
    row = _make_row(elevation=-10.0)
    result = format_row_styled("Saturn", row)
    assert all(isinstance(cell, Text) for cell in result)
    assert all(cell.style == "dim" for cell in result)


def test_format_row_styled_none_elevation():
    row = _make_row(elevation=None)
    result = format_row_styled("Moon", row)
    assert all(isinstance(cell, Text) for cell in result)
