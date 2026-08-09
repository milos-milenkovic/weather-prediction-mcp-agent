# Demo Prompts

Capture screenshots showing both the tool call and final answer for at least
three natural-language questions.

## Demo 1 — current conditions
> What's the weather in Chicago right now? Give me the temperature, humidity,
> wind, and a one-sentence summary.

Expected tool: `get_current_weather`

## Demo 2 — forecast + umbrella prediction
> Will I need an umbrella in Austin tomorrow? Use the forecast and explain the
> numbers behind your recommendation.

Expected tools: `get_forecast` and/or `predict_umbrella_needed`

## Demo 3 — practical recommendation
> I'm sightseeing in Stockholm this weekend. Pick Saturday and tell me whether
> conditions look good, whether I need a jacket or rain protection, and why.

Expected tool: `get_travel_recommendation` (optionally `get_forecast` too)

## Stretch demo — compare cities
> I can spend Saturday in Copenhagen, Berlin, or Amsterdam. Which city has the
> best weather for walking outdoors? Compare them and explain the ranking.

Expected tool: `compare_weather`

## Error-handling demo
> What's the weather in Xqzzzz tomorrow?

Expected behavior: clean tool error and a request to clarify; no hallucinated
weather.
