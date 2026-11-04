"""
tools/weather_tool.py
---------------------
Strands @tool that fetches a 7-day weather forecast from the Open-Meteo API
using the Open-Meteo geocoding service to convert a place name into coordinates.

Data source: Open-Meteo (https://open-meteo.com/) — free, no API key required.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import requests
from strands import tool

# ── Constants ────────────────────────────────────────────────────────────────

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
REQUEST_TIMEOUT = 10  # seconds

# WMO weather interpretation codes → human-readable description
# Source: https://open-meteo.com/en/docs (WMO Weather interpretation codes)
WMO_CODES: dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Icy fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snowfall",
    73: "Moderate snowfall",
    75: "Heavy snowfall",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


# ── Helper functions ──────────────────────────────────────────────────────────

def _geocode(location: str) -> dict[str, Any]:
    """
    Convert a location name to latitude/longitude using Open-Meteo geocoding.
    Returns a dict with keys: name, latitude, longitude, country, admin1.
    Raises ValueError if location is not found.
    """
    params = {"name": location, "count": 1, "language": "en", "format": "json"}
    try:
        response = requests.get(GEOCODE_URL, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ConnectionError(f"Geocoding request failed: {exc}") from exc

    data = response.json()
    results = data.get("results")
    if not results:
        raise ValueError(
            f"Location '{location}' was not found. "
            "Try a more specific name such as 'Chennai, India' or 'Coimbatore, Tamil Nadu'."
        )

    place = results[0]
    return {
        "name": place.get("name", location),
        "latitude": place["latitude"],
        "longitude": place["longitude"],
        "country": place.get("country", ""),
        "admin1": place.get("admin1", ""),  # state / province
    }


def _fetch_forecast(latitude: float, longitude: float) -> dict[str, Any]:
    """
    Fetch 7-day daily forecast from Open-Meteo for the given coordinates.
    Returns the raw JSON response as a dict.
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "weathercode",
        ],
        "timezone": "auto",
        "forecast_days": 7,
    }
    try:
        response = requests.get(FORECAST_URL, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ConnectionError(f"Forecast request failed: {exc}") from exc

    return response.json()


def _format_forecast(raw: dict[str, Any], place: dict[str, Any]) -> dict[str, Any]:
    """
    Convert the raw Open-Meteo response into a structured, readable dict.
    Returns a dict that the Strands agent can easily summarise.
    """
    daily = raw.get("daily", {})
    dates: list[str] = daily.get("time", [])
    max_temps: list[float | None] = daily.get("temperature_2m_max", [])
    min_temps: list[float | None] = daily.get("temperature_2m_min", [])
    precip: list[float | None] = daily.get("precipitation_sum", [])
    codes: list[int | None] = daily.get("weathercode", [])

    days = []
    for i, date in enumerate(dates):
        code = codes[i] if i < len(codes) else None
        days.append(
            {
                "date": date,
                "temp_max_c": max_temps[i] if i < len(max_temps) else None,
                "temp_min_c": min_temps[i] if i < len(min_temps) else None,
                "precipitation_mm": precip[i] if i < len(precip) else None,
                "condition": WMO_CODES.get(code, f"Weather code {code}") if code is not None else "Unknown",
            }
        )

    location_label = place["name"]
    if place.get("admin1"):
        location_label += f", {place['admin1']}"
    if place.get("country"):
        location_label += f", {place['country']}"

    return {
        "location": location_label,
        "latitude": place["latitude"],
        "longitude": place["longitude"],
        "forecast_days": days,
        "data_source": "Open-Meteo (https://open-meteo.com/) — free, no API key required",
        "retrieved_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }


# ── Strands tool ──────────────────────────────────────────────────────────────

@tool
def get_weather_forecast(location: str) -> str:
    """
    Retrieve a 7-day weather forecast for a given location.

    This tool calls the Open-Meteo geocoding API to find the location coordinates,
    then fetches a daily forecast including maximum and minimum temperatures,
    precipitation totals, and general weather conditions.

    Args:
        location: A place name, such as 'Chennai', 'Coimbatore, Tamil Nadu',
                  or 'Madurai, India'.

    Returns:
        A JSON string containing:
        - location: resolved place name
        - latitude / longitude: coordinates used
        - forecast_days: list of 7 days, each with date, temp_max_c,
          temp_min_c, precipitation_mm, and condition
        - data_source: attribution string
        - retrieved_at: UTC timestamp of retrieval
        - error (only present on failure): human-readable error message

    The agent MUST include the data_source value when presenting results to
    the user so the farmer knows where the information came from.
    """
    try:
        place = _geocode(location)
        raw = _fetch_forecast(place["latitude"], place["longitude"])
        result = _format_forecast(raw, place)
        return json.dumps(result, ensure_ascii=False, indent=2)

    except ValueError as exc:
        # Location not found
        return json.dumps({"error": str(exc)})
    except ConnectionError as exc:
        # Network or API failure
        return json.dumps(
            {
                "error": str(exc),
                "suggestion": (
                    "Check your internet connection. "
                    "The Open-Meteo service is free and does not require an API key."
                ),
            }
        )
    except Exception as exc:  # noqa: BLE001
        # Unexpected error — never let the agent fill this gap silently
        return json.dumps({"error": f"Unexpected error retrieving weather data: {exc}"})
