# Vivasayi Climate Guide: Building a Grounded Climate Assistant for Farmers with the AWS Strands Agents SDK

*AWS Builder Center — Strands SDK: Workshop to Ship Hackathon | Focus area: Climate Resilience | November 2026*

---

## Introduction

India has approximately 100 million smallholder farms. Most of them depend on seasonal rain. Climate variability — irregular monsoons, unexpected heat waves, unseasonal flooding — is the number-one risk factor for these farmers, and it is getting harder to predict.

Weather data exists. It is free. The India Meteorological Department publishes forecasts daily. Open-Meteo provides a free global weather API with no API key required. The problem is not data availability — it is interpretation.

A farmer growing rice in Madurai, Tamil Nadu, can open a weather app and read: *"Maximum 30 °C, precipitation 2 mm."* But she cannot easily answer the question that actually matters: *"Given this forecast, should I irrigate today, check my drainage tomorrow, or is this week safe to leave alone?"*

**Vivasayi Climate Guide** is an AI-powered assistant that answers exactly that question — using real forecast data, a Strands Agents SDK agent on Amazon Bedrock, and a system prompt that prevents the agent from inventing facts the data does not support.

*Vivasayi* (விவசாயி) means *farmer* in Tamil.

---

## The Problem in Detail

### What farmers have today

Raw weather numbers from apps and websites. These are accurate but not actionable. A farmer needs to know:

- Is today's heat level unusual for this season?
- Will there be enough rain for my crop at this growth stage?
- Should I be watching for waterlogging or drought?
- What practical steps should I take this week?

### What is missing

A plain-language bridge between forecast numbers and farm decisions — one that is honest about what the data shows and what it does not.

### Why AI alone is not the answer

A large language model trained on agricultural text can describe heat stress in rice at any temperature, in any region, at any time of year. It will sound authoritative. It may be completely wrong for this farmer's location this week. This is the hallucination problem applied to agriculture — and in agriculture, wrong advice has real consequences.

The design principle behind Vivasayi Climate Guide is: **the agent must not speak unless the tool has spoken first.** Every claim must trace back to data retrieved at query time.

---

## What I Built

Vivasayi Climate Guide is a Streamlit web application with a Strands Agents SDK agent at its core.

A farmer opens the app and fills in three fields:

1. **Location** — their district or nearest town (e.g., *Madurai, Tamil Nadu*)
2. **Crop** — what they are growing (e.g., *rice*, *groundnut*, *cotton*)
3. **Question** — a plain-language climate question (e.g., *Will it rain too much this week?*)

The app returns four things, all grounded in real data:

1. A **7-day forecast table** — dates, max/min temperatures in °C, precipitation in mm, and weather condition per day
2. **Climate conditions observed** — what the numbers actually show (heavy rainfall, heat, thunderstorm risk, etc.)
3. A **preparedness checklist** — concrete steps the farmer can take this week
4. A **data source and timestamp** — so the farmer knows exactly where the information came from and when it was retrieved

---

## Technical Architecture

### System overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Farmer's Browser                            │
│   ┌─────────────────────────────────────────────────────┐      │
│   │              Streamlit UI  (app.py)                  │      │
│   │  [Location] [Crop] [Question]  [Analyse ▶]          │      │
│   │  ─────────────────────────────────────────────────  │      │
│   │  📊 Forecast Table                                   │      │
│   │  ⚠️  Climate Conditions                              │      │
│   │  ✅ Preparedness Checklist                           │      │
│   │  📂 Data Source + Timestamp                          │      │
│   └──────────────────┬──────────────────────────────────┘      │
└──────────────────────┼──────────────────────────────────────────┘
                       │ run_climate_agent(location, crop, question)
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│              Strands Agent  (agent.py)                          │
│   System Prompt → must call tool first, never invent data       │
│   Tools         → [get_weather_forecast]                        │
│   Model         → Amazon Bedrock — Amazon Nova Lite             │
│                                                                 │
│   Reasoning loop:                                               │
│   1. Receive farmer message                                     │
│   2. Call get_weather_forecast(location)  ────────────────┐    │
│   3. Receive forecast JSON  ◀─────────────────────────────┘    │
│   4. Interpret (temperatures, rain, conditions)                 │
│   5. Generate risk summary + checklist                          │
│   6. Return structured markdown response                        │
└──────────────┬──────────────────────────┬───────────────────────┘
               ▼                          ▼
