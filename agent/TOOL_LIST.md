# MCP Tool List

## Required tools

### `get_current_weather(location)`
Returns current temperature, apparent temperature, humidity, precipitation,
wind/gusts, and WMO-derived conditions.

### `get_forecast(location, days=5)`
Returns 1-16 daily forecasts with high/low temperature, precipitation
probability and amount, condition, wind/gusts, sunrise, and sunset.

### `predict_umbrella_needed(location, date, precipitation_threshold_pct=40)`
Derived prediction. Recommends an umbrella when rain probability reaches the
threshold, forecast precipitation reaches 1 mm, or a wet-weather WMO code is
present. Returns the explicit reasons and thresholds.

## Stretch tools

### `get_travel_recommendation(location, date)`
Creates a deterministic 0-100 travel/outdoor score and packing suggestions from
rain, storms/snow, wind, heat, and cold.

### `compare_weather(locations, date)`
Ranks 2-5 locations using the same travel score.

### `health()`
Simple deployment validation tool.
