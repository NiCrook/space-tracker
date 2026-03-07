from space_tracker.api.horizons import parse_ephemeris


SAMPLE_RESULT = """\
*******************************************************************************
Some header text here
*******************************************************************************
$$SOE
 2026-Mar-07 00:00     22 21 48.06 -11 23 00.4  270.1234    45.6789    1.136   3.884  2.33265492552914  -2.5064899   12.9930 /L
 2026-Mar-08 00:00     22 24 47.61 -11 05 49.6  271.5678    44.3210    1.158   3.907  2.33120549156146  -2.5128926   13.2048 /L
$$EOE
*******************************************************************************
Some footer text here
"""

SAMPLE_RESULT_NA = """\
$$SOE
 2026-Mar-07 00:00     22 21 48.06 -11 23 00.4        n.a.       n.a.    1.136   3.884  2.33265492552914  -2.5064899   12.9930 /L
$$EOE
"""


def test_parse_ephemeris_row_count():
    rows = parse_ephemeris(SAMPLE_RESULT)
    assert len(rows) == 2


def test_parse_ephemeris_first_row():
    rows = parse_ephemeris(SAMPLE_RESULT)
    row = rows[0]
    assert row.datetime == "2026-Mar-07 00:00"
    assert row.ra == "22 21 48.06"
    assert row.dec == "-11 23 00.4"
    assert row.azimuth is not None
    assert abs(row.azimuth - 270.1234) < 0.001
    assert row.elevation is not None
    assert abs(row.elevation - 45.6789) < 0.001
    assert row.magnitude is not None
    assert abs(row.magnitude - 1.136) < 0.001
    assert row.delta_au is not None
    assert abs(row.delta_au - 2.332655) < 0.001
    assert row.solar_elongation is not None
    assert abs(row.solar_elongation - 12.993) < 0.001


def test_parse_ephemeris_na_values():
    rows = parse_ephemeris(SAMPLE_RESULT_NA)
    row = rows[0]
    assert row.azimuth is None
    assert row.elevation is None
    assert row.magnitude is not None


def test_parse_ephemeris_empty():
    result = "$$SOE\n$$EOE\n"
    rows = parse_ephemeris(result)
    assert rows == []
