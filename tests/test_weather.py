"""
tests/test_weather.py
----------------------
Unit tests for the weather tool (tools/weather_tool.py).

These tests cover:
  1. Valid location geocoding
  2. Invalid location (not found)
  3. Successful weather retrieval (mocked API)
  4. Weather API failure (network error)
  5. Missing weather data fields
  6. Heat-related conditions detection
  7. Rainfall-related conditions detection

Run with:
    pytest tests/ -v
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

# We test the internal helpers directly as well as the @tool entry point.
from tools.weather_tool import (
    WMO_CODES,
    _format_forecast,
    _geocode,
    get_weather_forecast,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

VALID_GEOCODE_RESPONSE = {
    "results": [
        {
            "name": "Chennai",
            "latitude": 13.0827,
            "longitude": 80.2707,
            "country": "India",
            "admin1": "Tamil Nadu",
        }
    ]
}

VALID_FORECAST_RESPONSE = {
    "daily": {
        "time": ["2026-11-02", "2026-11-03", "2026-11-04", "2026-11-05",
                 "2026-11-06", "2026-11-07", "2026-11-08"],
        "temperature_2m_max": [38.5, 37.2, 39.1, 36.8, 35.0, 34.5, 33.2],
        "temperature_2m_min": [28.0, 27.5, 29.0, 26.5, 25.0, 24.5, 24.0],
        "precipitation_sum":  [0.0,  0.0,  0.2,  5.5, 12.0,  0.0,  0.0],
        "weathercode":        [0,    1,    2,    63,   80,    0,    1],
    }
}

EMPTY_GEOCODE_RESPONSE = {"results": []}

HEAT_FORECAST_RESPONSE = {
    "daily": {
        "time": ["2026-11-02", "2026-11-03"],
        "temperature_2m_max": [42.0, 43.5],
        "temperature_2m_min": [32.0, 33.0],
        "precipitation_sum":  [0.0,  0.0],
        "weathercode":        [0,    0],
    }
}

RAIN_FORECAST_RESPONSE = {
    "daily": {
        "time": ["2026-11-02", "2026-11-03"],
        "temperature_2m_max": [28.0, 27.5],
        "temperature_2m_min": [22.0, 21.5],
        "precipitation_sum":  [45.0, 55.0],
        "weathercode":        [65,   82],
    }
}


# ── Test 1: Valid location ────────────────────────────────────────────────────

def test_valid_location_geocoding():
    """Geocoding a real city name returns coordinates and place info."""
    mock_response = MagicMock()
    mock_response.json.return_value = VALID_GEOCODE_RESPONSE
    mock_response.raise_for_status = MagicMock()

    with patch("tools.weather_tool.requests.get", return_value=mock_response):
        result = _geocode("Chennai")

    assert result["name"] == "Chennai"
    assert result["latitude"] == pytest.approx(13.0827, abs=0.01)
    assert result["longitude"] == pytest.approx(80.2707, abs=0.01)
    assert result["country"] == "India"
    assert result["admin1"] == "Tamil Nadu"


# ── Test 2: Invalid location ──────────────────────────────────────────────────

def test_invalid_location_raises_value_error():
    """An unrecognised location name raises a ValueError with a helpful message."""
    mock_response = MagicMock()
    mock_response.json.return_value = EMPTY_GEOCODE_RESPONSE
    mock_response.raise_for_status = MagicMock()

    with patch("tools.weather_tool.requests.get", return_value=mock_response):
        with pytest.raises(ValueError, match="was not found"):
            _geocode("xyzzy_no_such_place_12345")


# ── Test 3: Successful weather retrieval ─────────────────────────────────────

def test_successful_weather_retrieval():
    """
    The @tool returns a valid JSON string with all expected fields
    when both geocoding and forecast APIs respond correctly.
    """
    geocode_mock = MagicMock()
    geocode_mock.json.return_value = VALID_GEOCODE_RESPONSE
    geocode_mock.raise_for_status = MagicMock()

    forecast_mock = MagicMock()
    forecast_mock.json.return_value = VALID_FORECAST_RESPONSE
    forecast_mock.raise_for_status = MagicMock()

    call_count = 0

    def side_effect(url, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return geocode_mock   # first call = geocoding
        return forecast_mock      # second call = forecast

    with patch("tools.weather_tool.requests.get", side_effect=side_effect):
        raw = get_weather_forecast("Chennai")

    data = json.loads(raw)
    assert "error" not in data, f"Unexpected error: {data.get('error')}"
    assert data["location"] == "Chennai, Tamil Nadu, India"
    assert "forecast_days" in data
    assert len(data["forecast_days"]) == 7
    assert "data_source" in data
    assert "retrieved_at" in data
    # Spot-check first day
    day0 = data["forecast_days"][0]
    assert day0["date"] == "2026-11-02"
    assert day0["temp_max_c"] == pytest.approx(38.5)
    assert day0["condition"] == "Clear sky"   # WMO code 0


# ── Test 4: Weather API failure ───────────────────────────────────────────────

def test_weather_api_network_failure():
    """
    A network error during the forecast request returns an error JSON,
    not a Python exception — the @tool handles it gracefully.
    """
    import requests as req_module

    geocode_mock = MagicMock()
    geocode_mock.json.return_value = VALID_GEOCODE_RESPONSE
    geocode_mock.raise_for_status = MagicMock()

    call_count = 0

    def side_effect(url, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return geocode_mock
        raise req_module.ConnectionError("Network unreachable")

    with patch("tools.weather_tool.requests.get", side_effect=side_effect):
        raw = get_weather_forecast("Chennai")

    data = json.loads(raw)
    assert "error" in data
    assert "Forecast request failed" in data["error"] or "Network" in data["error"]


# ── Test 5: Missing weather data fields ──────────────────────────────────────

def test_missing_weather_data_fields():
    """
    If the forecast response is missing some fields (e.g. precipitation),
    _format_forecast fills them with None rather than crashing.
    """
    place = {
        "name": "Chennai",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "country": "India",
        "admin1": "Tamil Nadu",
    }
    # Precipitation and weathercode fields missing
    partial_forecast = {
        "daily": {
            "time": ["2026-11-02"],
            "temperature_2m_max": [38.0],
            "temperature_2m_min": [27.0],
        }
    }

    result = _format_forecast(partial_forecast, place)
    day = result["forecast_days"][0]

    assert day["precipitation_mm"] is None
    assert day["condition"] == "Unknown"
    assert day["temp_max_c"] == pytest.approx(38.0)


# ── Test 6: Heat-related conditions ──────────────────────────────────────────

def test_heat_related_forecast_detected():
    """
    A forecast with consistently high max temperatures (> 40 °C) is
    represented correctly in the formatted output.
    """
    place = {
        "name": "Madurai",
        "latitude": 9.9252,
        "longitude": 78.1198,
        "country": "India",
        "admin1": "Tamil Nadu",
    }
    result = _format_forecast(HEAT_FORECAST_RESPONSE, place)
    days = result["forecast_days"]

    assert all(d["temp_max_c"] >= 40.0 for d in days), (
        "Expected all days to have max temp >= 40 °C for heat scenario"
    )
    assert all(d["precipitation_mm"] == 0.0 for d in days)
    assert all(d["condition"] == "Clear sky" for d in days)


# ── Test 7: Rainfall-related conditions ──────────────────────────────────────

def test_rainfall_related_forecast_detected():
    """
    A forecast with heavy precipitation is represented correctly,
    including correct WMO code descriptions.
    """
    place = {
        "name": "Coimbatore",
        "latitude": 11.0168,
        "longitude": 76.9558,
        "country": "India",
        "admin1": "Tamil Nadu",
    }
    result = _format_forecast(RAIN_FORECAST_RESPONSE, place)
    days = result["forecast_days"]

    assert all(d["precipitation_mm"] >= 40.0 for d in days)
    assert days[0]["condition"] == "Heavy rain"        # WMO code 65
    assert days[1]["condition"] == "Violent rain showers"  # WMO code 82


# ── Test: WMO code map completeness ──────────────────────────────────────────

def test_wmo_codes_map_contains_common_codes():
    """Sanity check that the WMO codes dict has the most common entries."""
    for code in [0, 1, 2, 3, 61, 63, 65, 80, 95]:
        assert code in WMO_CODES, f"WMO code {code} missing from WMO_CODES map"
