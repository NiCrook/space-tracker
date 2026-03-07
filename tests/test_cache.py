from unittest.mock import AsyncMock, patch

import pytest

from space_tracker.api.horizons import EphemerisCache, EphemerisRow
from space_tracker.config import Location


def _row() -> EphemerisRow:
    return EphemerisRow(
        datetime="2026-Mar-07 00:00",
        ra="00 00 00.00",
        dec="+00 00 00.0",
        azimuth=180.0,
        elevation=45.0,
        magnitude=1.0,
        surface_brightness=3.0,
        delta_au=1.5,
        delta_dot=-0.5,
        solar_elongation=90.0,
    )


LOC = Location(latitude=37.77, longitude=-122.42, elevation_km=0.01)


def test_cache_miss_returns_none():
    cache = EphemerisCache()
    result = cache.get("199", LOC, "2026-Mar-07 00:00", "2026-Mar-07 00:01")
    assert result is None


def test_cache_put_and_get():
    cache = EphemerisCache()
    rows = [_row()]
    cache.put(rows, "199", LOC, "2026-Mar-07 00:00", "2026-Mar-07 00:01")
    result = cache.get("199", LOC, "2026-Mar-07 00:00", "2026-Mar-07 00:01")
    assert result is rows


def test_cache_different_params_miss():
    cache = EphemerisCache()
    rows = [_row()]
    cache.put(rows, "199", LOC, "2026-Mar-07 00:00", "2026-Mar-07 00:01")
    # Different command
    assert cache.get("299", LOC, "2026-Mar-07 00:00", "2026-Mar-07 00:01") is None
    # Different time
    assert cache.get("199", LOC, "2026-Mar-07 01:00", "2026-Mar-07 01:01") is None


def test_cache_expired_returns_none():
    cache = EphemerisCache(default_ttl=0.0)
    rows = [_row()]
    cache.put(rows, "199", LOC, "2026-Mar-07 00:00", "2026-Mar-07 00:01")
    result = cache.get("199", LOC, "2026-Mar-07 00:00", "2026-Mar-07 00:01")
    assert result is None


def test_cache_custom_ttl():
    cache = EphemerisCache(default_ttl=9999.0)
    rows = [_row()]
    cache.put(rows, "199", LOC, "2026-Mar-07 00:00", "2026-Mar-07 00:01")
    # Should expire with ttl=0
    result = cache.get("199", LOC, "2026-Mar-07 00:00", "2026-Mar-07 00:01", ttl=0.0)
    assert result is None


@pytest.mark.asyncio
async def test_cache_fetch_caches_result():
    cache = EphemerisCache()
    rows = [_row()]

    with patch("space_tracker.api.horizons.fetch_ephemeris", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = rows
        client = AsyncMock()

        result1 = await cache.fetch(client, "199", LOC, "2026-Mar-07 00:00", "2026-Mar-07 00:01")
        result2 = await cache.fetch(client, "199", LOC, "2026-Mar-07 00:00", "2026-Mar-07 00:01")

        assert result1 == rows
        assert result2 == rows
        assert mock_fetch.call_count == 1  # Only one actual API call


@pytest.mark.asyncio
async def test_cache_fetch_batch():
    cache = EphemerisCache()
    rows = [_row()]

    with patch("space_tracker.api.horizons.fetch_ephemeris", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = rows
        client = AsyncMock()

        commands = {"Mercury": "199", "Venus": "299"}
        result = await cache.fetch_batch(
            client, commands, LOC, "2026-Mar-07 00:00", "2026-Mar-07 00:01"
        )

        assert "Mercury" in result
        assert "Venus" in result
        assert mock_fetch.call_count == 2

        # Second batch call should be fully cached
        await cache.fetch_batch(
            client, commands, LOC, "2026-Mar-07 00:00", "2026-Mar-07 00:01"
        )
        assert mock_fetch.call_count == 2  # No additional calls
