# 🌱 Vivasayi Climate Guide

> AI-powered weather and climate risk assistant for smallholder farmers.

Built with the [Strands Agents SDK](https://strandsagents.com), Amazon Bedrock, and [Open-Meteo](https://open-meteo.com) for the **AWS Strands SDK: Workshop to Ship** Hackathon 2026.

---

## What it does

Vivasayi Climate Guide helps smallholder farmers:

- **Understand weather forecasts** — 7-day daily temperatures, precipitation, and conditions for any location.
- **Identify climate-related conditions** — heat stress risk, low rainfall, heavy rain, and dry spells, explained in plain language.
- **Get a preparedness checklist** — general, safe steps the farmer can take based on the actual forecast data.

All weather data comes from the free **Open-Meteo API** (no API key required). AI interpretation runs on **Amazon Bedrock** via the **Strands Agents SDK**. The agent will not invent forecast values or prescribe specific pesticide/fertiliser treatments.

---

## Architecture

```
Farmer (Streamlit UI)
        │
        ▼
  agent.py (Strands Agent)
        │  system_prompt: prompts/climate_prompt.py
        │  tools: [get_weather_forecast]
        │
        ├──▶ tools/weather_tool.py
        │         │
        │         ├──▶ Open-Meteo Geocoding API  (location → coordinates)
        │         └──▶ Open-Meteo Forecast API   (coordinates → 7-day forecast)
        │
        └──▶ Amazon Bedrock (Nova Lite)
                  └──▶ Interprets forecast, generates risk summary + checklist
```

---

## Project Structure

```
vivasayi-climate-guide/
├── app.py                  # Streamlit web interface
├── agent.py                # Strands Agent definition and run_climate_agent()
├── tools/
│   ├── __init__.py
│   └── weather_tool.py     # @tool: get_weather_forecast
├── prompts/
│   ├── __init__.py
│   └── climate_prompt.py   # Agent system prompt
├── tests/
│   ├── __init__.py
│   └── test_weather.py     # Pytest unit tests (7 test cases)
├── results/                # Evaluation outputs (gitignored raw files)
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.10 – 3.13 |
| AWS account | with Bedrock access |
| Amazon Nova Lite | enabled in Bedrock console (Model access) |
| Internet access | for Open-Meteo API calls |

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/vivasayi-climate-guide.git
cd vivasayi-climate-guide
```

### 2. Create and activate a virtual environment

```bash
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure AWS credentials

The app uses your standard AWS credentials — no keys in code or `.env`.

```bash
aws configure
# or, for SSO:
aws sso login
```

Make sure the IAM user/role has the `bedrock:InvokeModel` permission and that **Amazon Nova Lite** (`us.amazon.nova-lite-v1:0`) is enabled in the **Bedrock console → Model access** for `us-east-1`.

### 5. (Optional) Create a `.env` file

```bash
cp .env.example .env
# Edit .env if you want to override the model or region
```

---

## Running the App

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## Running the Tests

```bash
pytest tests/ -v
```

Tests use mocked HTTP responses — **no AWS credentials or internet connection required** to run them.

### Test coverage

| # | Test | What it checks |
|---|---|---|
| 1 | `test_valid_location_geocoding` | Geocoding returns correct coordinates for a real city |
| 2 | `test_invalid_location_raises_value_error` | Unknown location returns a helpful error message |
| 3 | `test_successful_weather_retrieval` | @tool returns all expected fields with correct values |
| 4 | `test_weather_api_network_failure` | Network error is caught; returns error JSON, not exception |
| 5 | `test_missing_weather_data_fields` | Missing API fields are handled gracefully with None |
| 6 | `test_heat_related_forecast_detected` | High-temperature forecast is represented correctly |
| 7 | `test_rainfall_related_forecast_detected` | Heavy-rain forecast maps to correct WMO descriptions |

---

## Configuration

| Environment Variable | Default | Description |
|---|---|---|
| `BEDROCK_MODEL_ID` | `us.amazon.nova-lite-v1:0` | Bedrock model to use |
| `AWS_DEFAULT_REGION` | `us-east-1` | AWS region for Bedrock |

---

## Limitations and Honesty

- **Weather data only** — the app uses a 7-day gridded forecast, not field-level sensors. Conditions at your exact farm may differ.
- **General guidance only** — the preparedness checklist is not a substitute for advice from a certified agronomist or your local agricultural extension office.
- **Language** — the current version responds in English. Tamil translation via Amazon Translate can be added as a future step.
- **Evaluation** — accuracy figures in the test results reflect performance on the test cases in this repository. They do not represent real-world field outcomes.

---

## Data Sources

- Weather forecasts: [Open-Meteo](https://open-meteo.com/) (free, no API key required, CC BY 4.0)
- AI model: Amazon Bedrock — Amazon Nova Lite
- Agent framework: [Strands Agents SDK](https://strandsagents.com)

---

## Hackathon

Built for the **AWS Builder Center: Strands SDK — Workshop to Ship** hackathon (28 Oct – 4 Nov 2026).

Focus area: **Climate Resilience** 🌍

---

## License

Apache 2.0 — see [LICENSE](LICENSE).
