from datetime import date
from unittest.mock import patch

from space_tracker.api.events import (
    CelestialEvent,
    EventType,
    get_eclipses,
    get_meteor_showers,
    compute_oppositions,
    compute_conjunctions,
    get_all_events,
    _cache,
)
from space_tracker.tabs.events_calendar import format_event_row


def test_get_meteor_showers_returns_all():
    showers = get_meteor_showers(2026)
    assert len(showers) == 10


def test_get_meteor_showers_correct_dates():
    showers = get_meteor_showers(2026)
    perseids = [s for s in showers if s.name == "Perseids"][0]
    assert perseids.date_peak == date(2026, 8, 12)


def test_get_meteor_showers_event_type():
    showers = get_meteor_showers(2026)
    assert all(s.event_type == EventType.METEOR_SHOWER for s in showers)


def test_get_eclipses_2026():
    eclipses = get_eclipses(2026)
    assert len(eclipses) == 4
    names = [e.name for e in eclipses]
    assert "Total Solar Eclipse" in names


def test_get_eclipses_empty_year():
    eclipses = get_eclipses(2099)
    assert eclipses == []


def test_compute_oppositions_finds_jupiter():
    oppositions = compute_oppositions(2026)
    names = [o.name for o in oppositions]
    assert any("Jupiter" in n for n in names)


def test_compute_conjunctions_finds_events():
    conjunctions = compute_conjunctions(2026)
    assert len(conjunctions) >= 1


def test_get_all_events_sorted_by_date():
    _cache.clear()
    events = get_all_events(2026)
    dates = [e.date_peak for e in events]
    assert dates == sorted(dates)


def test_format_event_row_conjunction():
    event = CelestialEvent(
        event_type=EventType.CONJUNCTION,
        name="Venus-Jupiter Conjunction",
        date_peak=date(2026, 5, 15),
        date_end=None,
        description="0.5° separation",
    )
    row = format_event_row(event)
    assert len(row) == 5
    assert row[0] == "Conjunction"
    assert row[1] == "Venus-Jupiter Conjunction"
    assert row[2] == "May 15"
    assert row[4] == "0.5° separation"


def test_format_event_row_meteor_shower_date_range():
    event = CelestialEvent(
        event_type=EventType.METEOR_SHOWER,
        name="Perseids",
        date_peak=date(2026, 8, 12),
        date_end=date(2026, 8, 13),
        description="ZHR ~100, parent: 109P/Swift-Tuttle",
    )
    row = format_event_row(event)
    assert row[2] == "Aug 12 - Aug 13"


@patch("space_tracker.tabs.events_calendar.date")
def test_format_event_row_today(mock_date):
    mock_date.today.return_value = date(2026, 5, 15)
    mock_date.side_effect = lambda *args, **kw: date(*args, **kw)
    event = CelestialEvent(
        event_type=EventType.CONJUNCTION,
        name="Venus-Jupiter Conjunction",
        date_peak=date(2026, 5, 15),
        date_end=None,
        description="0.5° separation",
    )
    row = format_event_row(event)
    assert row[3] == "TODAY"