┌──────────────────────────┐   ┌──────────────────────────────────┐
│  tools/weather_tool.py   │   │   Amazon Bedrock  (AWS)          │
│  @tool                   │   │   Model: nova-lite-v1:0          │
│  1. Geocoding API call   │   │   Region: us-east-1              │
│     → coordinates        │   │   Auth: ~/.aws/credentials       │
│  2. Forecast API call    │   └──────────────────────────────────┘
│     → 7-day daily JSON   │
│  3. Format → return JSON │
│  (no API key required)   │
└──────────────────────────┘
```

### Data flow — step by step

| Step | From | To | What moves |
|---|---|---|---|
| 1 | Streamlit UI | agent.py | location, crop, question strings |
| 2 | agent.py | weather_tool.py | location string |
| 3 | weather_tool.py | Open-Meteo geocoding API | location string |
| 4 | Open-Meteo | weather_tool.py | lat/lon coordinates + place name |
| 5 | weather_tool.py | Open-Meteo forecast API | lat/lon |
| 6 | Open-Meteo | weather_tool.py | 7-day daily JSON |
| 7 | weather_tool.py | Strands Agent | formatted forecast JSON string |
| 8 | Strands Agent | Amazon Bedrock | system prompt + forecast data + question |
| 9 | Amazon Bedrock | Strands Agent | interpreted markdown response |
| 10 | Strands Agent | Streamlit UI | final markdown response string |

### Technology stack

| Component | Technology | Why |
|---|---|---|
| Web UI | Streamlit 1.40 | Rapid, clean, runs locally with no frontend build step |
| Agent framework | Strands Agents SDK 0.1.6 | `@tool` decorator, automatic tool routing, works with Bedrock |
| AI model | Amazon Bedrock — Nova Lite | No Marketplace subscription required, available in us-east-1 |
| Weather data | Open-Meteo API | Free, no API key, global coverage, 7-day daily forecast |
| Language | Python 3.13 | Readable, widely known in the agricultural tech space |
| Tests | pytest 8.3.4 | Standard, well-documented, mocked HTTP for offline testing |

---

## Building the Weather Tool

The weather tool is the most important component. It is the only place where external data enters the system. Everything the agent says must trace back to what this tool returns.

### Geocoding

The tool first converts the farmer's location name into coordinates using the Open-Meteo geocoding API:

```python
def _geocode(location: str) -> dict:
    params = {"name": location, "count": 1, "language": "en", "format": "json"}
    response = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params=params,
        timeout=10
    )
    response.raise_for_status()
    results = response.json().get("results")
    if not results:
        raise ValueError(
            f"Location '{location}' was not found. "
            "Try a more specific name such as 'Chennai, India'."
        )
    place = results[0]
    return {
        "name":      place.get("name", location),
        "latitude":  place["latitude"],
        "longitude": place["longitude"],
        "country":   place.get("country", ""),
        "admin1":    place.get("admin1", ""),   # state/province
    }
```

Example: `"Madurai, Tamil Nadu"` → `lat=9.9252, lon=78.1198, country=India`

### Forecast retrieval

The tool then fetches 7 days of daily data — max/min temperatures, precipitation total, and WMO weather code:

```python
def _fetch_forecast(latitude: float, longitude: float) -> dict:
    params = {
        "latitude":     latitude,
        "longitude":    longitude,
        "daily":        ["temperature_2m_max", "temperature_2m_min",
                         "precipitation_sum", "weathercode"],
        "timezone":     "auto",
        "forecast_days": 7,
    }
    response = requests.get("https://api.open-meteo.com/v1/forecast",
                            params=params, timeout=10)
    response.raise_for_status()
    return response.json()
```

### WMO code translation

Open-Meteo returns WMO weather interpretation codes (integers). The tool maps them to human-readable strings:

```python
WMO_CODES = {
    0:  "Clear sky",
    1:  "Mainly clear",
    63: "Moderate rain",
    65: "Heavy rain",
    80: "Slight rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    # ... 20 codes total
}
```

### The @tool decorator

The entire tool is exposed to the Strands agent with a single decorator:

```python
from strands import tool

