from space_tracker.api.close_approaches import (
    CloseApproach,
    estimate_diameter,
    parse_close_approaches,
)
from space_tracker.tabs.close_approaches import format_approach_row


SAMPLE_CAD_RESPONSE = {
    "signature": {"source": "NASA/JPL SBDB Close Approach Data API", "version": "1.5"},
    "count": "2",
    "fields": ["des", "orbit_id", "jd", "cd", "dist", "dist_min", "dist_max",
               "v_rel", "v_inf", "t_sigma_f", "h", "diameter", "diameter_sigma",
               "fullname"],
    "data": [
        ["2024 AA", "8", "2460700.5", "2026-Mar-10 00:00", "0.0123456", "0.012",
         "0.013", "12.345", "12.0", "00:05", "24.5", None, None, "  (2024 AA)  "],
        ["2023 BB", "3", "2460705.5", "2026-Mar-15 12:00", "0.0456789", "0.045",
         "0.046", "8.765", "8.5", "00:10", None, None, None, "  (2023 BB)  "],
    ],
}


def test_parse_close_approaches():
    results = parse_close_approaches(SAMPLE_CAD_RESPONSE)
    assert len(results) == 2

    ca = results[0]
    assert ca.designation == "2024 AA"
    assert ca.fullname == "(2024 AA)"
    assert ca.close_approach_date == "2026-Mar-10 00:00"
    assert abs(ca.distance_au - 0.0123456) < 1e-7
    assert abs(ca.v_rel - 12.345) < 0.001
    assert ca.h_mag == 24.5
    assert ca.diameter_min_m is not None
    assert ca.diameter_max_m is not None


def test_parse_close_approaches_null_h():
    results = parse_close_approaches(SAMPLE_CAD_RESPONSE)
    ca = results[1]
    assert ca.h_mag is None
    assert ca.diameter_min_m is None
    assert ca.diameter_max_m is None


def test_parse_close_approaches_empty():
    data = {"signature": {}, "count": "0", "fields": ["des"], "data": None}
    results = parse_close_approaches(data)
    assert results == []


def test_parse_close_approaches_no_data_key():
    data = {"signature": {}, "count": "0", "fields": ["des"]}
    results = parse_close_approaches(data)
    assert results == []


def test_estimate_diameter_known_value():
    # H=22, albedo 0.25: D = 1329/sqrt(0.25) * 10^(-22/5) = 2658 * 10^-4.4 ≈ 0.1058 km
    result = estimate_diameter(22.0)
    assert result is not None
    min_m, max_m = result
    assert min_m < max_m  # high albedo gives smaller diameter
    assert 50 < min_m < 200  # ~105.8 m
    assert 200 < max_m < 500  # ~236.6 m


def test_estimate_diameter_none():
    assert estimate_diameter(None) is None


def test_format_approach_row_with_diameter():
    ca = CloseApproach(
        designation="2024 AA",
        fullname="(2024 AA)",
        close_approach_date="2026-Mar-10 00:00",
        distance_au=0.01234,
        distance_ld=4.80,
        v_rel=12.345,
        h_mag=24.5,
        diameter_min_m=35.0,
        diameter_max_m=78.0,
    )
    row = format_approach_row(ca)
    assert row[0] == "(2024 AA)"
    assert row[1] == "2026-Mar-10 00:00"
    assert row[2] == "0.01234"
    assert row[3] == "4.80"
    assert row[4] == "12.3"
    assert "35" in row[5]
    assert "78" in row[5]


def test_format_approach_row_no_diameter():
    ca = CloseApproach(
        designation="2023 BB",
        fullname="(2023 BB)",
        close_approach_date="2026-Mar-15 12:00",
        distance_au=0.04567,
        distance_ld=17.77,
        v_rel=8.765,
        h_mag=None,
        diameter_min_m=None,
        diameter_max_m=None,
    )
    row = format_approach_row(ca)
    assert row[5] == "---"


def test_format_approach_row_large_diameter_in_km():
    ca = CloseApproach(
        designation="2025 CC",
        fullname="(2025 CC)",
        close_approach_date="2026-Apr-01 06:00",
        distance_au=0.03000,
        distance_ld=11.67,
        v_rel=15.0,
        h_mag=18.0,
        diameter_min_m=1500.0,
        diameter_max_m=3400.0,
    )
    row = format_approach_row(ca)
    assert "km" in row[5]
