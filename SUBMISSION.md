# Day 3 Homework Submission

## Project

**Weather Prediction MCP Server + Databricks Agent**

## GitHub repository

https://github.com/milos-milenkovic/weather-prediction-mcp-agent

## Databricks deployments

- MCP Server App: https://mcp-weather-predictor-7474649573226356.aws.databricksapps.com
- Agent: Databricks AI Playground tool-calling agent using the deployed `mcp-weather-predictor` Custom MCP Server
> The agent was configured and validated in Databricks AI Playground. A separate
> agent Databricks App was not deployed because the Free Edition workspace app
> limit was already reached. The included screenshots demonstrate the agent
> successfully discovering and invoking the custom MCP weather tools.

## Weather API

**Open-Meteo**

Authentication: **none required** for this non-commercial homework project.

The adapter uses:
- Open-Meteo Geocoding API to resolve human-readable locations,
- Open-Meteo Forecast API for current conditions and multi-day forecasts.

## Architecture

```text
Natural-language question
        ↓
Databricks Agent Bricks
        ↓ MCP
FastMCP weather server
        ↓
Weather adapter
        ↓
Open-Meteo APIs
```

Optional dashboard uses the same adapter logic as a second Databricks App.

## Required MCP capabilities

- Current conditions: `get_current_weather`
- Multi-day forecast: `get_forecast`
- Derived prediction: `predict_umbrella_needed`

Additional tools:
- `get_travel_recommendation`
- `compare_weather`
- `health`

## Derived reasoning

`predict_umbrella_needed` is not a passthrough. It applies explicit rules based
on precipitation probability, precipitation amount, and WMO condition codes.

`get_travel_recommendation` adds a transparent 0-100 suitability score based on
rain, storms/snow, wind, heat, and cold, and returns practical packing advice.

## Agent guardrails

The system prompt requires the agent to:

- use tools for all current/forecast weather claims,
- never invent weather data,
- expose the resolved location/date,
- react to clean API errors rather than hallucinating,
- use the dedicated recommendation tools instead of silently inventing
  thresholds,
- avoid safety guarantees and point users to official alerts for hazardous
  weather.

## Demonstration evidence

Add screenshots after deployment:

1. `01_current_weather_tool_call_and_answer.png`
2. `02_umbrella_prediction_tool_call_and_answer.png`
3. `03_travel_recommendation_tool_call_and_answer.png`

Recommended extras:

4. `04_compare_cities_tool_call_and_answer.png`
5. `05_bad_location_error_handling.png`
6. `06_mcp_tool_list.png`
7. `07_optional_dashboard.png`

## Notes

No API keys or secrets are committed because Open-Meteo does not require an API
key for this project.