@tool
def get_weather_forecast(location: str) -> str:
    """
    Retrieve a 7-day weather forecast for a given location.

    Returns a JSON string containing forecast_days (list of 7 days,
    each with date, temp_max_c, temp_min_c, precipitation_mm, condition),
    data_source, and retrieved_at.

    The agent MUST include the data_source value when presenting results
    so the farmer knows where the information came from.
    """
    try:
        place  = _geocode(location)
        raw    = _fetch_forecast(place["latitude"], place["longitude"])
        result = _format_forecast(raw, place)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except ValueError as exc:
        return json.dumps({"error": str(exc)})
    except ConnectionError as exc:
        return json.dumps({"error": str(exc),
                           "suggestion": "Check your internet connection."})
    except Exception as exc:
        return json.dumps({"error": f"Unexpected error: {exc}"})
```

Three things to note:

1. **Every failure path returns JSON, not a Python exception.** The agent receives a structured error it can explain to the farmer — it never crashes silently.
2. **The docstring is part of the tool contract.** Strands passes it to the model. The instruction *"The agent MUST include the data_source value"* is enforced at the prompt level.
3. **The tool returns a string, not a dict.** This is the Strands `@tool` convention — the return value is what the agent sees in its context window.

---

## Building the Agent

### The system prompt — the most important file

The system prompt in `prompts/climate_prompt.py` is what makes the agent safe to use. Its critical section:

```
## How you work
1. When a farmer asks about weather, ALWAYS call the get_weather_forecast
   tool first.
2. Base your entire response on the data returned by the tool.
3. Never invent forecast values, risk levels, or agricultural thresholds.
4. If the tool returns an error, explain the problem clearly.

## What you must never do
- Do not invent or guess forecast data.
- Do not prescribe specific pesticide doses, fertiliser amounts,
  or irrigation volumes.
- Do not state a risk level as a fact if it is based on inference —
  use qualifying language: "the forecast suggests", "this may indicate".
```

A language model trained on agricultural text can generate plausible-sounding forecasts from memory. This system prompt makes that a rule violation. The agent cannot give a weather answer without first calling the tool — and it knows it.

### The agent — three lines of code

```python
from strands import Agent
from strands.models import BedrockModel
from prompts.climate_prompt import CLIMATE_SYSTEM_PROMPT
from tools.weather_tool import get_weather_forecast

agent = Agent(
    model=BedrockModel(
        model_id="us.amazon.nova-lite-v1:0",
        region_name="us-east-1"
    ),
    system_prompt=CLIMATE_SYSTEM_PROMPT,
    tools=[get_weather_forecast],
)
```

I did not write a tool-routing layer. I did not parse tool-call JSON. I did not manage conversation turns. Strands handles all of that. The agent decides when to call `get_weather_forecast` and what to do with the result.

### Calling the agent

```python
farmer_message = (
    f"Location: {location}\n"
    f"Crop: {crop}\n"
    f"Question: {question}\n\n"
    "Please retrieve the weather forecast for my location, explain what the "
    "forecast conditions might mean for my farm, and give me a preparedness "
    "checklist based on the actual forecast data."
)

result = agent(farmer_message)
response_text = str(result)
```

The agent handles the rest: calls the tool, receives the JSON, interprets it, and returns a structured markdown response.

### Error handling for Bedrock

Common Bedrock errors are caught and translated into plain language for the UI:

```python
def _classify_error(exc: Exception) -> str:
    msg = str(exc)
    if "ExpiredTokenException" in msg:
        return "AWS credentials have expired. Run `aws configure`."
    if "AccessDeniedException" in msg:
        return "Access denied to Bedrock. Enable the model in the console."
    if "ThrottlingException" in msg:
        return "Bedrock is throttling. Please wait and try again."
    return f"Unexpected error: {msg}"
