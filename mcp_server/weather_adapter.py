from __future__ import annotations

import math
from datetime import date, datetime
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

DEFAULT_TIMEOUT_SECONDS = 15
MAX_FORECAST_DAYS = 16

# WMO Weather interpretation codes used by Open-Meteo.
WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snowfall",
    73: "Moderate snowfall",
    75: "Heavy snowfall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


class WeatherError(RuntimeError):
    """Clean domain error returned to MCP tools instead of raw HTTP exceptions."""


def _session() -> requests.Session:
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        status=3,
        backoff_factor=0.6,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "databricks-weather-prediction-mcp/1.0 "
                "(educational bootcamp project)"
            )
        }
    )
    session.mount("https://", adapter)
    return session


HTTP = _session()


def _get_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    try:
        response = HTTP.get(
            url,
            params=params,
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise WeatherError(
            f"Weather service could not be reached: {exc}"
        ) from exc

    if response.status_code >= 400:
        try:
            payload = response.json()
            reason = payload.get("reason") or payload.get("error")
        except Exception:
            reason = None

        detail = f": {reason}" if reason else ""
        raise WeatherError(
            f"Weather service returned HTTP {response.status_code}{detail}"
        )

    try:
        return response.json()
    except ValueError as exc:
        raise WeatherError(
            "Weather service returned an invalid JSON response."
        ) from exc


def weather_description(code: int | None) -> str:
    if code is None:
        return "Unknown"
    return WEATHER_CODES.get(int(code), f"WMO weather code {code}")


def resolve_location(location: str) -> dict[str, Any]:
    """Resolve a city/postcode-style location string using Open-Meteo geocoding."""
    query = (location or "").strip()
    if len(query) < 2:
        raise WeatherError(
            "Location is too short. Provide a city, city + country, or postcode."
        )

    data = _get_json(
        GEOCODING_URL,
        {
            "name": query,
            "count": 5,
            "language": "en",
            "format": "json",
        },
    )

    results = data.get("results") or []
    if not results:
        raise WeatherError(
            f"No location could be resolved for '{query}'. "
            "Try adding a country or region."
        )

    # Open-Meteo ranks results; use the top result and return enough context
    # for the agent to tell the user what was resolved.
    result = results[0]

    parts = [
        result.get("name"),
        result.get("admin1"),
        result.get("country"),
    ]
    display_name = ", ".join(str(x) for x in parts if x)

    return {
        "query": query,
        "name": result.get("name"),
        "display_name": display_name,
        "country": result.get("country"),
        "country_code": result.get("country_code"),
        "admin1": result.get("admin1"),
        "latitude": float(result["latitude"]),
        "longitude": float(result["longitude"]),
        "timezone": result.get("timezone") or "auto",
    }


def _forecast_payload(
    location: str,
    forecast_days: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    resolved = resolve_location(location)
    days = max(1, min(int(forecast_days), MAX_FORECAST_DAYS))

    params = {
        "latitude": resolved["latitude"],
        "longitude": resolved["longitude"],
        "timezone": "auto",
        "forecast_days": days,
        "current": ",".join(
            [
                "temperature_2m",
                "relative_humidity_2m",
                "apparent_temperature",
                "precipitation",
                "weather_code",
                "wind_speed_10m",
                "wind_gusts_10m",
            ]
        ),
        "daily": ",".join(
            [
                "weather_code",
                "temperature_2m_max",
                "temperature_2m_min",
                "apparent_temperature_max",
                "apparent_temperature_min",
                "precipitation_sum",
                "precipitation_probability_max",
                "wind_speed_10m_max",
                "wind_gusts_10m_max",
                "sunrise",
                "sunset",
            ]
        ),
    }

    data = _get_json(FORECAST_URL, params)
    return resolved, data


def get_current_conditions(location: str) -> dict[str, Any]:
    """Return normalized current weather for a resolved location."""
    resolved, data = _forecast_payload(location, forecast_days=1)
    current = data.get("current") or {}

    if not current:
        raise WeatherError(
            f"Current weather is unavailable for {resolved['display_name']}."
        )

    return {
        "location": resolved["display_name"],
        "resolved_location": resolved,
        "observed_at": current.get("time"),
        "timezone": data.get("timezone"),
        "temperature_c": current.get("temperature_2m"),
        "apparent_temperature_c": current.get("apparent_temperature"),
        "relative_humidity_pct": current.get("relative_humidity_2m"),
        "precipitation_mm": current.get("precipitation"),
        "wind_speed_kmh": current.get("wind_speed_10m"),
        "wind_gusts_kmh": current.get("wind_gusts_10m"),
        "weather_code": current.get("weather_code"),
        "conditions": weather_description(current.get("weather_code")),
    }


def get_daily_forecast(
    location: str,
    days: int = 5,
) -> dict[str, Any]:
    """Return normalized daily forecast rows for up to 16 days."""
    days = max(1, min(int(days), MAX_FORECAST_DAYS))
    resolved, data = _forecast_payload(location, forecast_days=days)
    daily = data.get("daily") or {}

    times = daily.get("time") or []
    if not times:
        raise WeatherError(
            f"Forecast is unavailable for {resolved['display_name']}."
        )

    def value(name: str, index: int):
        values = daily.get(name) or []
        return values[index] if index < len(values) else None

    rows = []
    for i, day in enumerate(times):
        code = value("weather_code", i)
        rows.append(
            {
                "date": day,
                "conditions": weather_description(code),
                "weather_code": code,
                "temperature_max_c": value("temperature_2m_max", i),
                "temperature_min_c": value("temperature_2m_min", i),
                "apparent_temperature_max_c": value(
                    "apparent_temperature_max", i
                ),
                "apparent_temperature_min_c": value(
                    "apparent_temperature_min", i
                ),
                "precipitation_probability_max_pct": value(
                    "precipitation_probability_max", i
                ),
                "precipitation_sum_mm": value("precipitation_sum", i),
                "wind_speed_max_kmh": value("wind_speed_10m_max", i),
                "wind_gusts_max_kmh": value("wind_gusts_10m_max", i),
                "sunrise": value("sunrise", i),
                "sunset": value("sunset", i),
            }
        )

    return {
        "location": resolved["display_name"],
        "resolved_location": resolved,
        "timezone": data.get("timezone"),
        "days": rows,
    }


def _find_day(
    forecast: dict[str, Any],
    target_date: str,
) -> dict[str, Any]:
    try:
        parsed = date.fromisoformat(target_date)
    except ValueError as exc:
        raise WeatherError(
            "Date must use YYYY-MM-DD format."
        ) from exc

    for row in forecast["days"]:
        if row["date"] == parsed.isoformat():
            return row

    available = [row["date"] for row in forecast["days"]]
    raise WeatherError(
        f"Date {target_date} is outside the available forecast window. "
        f"Available dates: {available[0]} through {available[-1]}."
    )


def predict_umbrella_needed(
    location: str,
    target_date: str,
    precipitation_threshold_pct: int = 40,
) -> dict[str, Any]:
    """Apply explicit umbrella logic to the forecast rather than echoing raw data."""
    threshold = max(0, min(int(precipitation_threshold_pct), 100))
    forecast = get_daily_forecast(
        location,
        days=MAX_FORECAST_DAYS,
    )
    day = _find_day(forecast, target_date)

    probability = day.get("precipitation_probability_max_pct")
    precipitation = day.get("precipitation_sum_mm")
    code = day.get("weather_code")

    wet_weather_code = code in {
        51, 53, 55, 56, 57,
        61, 63, 65, 66, 67,
        80, 81, 82, 95, 96, 99,
    }

    probability_trigger = (
        probability is not None and probability >= threshold
    )
    amount_trigger = (
        precipitation is not None and float(precipitation) >= 1.0
    )

    needed = bool(
        probability_trigger
        or amount_trigger
        or wet_weather_code
    )

    reasons = []
    if probability_trigger:
        reasons.append(
            f"maximum precipitation probability is {probability}% "
            f"(threshold {threshold}%)"
        )
    if amount_trigger:
        reasons.append(
            f"forecast precipitation is {precipitation} mm"
        )
    if wet_weather_code:
        reasons.append(
            f"forecast condition is {day['conditions']}"
        )
    if not reasons:
        reasons.append(
            "precipitation probability, amount, and weather code "
            "are all below the umbrella thresholds"
        )

    return {
        "location": forecast["location"],
        "date": target_date,
        "umbrella_recommended": needed,
        "recommendation": (
            "Bring an umbrella."
            if needed
            else "An umbrella is probably not necessary."
        ),
        "reasons": reasons,
        "forecast": day,
        "logic": {
            "precipitation_probability_threshold_pct": threshold,
            "precipitation_amount_threshold_mm": 1.0,
            "wet_weather_code_trigger": True,
        },
    }


def get_travel_recommendation(
    location: str,
    target_date: str,
) -> dict[str, Any]:
    """Produce a simple outdoor/travel recommendation from explicit thresholds."""
    forecast = get_daily_forecast(
        location,
        days=MAX_FORECAST_DAYS,
    )
    day = _find_day(forecast, target_date)

    rain_prob = day.get("precipitation_probability_max_pct") or 0
    high = day.get("temperature_max_c")
    low = day.get("temperature_min_c")
    gusts = day.get("wind_gusts_max_kmh") or 0
    code = day.get("weather_code")

    score = 100
    reasons = []

    if rain_prob >= 70:
        score -= 35
        reasons.append(f"high precipitation probability ({rain_prob}%)")
    elif rain_prob >= 40:
        score -= 20
        reasons.append(f"moderate precipitation probability ({rain_prob}%)")

    if code in {95, 96, 99}:
        score -= 35
        reasons.append("thunderstorm conditions")
    elif code in {71, 73, 75, 77, 85, 86}:
        score -= 20
        reasons.append("snow conditions")

    if gusts >= 60:
        score -= 25
        reasons.append(f"strong wind gusts ({gusts} km/h)")
    elif gusts >= 40:
        score -= 10
        reasons.append(f"breezy conditions ({gusts} km/h gusts)")

    if high is not None and high >= 32:
        score -= 15
        reasons.append(f"hot daytime temperature ({high}°C)")
    if low is not None and low <= 3:
        score -= 15
        reasons.append(f"cold temperature ({low}°C)")

    score = max(0, min(score, 100))

    if score >= 80:
        rating = "good"
        recommendation = (
            "Conditions look generally favorable for outdoor plans."
        )
    elif score >= 55:
        rating = "mixed"
        recommendation = (
            "Plans are reasonable, but prepare for the listed conditions."
        )
    else:
        rating = "poor"
        recommendation = (
            "Consider flexible or indoor plans if possible."
        )

    if not reasons:
        reasons.append(
            "no major precipitation, temperature, wind, or storm thresholds "
            "were triggered"
        )

    packing = []
    if rain_prob >= 40:
        packing.append("umbrella or waterproof layer")
    if low is not None and low <= 10:
        packing.append("jacket or warm layer")
    if high is not None and high >= 27:
        packing.append("water and sun protection")
    if gusts >= 40:
        packing.append("wind-resistant outer layer")

    return {
        "location": forecast["location"],
        "date": target_date,
        "travel_score": score,
        "rating": rating,
        "recommendation": recommendation,
        "reasons": reasons,
        "packing_suggestions": packing,
        "forecast": day,
    }


def compare_locations(
    locations: list[str],
    target_date: str,
) -> dict[str, Any]:
    """Compare travel conditions for 2-5 locations on the same date."""
    cleaned = [x.strip() for x in locations if x and x.strip()]
    if not 2 <= len(cleaned) <= 5:
        raise WeatherError(
            "Provide between 2 and 5 locations to compare."
        )

    comparisons = [
        get_travel_recommendation(location, target_date)
        for location in cleaned
    ]
    ranked = sorted(
        comparisons,
        key=lambda item: item["travel_score"],
        reverse=True,
    )

    return {
        "date": target_date,
        "best_location": ranked[0]["location"],
        "ranking": [
            {
                "location": item["location"],
                "travel_score": item["travel_score"],
                "rating": item["rating"],
                "conditions": item["forecast"]["conditions"],
                "temperature_max_c": item["forecast"]["temperature_max_c"],
                "precipitation_probability_max_pct": item["forecast"][
                    "precipitation_probability_max_pct"
                ],
            }
            for item in ranked
        ],
    }
