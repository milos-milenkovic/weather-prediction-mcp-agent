# Weather Prediction MCP Server + Databricks Agent

A Day 3 Databricks AI Boot Camp homework project that exposes real weather
forecasting tools through **FastMCP**, then connects those tools to a
**Databricks Agent Bricks agent**.

The project uses **Open-Meteo**, so no API key or paid account is required.

## Architecture

```text
User
  ↓ natural language
Databricks Agent Bricks agent
  ↓ MCP tool calls
mcp_server/weather_mcp_server.py
  ↓ thin tool wrappers
mcp_server/weather_adapter.py
  ↓ HTTPS
Open-Meteo Geocoding + Forecast APIs

Optional:
dashboard/app.py
  ↓ same adapter logic
Open-Meteo
```

The separation mirrors the Day 3 lab pattern: the MCP file exposes tools, while
the adapter owns HTTP calls, retry/error handling, location resolution, parsing,
and derived prediction logic.

## Weather provider

**Open-Meteo**

- No signup or API key for the non-commercial homework use case.
- Global geocoding for city/postcode-style inputs.
- Current conditions and forecasts up to 16 days.
- Daily temperature, precipitation probability, weather code, wind, sunrise,
  and sunset are used by this project.

No secrets are required or committed.

## MCP tools

Required:
- `get_current_weather(location)`
- `get_forecast(location, days)`
- `predict_umbrella_needed(location, date, precipitation_threshold_pct=40)`

Stretch:
- `get_travel_recommendation(location, date)`
- `compare_weather(locations, date)`
- `health()`

All `@mcp.tool()` functions are intentionally thin. HTTP and parsing live in
`weather_adapter.py`.

## Prediction logic

### Umbrella

An umbrella is recommended if at least one condition is true:

- maximum precipitation probability is at or above 40% by default,
- expected precipitation is at least 1 mm,
- the WMO weather code represents drizzle, rain, rain showers, or thunder.

The tool returns the actual rule(s) that fired.

### Travel/outdoor score

Starts at 100 and subtracts points for:

- moderate/high precipitation probability,
- thunderstorms or snow,
- strong wind gusts,
- very hot daytime temperature,
- very cold minimum temperature.

The score is mapped to `good`, `mixed`, or `poor`, with packing suggestions.

## Error handling

The adapter uses:

- 15-second HTTP timeouts,
- automatic retries with exponential backoff,
- retry support for HTTP 429 and 5xx responses,
- `Retry-After` support,
- clean `WeatherError` messages,
- explicit bad-location and bad-date validation.

The MCP functions return clean error dictionaries so the agent can ask for
clarification instead of surfacing a stack trace.

## Project structure

```text
weather-prediction-mcp-homework/
├── mcp_server/
│   ├── weather_mcp_server.py
│   ├── weather_adapter.py
│   ├── pyproject.toml
│   ├── requirements.txt
│   └── app.yaml
├── dashboard/
│   ├── app.py
│   ├── weather_adapter.py
│   ├── requirements.txt
│   └── app.yaml
├── agent/
│   ├── AGENT_SYSTEM_PROMPT.md
│   ├── TOOL_LIST.md
│   └── DEMO_PROMPTS.md
├── screenshots/
│   └── README.md
├── .gitignore
├── README.md
└── SUBMISSION.md
```

## Deploy the MCP server in Databricks

1. Push this repository to GitHub.
2. Create a Databricks Git folder from the repository.
3. Go to **Compute → Apps → Create app**.
4. Choose the MCP Server starter/template.
5. Name it something beginning with `mcp-`, for example:
   `mcp-weather-predictor`.
6. Point the app source at the repository's `mcp_server/` folder.
7. Deploy.
8. Confirm the app is running. The streamable HTTP endpoint is:
   `https://<app-url>/mcp`.

The MCP app does not need secrets/resources because Open-Meteo is public.

## Connect the agent

Databricks UI wording may vary by workspace preview/version.

1. Open **Agents / Agent Bricks** (or AI Playground when validating tools).
2. Create a tool-calling/custom agent.
3. Add the deployed `mcp-weather-predictor` as a custom/external MCP tool.
   Databricks-hosted MCP apps whose names begin with `mcp-` can be discovered
   directly by supported tool pickers; otherwise use the app's `/mcp` endpoint
   in the external MCP registration flow offered by the workspace.
4. Enable the weather tools.
5. Copy `agent/AGENT_SYSTEM_PROMPT.md` into the agent's system instructions.
6. Test the prompts in `agent/DEMO_PROMPTS.md`.
7. Deploy/save the agent and record its name/URL in `SUBMISSION.md`.

## Optional dashboard

Deploy `dashboard/` as a second Databricks App. It provides a human-facing
current-weather, forecast, and travel-recommendation view and uses the same
adapter/decision logic as the MCP server.

Suggested app name:

`weather-prediction-dashboard`

No secrets/resources are required.

## Evidence to capture

At minimum, capture three screenshots from Agent Bricks/Playground:

1. natural-language current-weather question → tool call → final answer,
2. umbrella question → prediction tool → final answer,
3. travel recommendation → tool call → final answer.

Recommended extras:

4. tool list showing the custom MCP server,
5. MCP app deployment page/URL,
6. optional dashboard,
7. clean bad-location error behavior.

Name screenshots according to `screenshots/README.md`.

## Submission

Before submitting:

- push the final code to your own GitHub repository,
- fill in the URLs in `SUBMISSION.md`,
- add at least three tool-call screenshots under `screenshots/`,
- submit/share the GitHub repository URL plus Databricks App URL(s), or use
  screenshots if workspace access cannot be shared.
