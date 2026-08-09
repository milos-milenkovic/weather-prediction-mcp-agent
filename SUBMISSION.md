You're right. The problem is that I put multiple fenced code blocks inside one big fenced Markdown block, which breaks the formatting when you copy it.

Use this clean version instead — copy everything below directly into `SUBMISSION.md`:

# Day 3 Homework Submission

## Project

**Weather Prediction MCP Server + Databricks Agent**

## GitHub repository

[https://github.com/milos-milenkovic/weather-prediction-mcp-agent](https://github.com/milos-milenkovic/weather-prediction-mcp-agent)

## Databricks deployments

* MCP Server App: [https://mcp-weather-predictor-7474649573226356.aws.databricksapps.com](https://mcp-weather-predictor-7474649573226356.aws.databricksapps.com)
* Agent: Databricks AI Playground tool-calling agent configured with the deployed `mcp-weather-predictor` Custom MCP Server and the system prompt in `agent/AGENT_SYSTEM_PROMPT.md`

The agent was configured and validated in Databricks AI Playground. A separate agent Databricks App was not deployed because the Databricks Free Edition workspace app limit had already been reached. The included screenshots demonstrate successful MCP tool discovery, tool execution, structured tool output, and grounded final answers.

## Weather API

**Open-Meteo**

Authentication: **none required**

The project uses:

* Open-Meteo Geocoding API to resolve human-readable location names
* Open-Meteo Forecast API for current conditions and multi-day forecasts

No API keys or secrets are required or committed to the repository.

## Architecture

```text
Natural-language question
        ↓
Databricks AI Playground tool-calling agent
        ↓
Custom MCP Server
        ↓
FastMCP weather server
        ↓
Weather adapter
        ↓
Open-Meteo Geocoding + Forecast APIs
```

The MCP server is intentionally separated from the weather adapter:

* `weather_mcp_server.py` exposes thin MCP tool functions
* `weather_adapter.py` owns HTTP requests, retries, parsing, location resolution, validation, and prediction logic

## MCP tools

### Required capabilities

#### `get_current_weather(location)`

Returns current weather conditions including:

* temperature
* apparent temperature
* humidity
* precipitation
* wind speed
* wind gusts
* WMO-derived weather condition

#### `get_forecast(location, days)`

Returns a multi-day forecast including:

* daily high and low temperature
* apparent temperature
* precipitation probability
* precipitation amount
* weather condition
* wind speed and gusts
* sunrise and sunset

#### `predict_umbrella_needed(location, date, precipitation_threshold_pct=40)`

This is a derived prediction tool rather than a raw API passthrough.

An umbrella is recommended when at least one of these conditions is true:

* maximum precipitation probability is greater than or equal to the configured threshold, 40% by default
* expected precipitation is at least 1 mm
* the WMO weather code represents drizzle, rain, rain showers, or thunderstorms

The tool returns both the recommendation and the explicit reasons and thresholds used.

### Additional tools

#### `get_travel_recommendation(location, date)`

Creates a deterministic 0–100 travel/outdoor suitability score using:

* precipitation probability
* thunderstorms or snow
* wind gusts
* high temperatures
* low temperatures

It returns:

* travel score
* `good`, `mixed`, or `poor` rating
* explanation
* packing suggestions
* underlying forecast values

#### `compare_weather(locations, date)`

Compares 2–5 locations for the same date and ranks them using the same travel-suitability logic.

#### `health()`

Provides a lightweight MCP deployment health check.

## Error handling

The weather adapter includes:

* HTTP request timeout handling
* retries with exponential backoff
* retry support for HTTP `429` and `5xx` responses
* `Retry-After` support
* clean handling of unknown locations
* validation of forecast dates
* validation of tool parameters
* clean MCP error responses instead of raw stack traces

If a weather request fails, the agent is instructed to explain the problem or ask the user to clarify rather than hallucinating weather data.

## Agent system prompt and guardrails

The agent system prompt is stored in:

`agent/AGENT_SYSTEM_PROMPT.md`

The prompt requires the agent to:

* use MCP tools for all current and forecast weather claims
* never invent weather values
* use `get_current_weather` for present conditions
* use `get_forecast` for future or multi-day questions
* use `predict_umbrella_needed` for umbrella decisions
* use `get_travel_recommendation` for practical planning questions
* use `compare_weather` when comparing multiple destinations
* report the resolved location returned by the tool
* react cleanly to invalid locations or API failures
* describe forecasts as forecasts rather than certainties
* avoid making safety guarantees
* rely on the explicit recommendation logic returned by the tools rather than inventing new thresholds

## Demonstration evidence

The following screenshots demonstrate the agent's natural-language prompt, MCP tool call, structured tool output, and final grounded answer.

### 1. Current weather

Screenshot:

`/screenshots/01_current_weather_tool_call_and_answer.png`

Prompt:

> What's the weather in Chicago right now? Give me the temperature, humidity, wind, and a one-sentence summary.

Demonstrated tool:

`get_current_weather`

The agent successfully resolved Chicago, retrieved current Open-Meteo weather data, and generated its answer from the MCP tool output.

### 2. Umbrella prediction

Screenshot:

`/screenshots/02_umbrella_prediction_tool_call_and_answer.png`

Prompt:

> Will I need an umbrella in Austin tomorrow? Use the forecast and explain the numbers behind your recommendation.

Demonstrated tool:

`predict_umbrella_needed`

The agent resolved "tomorrow" to a concrete date, called the derived prediction tool, and explained the recommendation using the returned precipitation probability, expected precipitation amount, and configured threshold.

### 3. Travel recommendation

Screenshot:

`/screenshots/03_travel_recommendation_tool_call_and_answer.png`

Prompt:

> I'm sightseeing in Stockholm this weekend. Pick Saturday and tell me whether conditions look good, whether I need a jacket or rain protection, and why.

Demonstrated tool:

`get_travel_recommendation`

The agent resolved Saturday to a concrete date and used the derived travel score, weather conditions, and packing suggestions returned by the MCP tool.

## Requirements coverage

The submission includes:

* FastMCP-based MCP server
* separate weather adapter module
* public weather API integration
* no hardcoded secrets
* current conditions tool
* multi-day forecast tool
* derived prediction/recommendation tool
* additional comparison and travel tools
* retry and error handling
* `requirements.txt`
* `pyproject.toml`
* `app.yaml`
* deployed Databricks MCP App
* Databricks AI Playground agent configured with the MCP server
* explicit agent system prompt and guardrails
* README documentation
* three natural-language demonstrations with visible tool calls and final answers

## Notes

The MCP server is deployed as a Databricks App named:

`mcp-weather-predictor`

The deployed application successfully exposes the weather tools through the custom MCP integration used by Databricks AI Playground.

Open-Meteo was selected because it requires no API key for this project and provides the location resolution, current conditions, and forecast data needed for all required homework capabilities.
