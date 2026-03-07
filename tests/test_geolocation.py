import httpx
import pytest

from space_tracker.api.geolocation import detect_location


@pytest.fixture
def ipinfo_response_data() -> dict:
    return {
        "ip": "1.2.3.4",
        "city": "Austin",
        "region": "Texas",
        "country": "US",
        "loc": "30.2672,-97.7431",
        "org": "AS0000 Test ISP",
        "postal": "78701",
        "timezone": "America/Chicago",
    }


@pytest.mark.asyncio
async def test_detect_location_success(ipinfo_response_data: dict) -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=ipinfo_response_data)
    )
    async with httpx.AsyncClient(transport=transport) as client:
        result = await detect_location(client)

    assert result is not None
    assert result.location.latitude == pytest.approx(30.2672)
    assert result.location.longitude == pytest.approx(-97.7431)
    assert result.location.elevation_km == 0.0
    assert result.display_name == "Austin, Texas"


@pytest.mark.asyncio
async def test_detect_location_missing_city(ipinfo_response_data: dict) -> None:
    del ipinfo_response_data["city"]
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=ipinfo_response_data)
    )
    async with httpx.AsyncClient(transport=transport) as client:
        result = await detect_location(client)

    assert result is not None
    assert result.display_name == "Texas"


@pytest.mark.asyncio
async def test_detect_location_http_error() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(500)
    )
    async with httpx.AsyncClient(transport=transport) as client:
        result = await detect_location(client)

    assert result is None


@pytest.mark.asyncio
async def test_detect_location_bad_json() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"ip": "1.2.3.4"})
    )
    async with httpx.AsyncClient(transport=transport) as client:
        result = await detect_location(client)

    assert result is None
