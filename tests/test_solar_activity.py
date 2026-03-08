from space_tracker.api.donki import (
    SolarFlare,
    GeomagneticStorm,
    CoronalMassEjection,
    parse_solar_flares,
    parse_geomagnetic_storms,
    parse_cmes,
)
from space_tracker.tabs.solar_activity import (
    format_flare_row,
    format_storm_row,
    format_cme_row,
    kp_to_storm_level,
)


SAMPLE_FLARES = [
    {
        "flrID": "2026-03-01T12:00:00-FLR-001",
        "beginTime": "2026-03-01T12:00Z",
        "peakTime": "2026-03-01T12:15Z",
        "endTime": "2026-03-01T12:30Z",
        "classType": "M1.2",
        "sourceLocation": "N23W45",
        "activeRegionNum": 13456,
    },
]

SAMPLE_FLARES_NULL_FIELDS = [
    {
        "flrID": "2026-03-02T08:00:00-FLR-002",
        "beginTime": "2026-03-02T08:00Z",
        "peakTime": None,
        "endTime": None,
        "classType": "C3.4",
        "sourceLocation": None,
        "activeRegionNum": None,
    },
]

SAMPLE_STORMS = [
    {
        "gstID": "2026-02-20T00:00:00-GST-001",
        "startTime": "2026-02-20T00:00Z",
        "allKpIndex": [
            {"kpIndex": 5, "observedTime": "2026-02-20T03:00Z"},
            {"kpIndex": 7, "observedTime": "2026-02-20T06:00Z"},
            {"kpIndex": 4, "observedTime": "2026-02-20T09:00Z"},
        ],
    },
]

SAMPLE_CMES = [
    {
        "activityID": "2026-03-01T10:00:00-CME-001",
        "startTime": "2026-03-01T10:00Z",
        "sourceLocation": "S15E30",
        "activeRegionNum": 13456,
        "cmeAnalyses": [
            {
                "isMostAccurate": False,
                "speed": 500.0,
                "halfAngle": 30.0,
                "type": "S",
            },
            {
                "isMostAccurate": True,
                "speed": 750.0,
                "halfAngle": 45.0,
                "type": "C",
            },
        ],
    },
]


def test_parse_solar_flares():
    results = parse_solar_flares(SAMPLE_FLARES)
    assert len(results) == 1
    flare = results[0]
    assert flare.flr_id == "2026-03-01T12:00:00-FLR-001"
    assert flare.begin_time == "2026-03-01T12:00Z"
    assert flare.peak_time == "2026-03-01T12:15Z"
    assert flare.end_time == "2026-03-01T12:30Z"
    assert flare.class_type == "M1.2"
    assert flare.source_location == "N23W45"
    assert flare.active_region_num == 13456


def test_parse_solar_flares_null_fields():
    results = parse_solar_flares(SAMPLE_FLARES_NULL_FIELDS)
    assert len(results) == 1
    flare = results[0]
    assert flare.peak_time is None
    assert flare.end_time is None
    assert flare.source_location is None
    assert flare.active_region_num is None


def test_parse_solar_flares_empty():
    assert parse_solar_flares([]) == []


def test_parse_geomagnetic_storms():
    results = parse_geomagnetic_storms(SAMPLE_STORMS)
    assert len(results) == 1
    storm = results[0]
    assert storm.gst_id == "2026-02-20T00:00:00-GST-001"
    assert storm.start_time == "2026-02-20T00:00Z"
    assert storm.kp_index_max == 7.0


def test_parse_geomagnetic_storms_empty():
    assert parse_geomagnetic_storms([]) == []


def test_parse_cmes():
    results = parse_cmes(SAMPLE_CMES)
    assert len(results) == 1
    cme = results[0]
    assert cme.activity_id == "2026-03-01T10:00:00-CME-001"
    assert cme.speed == 750.0
    assert cme.half_angle == 45.0
    assert cme.cme_type == "C"
    assert cme.source_location == "S15E30"
    assert cme.active_region_num == 13456


def test_parse_cmes_no_analysis():
    data = [
        {
            "activityID": "2026-03-02T06:00:00-CME-002",
            "startTime": "2026-03-02T06:00Z",
            "sourceLocation": None,
            "activeRegionNum": None,
            "cmeAnalyses": [],
        },
    ]
    results = parse_cmes(data)
    assert len(results) == 1
    cme = results[0]
    assert cme.speed is None
    assert cme.half_angle is None
    assert cme.cme_type is None


def test_kp_to_storm_level():
    assert kp_to_storm_level(4.0) == "Below Storm"
    assert kp_to_storm_level(5.0) == "G1 (Minor)"
    assert kp_to_storm_level(6.0) == "G2 (Moderate)"
    assert kp_to_storm_level(7.0) == "G3 (Strong)"
    assert kp_to_storm_level(8.0) == "G4 (Severe)"
    assert kp_to_storm_level(9.0) == "G5 (Extreme)"


def test_format_flare_row():
    flare = SolarFlare(
        flr_id="FLR-001",
        begin_time="2026-03-01T12:00Z",
        peak_time="2026-03-01T12:15Z",
        end_time="2026-03-01T12:30Z",
        class_type="X5.0",
        source_location="N23W45",
        active_region_num=13456,
    )
    row = format_flare_row(flare)
    assert row == ("X5.0", "2026-03-01T12:15Z", "2026-03-01T12:00Z", "2026-03-01T12:30Z", "N23W45", "13456")


def test_format_storm_row():
    storm = GeomagneticStorm(
        gst_id="GST-001",
        start_time="2026-02-20T00:00Z",
        kp_index_max=7.0,
    )
    row = format_storm_row(storm)
    assert row == ("2026-02-20T00:00Z", "7.0", "G3 (Strong)")


def test_format_cme_row():
    cme = CoronalMassEjection(
        activity_id="CME-001",
        start_time="2026-03-01T10:00Z",
        source_location="S15E30",
        active_region_num=13456,
        speed=750.0,
        half_angle=45.0,
        cme_type="C",
    )
    row = format_cme_row(cme)
    assert row == ("2026-03-01T10:00Z", "750", "C", "45", "S15E30", "13456")