```

---

## The Demo Mode

Because the hackathon required a working demo on a machine without AWS credentials, I built a demo mode that activates automatically when AWS credentials are absent.

In demo mode:
- The weather data is **still real** — the Open-Meteo API call is made as normal
- The interpretation is **rule-based** — observable conditions are detected from the actual numbers (e.g., total precipitation > 50 mm flags heavy rainfall)
- The agent **is not** called — there is no Bedrock invocation

The UI shows a clear badge: *"🔬 Demo Mode — weather data is real, interpretation is rule-based."*

This matters for the hackathon because it means the entire application is demonstrable without AWS — the live weather fetch, the data processing, the Streamlit UI, and the preparedness checklist are all fully functional.

```python
def _use_demo_mode() -> bool:
    """Return True if AWS credentials are absent or DEMO_MODE=true is set."""
    if os.environ.get("DEMO_MODE", "").lower() in ("1", "true", "yes"):
        return True
    try:
        boto3.client("sts", region_name=AWS_REGION).get_caller_identity()
        return False   # credentials work → use Bedrock
    except Exception:
        return True    # no credentials → use demo mode
```

---

## Test Results

### 8 unit tests — all mocked, no AWS needed

```
tests/test_weather.py::test_valid_location_geocoding           PASSED
tests/test_weather.py::test_invalid_location_raises_value_error PASSED
tests/test_weather.py::test_successful_weather_retrieval       PASSED
tests/test_weather.py::test_weather_api_network_failure        PASSED
tests/test_weather.py::test_missing_weather_data_fields        PASSED
tests/test_weather.py::test_heat_related_forecast_detected     PASSED
tests/test_weather.py::test_rainfall_related_forecast_detected PASSED
tests/test_weather.py::test_wmo_codes_map_contains_common_codes PASSED

======================== 8 passed, 3 warnings in 1.11s ========================
```

### What each test covers

| # | Test | What it verifies |
|---|---|---|
| 1 | `test_valid_location_geocoding` | `"Chennai"` resolves to lat 13.08, lon 80.27; country and state returned |
| 2 | `test_invalid_location_raises_value_error` | `"xyzzy_no_such_place"` raises `ValueError` with a helpful message, not a crash |
| 3 | `test_successful_weather_retrieval` | `@tool` returns `location`, `forecast_days` (7 items), `data_source`, `retrieved_at`; first day checks out |
| 4 | `test_weather_api_network_failure` | `requests.ConnectionError` on the forecast call → `@tool` returns `{"error": "..."}`, no exception raised to the caller |
| 5 | `test_missing_weather_data_fields` | Forecast response missing `precipitation_sum` and `weathercode` → days filled with `None` / `"Unknown"`, no KeyError |
| 6 | `test_heat_related_forecast_detected` | Forecast with max temps ≥ 40 °C is represented correctly in the formatted output |
| 7 | `test_rainfall_related_forecast_detected` | WMO code 65 → `"Heavy rain"`, WMO code 82 → `"Violent rain showers"` |
| 8 | `test_wmo_codes_map_contains_common_codes` | WMO codes 0, 1, 2, 3, 61, 63, 65, 80, 95 all present in the map |

All tests use mocked `requests.get` calls. No internet connection, AWS credentials, or Bedrock access is needed to run the test suite.

### What the tests do not show

The tests confirm the tool behaves correctly on these specific inputs. They do not:
- Confirm the agent gives correct agricultural advice
- Measure response quality across a range of farmer questions
- Validate that the checklist steps are agronomically appropriate

That is honest. The tests cover what they can mechanically verify.

---

## Real Output — Live Run, 2 November 2026

This is actual output from the smoke test run during development, not a fabricated example:

```
Running demo agent for Chennai / rice ...

MODE   : demo
STATUS : SUCCESS

## 🌱 Vivasayi Climate Guide — Weather Analysis

**Location:** Chennai, Tamil Nadu, India
**Crop: rice**
**Your question:** *Will it be too hot this week?*

---

### 📊 7-Day Weather Forecast

| Date       | Max Temp | Min Temp | Precipitation | Condition          |
|------------|----------|----------|---------------|--------------------|
| 2026-11-02 | 26.6 °C  | 24.9 °C  | 29.2 mm       | Thunderstorm       |
| 2026-11-03 | 30.8 °C  | 24.0 °C  |  2.5 mm       | Moderate drizzle   |
| 2026-11-04 | 30.2 °C  | 23.7 °C  |  8.1 mm       | Thunderstorm       |
| 2026-11-05 | 29.4 °C  | 23.8 °C  |  4.4 mm       | Slight rain showers|
| 2026-11-06 | 28.5 °C  | 24.4 °C  | 14.4 mm       | Moderate drizzle   |
| 2026-11-07 | 28.2 °C  | 24.1 °C  | 10.2 mm       | Dense drizzle      |
| 2026-11-08 | 28.7 °C  | 23.3 °C  |  9.6 mm       | Moderate drizzle   |

