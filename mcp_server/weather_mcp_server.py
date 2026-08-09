from __future__ import annotations

import os
from typing import Any

import uvicorn
from fastmcp import FastMCP

from weather_adapter import (
    WeatherError,
    compare_locations as adapter_compare_locations,
    get_current_conditions,
    get_daily_forecast,
    get_travel_recommendation as adapter_travel_recommendation,
    predict_umbrella_needed as adapter_umbrella_prediction,
)


mcp = FastMCP(name="weather-prediction-mcp")


def _clean_error(operation: str, exc: Exception) -> dict[str, Any]:
    return {
        "ok": False,
        "operation": operation,
        "error": str(exc),
        "instruction": (
            "Do not guess weather data. Ask the user to clarify the location/date "
            "or explain that the weather service is temporarily unavailable."
        ),
    }


@mcp.tool()
def get_current_weather(location: str) -> dict[str, Any]:
    """Get current weather conditions for a city, postcode, or location name.

    Use this tool when the user asks about weather right now, current temperature,
    humidity, wind, or present conditions.

    Args:
        location: Human-readable place such as "Chicago", "Austin, TX",
            "Stockholm, Sweden", or a postcode supported by Open-Meteo geocoding.

    Returns:
        A dictionary containing the resolved location, temperature, apparent
        temperature, humidity, precipitation, wind, gusts, and conditions.
        On failure, returns a clean error dictionary; never invent weather data.
    """
    try:
        return {"ok": True, **get_current_conditions(location)}
    except WeatherError as exc:
        return _clean_error("get_current_weather", exc)


@mcp.tool()
def get_forecast(location: str, days: int = 5) -> dict[str, Any]:
    """Get a multi-day weather forecast, from 1 to 16 days.

    Use this tool for tomorrow, weekend, multi-day, temperature-range, rain,
    or general forecast questions.

    Args:
        location: Human-readable location name.
        days: Number of forecast days to return. Valid range is 1-16.

    Returns:
        Resolved location and one row per day with high/low temperature,
        apparent temperature, precipitation probability and amount, weather
        condition, wind/gusts, sunrise, and sunset.
    """
    try:
        return {"ok": True, **get_daily_forecast(location, days)}
    except (WeatherError, ValueError) as exc:
        return _clean_error("get_forecast", exc)


@mcp.tool()
def predict_umbrella_needed(
    location: str,
    date: str,
    precipitation_threshold_pct: int = 40,
) -> dict[str, Any]:
    """Predict whether the user should bring an umbrella on a specific date.

    This is a derived recommendation, not a raw API passthrough. An umbrella is
    recommended when any of these are true:
      - maximum precipitation probability >= the supplied threshold (40% default)
      - forecast precipitation >= 1 mm
      - the WMO weather code represents drizzle, rain, rain showers, or thunder

    Args:
        location: Human-readable location name.
        date: Target local calendar date in YYYY-MM-DD format.
        precipitation_threshold_pct: Probability threshold from 0-100.

    Returns:
        Boolean umbrella recommendation, human-readable reasons, the forecast
        values used, and the explicit decision thresholds.
    """
    try:
        return {
            "ok": True,
            **adapter_umbrella_prediction(
                location,
                date,
                precipitation_threshold_pct,
            ),
        }
    except (WeatherError, ValueError) as exc:
        return _clean_error("predict_umbrella_needed", exc)


@mcp.tool()
def get_travel_recommendation(
    location: str,
    date: str,
) -> dict[str, Any]:
    """Rate outdoor/travel conditions for one place and date.

    The adapter calculates a 0-100 travel score using explicit rules for
    precipitation probability, thunderstorms/snow, wind gusts, heat, and cold.
    This tool is appropriate for questions such as "Should I bring a jacket?",
    "Is Saturday good for sightseeing?", or "Should we plan indoor activities?"

    Args:
        location: Human-readable location name.
        date: Target local calendar date in YYYY-MM-DD format.

    Returns:
        Travel score, good/mixed/poor rating, explanation, packing suggestions,
        and the underlying forecast values.
    """
    try:
        return {
            "ok": True,
            **adapter_travel_recommendation(location, date),
        }
    except (WeatherError, ValueError) as exc:
        return _clean_error("get_travel_recommendation", exc)


@mcp.tool()
def compare_weather(
    locations: list[str],
    date: str,
) -> dict[str, Any]:
    """Compare forecast suitability across 2-5 locations for the same date.

    Args:
        locations: Two to five city/location strings.
        date: Target date in YYYY-MM-DD format.

    Returns:
        Locations ranked by the same explicit travel-score logic used by
        get_travel_recommendation, including conditions, temperature, and rain
        probability for transparent comparison.
    """
    try:
        return {
            "ok": True,
            **adapter_compare_locations(locations, date),
        }
    except (WeatherError, ValueError) as exc:
        return _clean_error("compare_weather", exc)


@mcp.tool()
def health() -> dict[str, Any]:
    """Return a lightweight health response for MCP deployment validation."""
    return {
        "ok": True,
        "service": "weather-prediction-mcp",
        "provider": "Open-Meteo",
    }


app = mcp.http_app(stateless_http=True)


def main() -> None:
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("DATABRICKS_APP_PORT", "8000")),
    )


if __name__ == "__main__":
    main()
