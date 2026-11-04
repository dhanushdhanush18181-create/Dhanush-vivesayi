# Architecture Diagram — Vivasayi Climate Guide

```
┌─────────────────────────────────────────────────────────────────┐
│                     Farmer's Browser                            │
│                                                                 │
│   ┌─────────────────────────────────────────────────────┐      │
│   │              Streamlit UI  (app.py)                  │      │
│   │                                                      │      │
│   │  [Location] [Crop] [Question]  [Analyse ▶]          │      │
│   │  ────────────────────────────────────────────────   │      │
│   │  📊 Weather Summary                                  │      │
│   │  ⚠️  Climate Risk Explanation                        │      │
│   │  ✅ Preparedness Checklist                           │      │
│   │  📂 Data Source + Timestamp                          │      │
│   └──────────────────┬──────────────────────────────────┘      │
└──────────────────────┼──────────────────────────────────────────┘
                       │ run_climate_agent(location, crop, question)
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│              Strands Agent  (agent.py)                          │
│                                                                 │
│   System Prompt: prompts/climate_prompt.py                      │
│   Tools: [get_weather_forecast]                                 │
│   Model: Amazon Bedrock — Amazon Nova Lite                      │
│                                                                 │
│   Agent reasoning loop:                                         │
│   1. Receive farmer message                                     │
│   2. Decide to call get_weather_forecast(location)  ──────┐    │
│   3. Receive forecast JSON  ◀──────────────────────────────┘   │
│   4. Interpret data (temperatures, rain, conditions)            │
│   5. Generate risk summary + checklist                          │
│   6. Return structured response                                 │
└──────────────┬──────────────────────────┬───────────────────────┘
               │                          │
               ▼                          ▼
┌──────────────────────────┐   ┌──────────────────────────────────┐
│  tools/weather_tool.py   │   │   Amazon Bedrock  (AWS)          │
│                          │   │                                  │
│  1. Geocoding API call   │   │  Model: us.amazon.nova-lite-v1:0 │
│  open-meteo.com/geocode  │   │  Region: us-east-1               │
│        │                 │   │  Auth: ~/.aws/credentials        │
│        ▼                 │   └──────────────────────────────────┘
│  2. Forecast API call    │
│  api.open-meteo.com      │
│        │                 │
│        ▼                 │
│  3. Format + return JSON │
│  (no API key required)   │
└──────────────────────────┘
```

## Data flow summary

| Step | From | To | Data |
|---|---|---|---|
| 1 | Streamlit UI | agent.py | location, crop, question strings |
| 2 | agent.py | weather_tool.py | location string |
| 3 | weather_tool.py | Open-Meteo geocoding | location string |
| 4 | Open-Meteo geocoding | weather_tool.py | lat/lon coordinates |
| 5 | weather_tool.py | Open-Meteo forecast | lat/lon |
| 6 | Open-Meteo forecast | weather_tool.py | 7-day JSON |
| 7 | weather_tool.py | Strands Agent | formatted forecast JSON string |
| 8 | Strands Agent | Amazon Bedrock | prompt + forecast data |
| 9 | Amazon Bedrock | Strands Agent | interpreted response text |
| 10 | Strands Agent | Streamlit UI | markdown response string |
