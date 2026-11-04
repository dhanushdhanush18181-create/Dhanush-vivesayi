# DESIGN.md — Vivasayi Climate Guide

## The decision that must never be wrong
> The weather values shown to the farmer must come from the Open-Meteo API,
> not from the model's parametric memory.

**How it is enforced in code:**
`tools/weather_tool.py` fetches the data and returns it as JSON.
The system prompt (`prompts/climate_prompt.py`) instructs the agent to
*always* call the tool first and base *every* claim on the returned data.
If the tool returns an error, the agent must say so — it cannot fill the gap
with invented values.

---

## Agent flow

```
User input (location, crop, question)
        │
        ▼
  [Strands Agent] ── system prompt sets rules and scope
        │
        ├──▶ @tool get_weather_forecast(location)
        │         │
        │         ├── Geocoding API  →  coordinates
        │         └── Forecast API   →  7-day daily JSON
        │
        ▼
  Agent interprets forecast data
        │
        ├── Identifies observable conditions (heat, rain, dry)
        ├── Generates plain-language risk explanation
        └── Returns preparedness checklist + data source
        │
        ▼
  Streamlit UI renders the response
```

---

## Strands blocks used

| Block | Job | File |
|---|---|---|
| `@tool` (b01_tools) | Real weather data retrieval | `tools/weather_tool.py` |
| System prompt / guardrails | Keeps agent grounded in data | `prompts/climate_prompt.py` |
| Single agent | Orchestrates tool call + response | `agent.py` |

---

## AWS services

| Service | Job |
|---|---|
| Amazon Bedrock (Nova Lite) | Language model for forecast interpretation |
| boto3 / botocore | Python SDK to call Bedrock |

---

## What is measured

| Metric | Description |
|---|---|
| Tool-use recall | % of responses where the weather tool was called |
| Citation completeness | % of responses that include the data_source string |
| Unsafe answer rate | % of responses that invent forecast values |
| Checklist completeness | % of responses that include at least 3 preparedness steps |

Baseline: a single-prompt agent with the same system prompt but no tool.

---

## Out of scope (stretch goals)
- Tamil language output
- SMS alerts via Amazon SNS
- Historical trend analysis
- Multi-crop comparison
- Voice interface (Strands Nova Sonic)

---

## Rubric sanity check

| Quarter | Score | Adjustment needed? |
|---|---|---|
| Social impact | 8 | No |
| Technical execution | 7 | No |
| Communication | 7 | No |
| Originality | 7 | No |
| Buildable in days left | 9 | No |
