from space_tracker.api.horizons import EphemerisRow, RiseTransitSet
from space_tracker.tabs.object_detail import format_detail


def _make_row() -> EphemerisRow:
    return EphemerisRow(
        datetime="2026-Mar-07 00:00",
        ra="05 32 12.30",
        dec="+22 05 30.1",
        azimuth=220.1,
        elevation=45.2,
        magnitude=-2.1,
        surface_brightness=3.5,
        delta_au=4.5678,
        delta_dot=-1.23,
        solar_elongation=120.3,
    )


def test_format_detail_contains_sections():
    row = _make_row()
    rts = RiseTransitSet(
        rise="18:23 UTC",
        transit="23:15 UTC",
        transit_elevation=62.1,
        set_time="04:07 UTC",
    )
    text = format_detail("Jupiter", row, rts)

    assert "Jupiter" in text
    assert "Position" in text
    assert "05 32 12.30" in text
    assert "+22 05 30.1" in text
    assert "45.2" in text
    assert "220.1" in text
    assert "Properties" in text
    assert "-2.1" in text
    assert "4.5678" in text
    assert "120.3" in text
    assert "Rise / Transit / Set" in text
    assert "18:23 UTC" in text
    assert "23:15 UTC" in text
    assert "62.1" in text
    assert "04:07 UTC" in text


def test_format_detail_none_values():
    row = EphemerisRow(
        datetime="2026-Mar-07 00:00",
        ra="05 32 12.30",
        dec="+22 05 30.1",
        azimuth=None,
        elevation=None,
        magnitude=None,
        surface_brightness=None,
        delta_au=None,
        delta_dot=None,
        solar_elongation=None,
    )
    rts = RiseTransitSet(rise=None, transit=None, transit_elevation=None, set_time=None)
    text = format_detail("Pluto", row, rts)

    assert "Pluto" in text
    assert "---" in text
