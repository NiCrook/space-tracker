from space_tracker.api.horizons import EphemerisRow, compute_rise_transit_set


def _row(dt: str, elevation: float | None) -> EphemerisRow:
    """Helper to create a minimal EphemerisRow with only datetime and elevation."""
    return EphemerisRow(
        datetime=dt,
        ra="00 00 00.00",
        dec="+00 00 00.0",
        azimuth=180.0,
        elevation=elevation,
        magnitude=None,
        surface_brightness=None,
        delta_au=None,
        delta_dot=None,
        solar_elongation=None,
    )


def test_normal_rise_and_set():
    rows = [
        _row("2026-Mar-07 18:00", -5.0),
        _row("2026-Mar-07 18:10", -2.0),
        _row("2026-Mar-07 18:20", 3.0),  # rise between 18:10 and 18:20
        _row("2026-Mar-07 22:00", 45.0),  # transit (max elevation)
        _row("2026-Mar-08 03:50", 2.0),
        _row("2026-Mar-08 04:00", -1.0),  # set between 03:50 and 04:00
    ]
    rts = compute_rise_transit_set(rows)
    assert rts.rise is not None
    assert "UTC" in rts.rise
    assert rts.transit is not None
    assert rts.transit_elevation == 45.0
    assert rts.set_time is not None


def test_rise_interpolation():
    rows = [
        _row("2026-Mar-07 18:00", -4.0),
        _row("2026-Mar-07 18:10", 6.0),  # rise at 18:04 (4/(4+6) = 0.4 of 10 min)
    ]
    rts = compute_rise_transit_set(rows)
    assert rts.rise == "18:04 UTC"


def test_set_interpolation():
    rows = [
        _row("2026-Mar-07 04:00", 6.0),
        _row("2026-Mar-07 04:10", -4.0),  # set at 04:06 (6/(6+4) = 0.6 of 10 min)
    ]
    rts = compute_rise_transit_set(rows)
    assert rts.set_time == "04:06 UTC"


def test_circumpolar_always_above():
    rows = [
        _row("2026-Mar-07 00:00", 30.0),
        _row("2026-Mar-07 06:00", 50.0),
        _row("2026-Mar-07 12:00", 35.0),
        _row("2026-Mar-07 18:00", 25.0),
    ]
    rts = compute_rise_transit_set(rows)
    assert rts.rise is None
    assert rts.set_time is None
    assert rts.transit is not None
    assert rts.transit_elevation == 50.0


def test_never_rises():
    rows = [
        _row("2026-Mar-07 00:00", -10.0),
        _row("2026-Mar-07 06:00", -8.0),
        _row("2026-Mar-07 12:00", -12.0),
        _row("2026-Mar-07 18:00", -15.0),
    ]
    rts = compute_rise_transit_set(rows)
    assert rts.rise is None
    assert rts.set_time is None
    assert rts.transit is None
    assert rts.transit_elevation is None


def test_none_elevation_handled():
    rows = [
        _row("2026-Mar-07 00:00", None),
        _row("2026-Mar-07 06:00", None),
        _row("2026-Mar-07 12:00", 20.0),
        _row("2026-Mar-07 18:00", None),
    ]
    rts = compute_rise_transit_set(rows)
    # Should not crash; transit found at the one positive row
    assert rts.transit is not None
    assert rts.transit_elevation == 20.0


def test_empty_rows():
    rts = compute_rise_transit_set([])
    assert rts.rise is None
    assert rts.transit is None
    assert rts.transit_elevation is None
    assert rts.set_time is None