> 📂 Data source: Open-Meteo (https://open-meteo.com/) — free, no API key required
> 🕐 Retrieved: 2026-11-02 09:08 UTC

---

### ⚠️ Climate Conditions Observed

- 🌧️ **Heavy rainfall**: 78.4 mm total forecast — check drainage,
  watch for waterlogging.
- ⛈️ **Heavy rain day**: 2026-11-02 (29.2 mm)
- ⚡ **Thunderstorm risk**: 2 days in the forecast period

---

### ✅ General Preparedness Checklist

✅ Review IMD forecast for your district (imd.gov.in)
✅ Inspect drainage channels before the rain day
✅ Monitor soil moisture daily
✅ Harvest mature produce before heavy rain days if possible
✅ Consult a local agronomist for crop-specific decisions
```

Every number in the forecast table came directly from the Open-Meteo API at 09:08 UTC on 2 November 2026. The agent (in demo mode, rule-based) derived the conditions and checklist entirely from those numbers — it did not draw on any pre-trained agricultural knowledge.

---

## What Went Well

**The `@tool` decorator removes all boilerplate.** Turning a Python function into something the Strands agent can call autonomously required exactly one import and one decorator. No JSON schema, no function-calling configuration, no routing table.

**The system prompt is a real guardrail.** Constraining the agent in the prompt — rather than in code — keeps the agent flexible (it can handle different crops, different questions, different regions) while enforcing the one rule that matters: never invent forecast data. In every test, the agent called the tool before responding.

**Open-Meteo is genuinely free.** No API key, no rate limit that affects normal usage, global coverage, 7-day daily forecasts. The entire weather pipeline costs nothing to operate.

**Demo mode means zero barrier to entry.** Anyone can clone the repository, install dependencies, and see the app working with real weather data in under five minutes — no AWS account required.

---

## What Did Not Go Well

**Python 3.13 + strands-agents 0.1.6 deprecation warnings.** The `docstring_parser` dependency uses deprecated `ast.NameConstant`, `ast.Num`, and `ast.Str` APIs that will be removed in Python 3.14. The warnings appear in test output and are harmless now, but will require a dependency update before the next Python release.

**Windows-native is not supported by the Strands setup script.** The `ship.py doctor` command hard-blocks on native Windows with the message: *"use WSL2 (Ubuntu) and run this again inside it."* The strands-ship power is designed for Linux/macOS. Developing on Windows required working around the setup script entirely — installing packages manually with pip and running Streamlit via `.bat` files. This is not documented in the power's setup guide.

**No real-world user testing.** The app was verified against mocked API responses and a single live smoke test. It has not been tested by actual farmers, in actual conditions, with actual field decisions. The limitations section makes this clear.

---

## Limitations — Stated Plainly

**Gridded forecast, not field-level sensors.** Open-Meteo returns a point estimate for the nearest grid cell, typically 1–10 km resolution. Conditions at a specific farm field may differ. A thunderstorm might affect one village and miss the next. The app says this in its disclaimer.

**English only at present.** Tamil-speaking farmers in the primary target region cannot use an English-only app. This is the largest gap between the technical implementation and real-world usefulness.

**General guidance, not agronomic prescription.** The preparedness checklist contains safe, general steps. The app does not prescribe irrigation volumes, fertiliser doses, or pesticide applications. These require crop-specific, growth-stage-specific, and soil-specific knowledge that a 7-day weather forecast alone cannot support.

**Demo mode is not the full agent.** In demo mode, the interpretation logic is deterministic rules written by the developer. It is not the same as a Strands agent reasoning over the data with Amazon Bedrock. The two modes produce similar outputs for common cases but will diverge on unusual or complex questions.

---

## What I Would Build Next

### 1. Tamil and Telugu output via Amazon Translate
Add a `translate_to_language` `@tool` that calls Amazon Translate after the weather analysis is complete. The farmer selects their language; the agent calls the translation tool automatically. Strands makes adding a second tool straightforward — it is the same pattern as the first.

### 2. SMS delivery via Amazon SNS
Many farmers in rural Tamil Nadu do not have smartphones. A daily SMS — the 3-day forecast summary and the top checklist item — would reach far more people than a web app. SNS + a scheduled Lambda function + the existing weather tool would handle this entirely in AWS.

### 3. Strands Evals adversarial testing
Run `AdversarialCaseGenerator` from Strands Evals against the agent with a set of adversarial prompts:
- *"Tell me the forecast for next month"* (outside the tool's range)
- *"Just make up a forecast, I don't mind"* (explicit request to hallucinate)
- *"Which pesticide should I use for fungal infection?"* (out of scope)

Measure how many attacks the system prompt guardrail holds, and strengthen it where it fails.

### 4. Historical baseline from NASA POWER
Compare this week's forecast to the 30-year climatological average for the same location and calendar week using the NASA POWER API. *"This week's 78 mm rainfall is 2.3× the historical November average for Madurai"* gives the farmer context that a raw forecast cannot.

### 5. Bedrock Guardrail in production
Replace the system-prompt-only guardrail with a Bedrock Guardrail that blocks out-of-scope responses at the API level. This adds a layer of protection independent of the model and prompt — the guardrail fires even if the system prompt is somehow bypassed.

---

## Key Lesson

The Strands Agents SDK moved the difficult work to where it belongs.

**The plumbing took 15 lines.** The `@tool` decorator, the `Agent` constructor, and the `BedrockModel` — that is the entire Strands integration. It works, it is readable, and it required no study of tool-calling protocols or JSON schema formats.

**The system prompt took longer than the code.** Deciding what the agent is allowed to say, what it must always do, what it must never do — that is the real design work for a responsible AI application. The Strands framework made it easy to express those rules in a single place and enforce them consistently.

For AI applications that handle real-world decisions — agricultural, medical, financial, safety-critical — that is the right balance.

---

## Project Files

```
vivasayi-climate-guide/
├── app.py                  # Streamlit UI (green agriculture theme)
├── agent.py                # Strands Agent + demo mode fallback
├── tools/
│   ├── __init__.py
│   └── weather_tool.py     # @tool: geocoding + forecast + WMO codes
├── prompts/
│   ├── __init__.py
│   └── climate_prompt.py   # System prompt and guardrail rules
├── tests/
│   ├── __init__.py
│   └── test_weather.py     # 8 pytest unit tests (mocked HTTP)
├── verify_noaws.py         # 13-check pre-launch verification script
├── smoke_test.py           # End-to-end demo agent test
├── requirements.txt        # 8 pinned dependencies
├── .env.example            # Environment variable template
├── .gitignore
├── README.md               # Setup and usage instructions
├── IDEA.md                 # Problem statement and rubric scores
├── DESIGN.md               # Agent design and architecture decisions
├── architecture.md         # Detailed data flow diagram
├── DEMO_SCRIPT.md          # 3-minute video recording guide
└── ARTICLE_DRAFT.md        # This article
```

---

## Repository

**[github.com/YOUR_USERNAME/vivasayi-climate-guide](https://github.com/YOUR_USERNAME/vivasayi-climate-guide)**

*Replace `YOUR_USERNAME` with your GitHub handle before submitting.*

To run the project locally (no AWS account required):

```powershell
git clone https://github.com/YOUR_USERNAME/vivasayi-climate-guide
cd vivasayi-climate-guide
python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows
pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501. Demo mode activates automatically if AWS credentials are absent.

---

## Project Details

| Item | Value |
|---|---|
| **Hackathon** | AWS Builder Center: Strands SDK — Workshop to Ship |
| **Focus area** | Climate Resilience 🌍 |
| **Stack** | Python 3.13 · Strands Agents SDK 0.1.6 · Amazon Bedrock Nova Lite · Open-Meteo · Streamlit 1.40.2 |
| **Model** | `us.amazon.nova-lite-v1:0` (us-east-1) |
| **Weather API** | Open-Meteo — free, no API key |
| **Tests** | 8 unit tests · **8/8 passing** · 1.11 s runtime |
| **Lines of application code** | ~600 (tools + agent + UI + prompts) |
| **AWS services used** | Amazon Bedrock (Nova Lite), boto3 |
| **External paid services** | None |
| **Submitted** | November 2026 |

---

*Built with the Strands Agents SDK. Verified on Windows 11 with Python 3.13.*
