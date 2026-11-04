"""
agent.py
--------
Vivasayi Climate Guide – Strands Agents SDK agent.

Supports two modes:
  - BEDROCK mode  : full Strands Agent with Amazon Bedrock (requires AWS account).
  - DEMO mode     : real weather data + rule-based analysis, no AWS needed.
                    Activated automatically when AWS credentials are absent,
                    or by setting DEMO_MODE=true in the environment / .env file.

Usage:
    from agent import run_climate_agent
    result = run_climate_agent("Chennai", "rice", "Will it be too hot this week?")
    print(result["response"])
"""

from __future__ import annotations

import json
import os
from typing import Any

from dotenv import load_dotenv

from prompts.climate_prompt import CLIMATE_SYSTEM_PROMPT
from tools.weather_tool import get_weather_forecast

load_dotenv()

# ── Configuration ─────────────────────────────────────────────────────────────

DEFAULT_MODEL_ID = "us.amazon.nova-lite-v1:0"
BEDROCK_MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", DEFAULT_MODEL_ID)
AWS_REGION       = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")

# Force demo mode via env var, or auto-detect when credentials are missing
_FORCE_DEMO = os.environ.get("DEMO_MODE", "").lower() in ("1", "true", "yes")


def _aws_credentials_available() -> bool:
    """Return True if boto3 can find usable AWS credentials."""
    try:
        import boto3
        boto3.client("sts", region_name=AWS_REGION).get_caller_identity()
        return True
    except Exception:
        return False


def _use_demo_mode() -> bool:
    """Decide whether to run in demo mode (no Bedrock needed)."""
    if _FORCE_DEMO:
        return True
    return not _aws_credentials_available()


# ── Bedrock / Strands agent (used when AWS is available) ─────────────────────

_agent = None   # module-level Strands Agent instance


def _get_strands_agent():
    """Build and cache the Strands Agent (only called when AWS is available)."""
    global _agent
    if _agent is None:
        from strands import Agent
        from strands.models import BedrockModel
        _agent = Agent(
            model=BedrockModel(model_id=BEDROCK_MODEL_ID, region_name=AWS_REGION),
            system_prompt=CLIMATE_SYSTEM_PROMPT,
            tools=[get_weather_forecast],
        )
    return _agent


def _run_with_bedrock(location: str, crop: str, question: str) -> dict[str, Any]:
    """Run the real Strands Agent with Amazon Bedrock."""
    farmer_message = (
        f"Location: {location}\n"
        f"Crop: {crop if crop else 'not specified'}\n"
        f"Question: {question}\n\n"
        "Please retrieve the weather forecast for my location, explain what the "
        "forecast conditions might mean for my farm, and give me a preparedness "
        "checklist based on the actual forecast data."
    )
    try:
        agent  = _get_strands_agent()
        result = agent(farmer_message)
        return {"response": str(result), "success": True, "error": None, "mode": "bedrock"}
    except Exception as exc:
        return {"response": "", "success": False, "error": _classify_error(exc), "mode": "bedrock"}


# ── Demo mode (no AWS needed) ─────────────────────────────────────────────────

def _run_demo_mode(location: str, crop: str, question: str) -> dict[str, Any]:
    """
    Demo mode: fetch REAL weather data from Open-Meteo, then generate a
    structured analysis using rule-based logic — no LLM required.
    The weather data is genuine; only the text interpretation is pre-written.
    """
    # Step 1 — fetch real forecast via the @tool
    raw = get_weather_forecast(location)
    data = json.loads(raw)

    if "error" in data:
        return {
            "response": "",
            "success": False,
            "error": f"Weather data error: {data['error']}",
            "mode": "demo",
        }

    days      = data.get("forecast_days", [])
    source    = data.get("data_source", "Open-Meteo")
    retrieved = data.get("retrieved_at", "")
    loc_name  = data.get("location", location)

    if not days:
        return {"response": "", "success": False,
                "error": "No forecast data returned for this location.", "mode": "demo"}

    # Step 2 — compute simple statistics from real data
    max_temps  = [d["temp_max_c"]        for d in days if d["temp_max_c"]        is not None]
    precip     = [d["precipitation_mm"]  for d in days if d["precipitation_mm"]  is not None]
    conditions = [d["condition"]         for d in days]

    avg_max   = sum(max_temps) / len(max_temps)   if max_temps else None
    total_rain= sum(precip)                        if precip    else 0.0
    peak_temp = max(max_temps)                     if max_temps else None
    min_temp  = min(d["temp_min_c"] for d in days if d.get("temp_min_c") is not None) if days else None

    # Step 3 — identify observable conditions from data
    flags = []
    if peak_temp and peak_temp >= 38:
        flags.append(f"🌡️ **High temperature alert**: Peak temperature of {peak_temp:.1f} °C forecast — potentially stressful for crops and field workers.")
    if avg_max and avg_max >= 35:
        flags.append(f"☀️ **Sustained heat**: Average daily maximum of {avg_max:.1f} °C across the forecast period.")
    if total_rain < 5:
        flags.append(f"🏜️ **Very low rainfall**: Only {total_rain:.1f} mm total forecast — monitor soil moisture closely.")
    elif total_rain < 20:
        flags.append(f"🌤️ **Low rainfall**: {total_rain:.1f} mm total forecast — irrigation may be needed depending on crop stage.")
    if total_rain >= 50:
        flags.append(f"🌧️ **Heavy rainfall**: {total_rain:.1f} mm total forecast — check drainage and watch for waterlogging.")
    heavy = [d for d in days if d.get("precipitation_mm") and d["precipitation_mm"] >= 15]
    if heavy:
        heavy_dates = ", ".join(d["date"] for d in heavy)
        flags.append(f"⛈️ **Heavy rain days**: {heavy_dates} — {len(heavy)} day(s) with ≥15 mm expected.")
    storm_days = [d for d in days if "Thunderstorm" in d.get("condition", "")]
    if storm_days:
        flags.append(f"⚡ **Thunderstorm risk**: {len(storm_days)} day(s) with thunderstorm conditions in the forecast.")

    if not flags:
        flags.append("✅ **No extreme conditions detected** in this 7-day forecast period.")

    # Step 4 — build checklist based on conditions
    checklist_items = [
        "✅ Review the latest official weather forecast for your district (India Meteorological Department: imd.gov.in).",
        "✅ Monitor soil moisture daily and adjust irrigation based on actual conditions.",
        "✅ Check your State Agricultural Department's advisories for crop-specific guidance.",
    ]
    if peak_temp and peak_temp >= 38:
        checklist_items += [
            "✅ Follow official heat safety guidance for outdoor field work — avoid peak afternoon hours.",
            "✅ Ensure adequate water supply for both crops and livestock.",
        ]
    if total_rain < 10:
        checklist_items += [
            "✅ Check water storage and irrigation availability.",
            "✅ Consider mulching to reduce soil moisture loss.",
        ]
    if total_rain >= 50 or heavy:
        checklist_items += [
            "✅ Inspect drainage channels and clear any blockages before heavy rain.",
            "✅ Harvest any mature produce before heavy rain days if possible.",
        ]
    checklist_items.append("✅ Consult a local agronomist for crop-specific decisions before major interventions.")

    # Step 5 — format the 7-day forecast table
    table_rows = ""
    for d in days:
        tmax = f"{d['temp_max_c']:.1f} °C"  if d['temp_max_c']  is not None else "N/A"
        tmin = f"{d['temp_min_c']:.1f} °C"  if d['temp_min_c']  is not None else "N/A"
        rain = f"{d['precipitation_mm']:.1f} mm" if d['precipitation_mm'] is not None else "N/A"
        table_rows += f"| {d['date']} | {tmax} | {tmin} | {rain} | {d['condition']} |\n"

    forecast_table = (
        "| Date | Max Temp | Min Temp | Precipitation | Condition |\n"
        "|------|----------|----------|---------------|-----------|\n"
        + table_rows
    )

    # Step 6 — assemble full response
    crop_str = f" for **{crop}**" if crop else ""
    response = f"""## 🌱 Vivasayi Climate Guide — Weather Analysis

**Location:** {loc_name}  
**Crop{crop_str.replace(' for ', ': ')}**  
**Your question:** *{question}*

---

### 📊 7-Day Weather Forecast

{forecast_table}

> 📂 **Data source:** {source}  
> 🕐 **Retrieved:** {retrieved}

---

### ⚠️ Climate Conditions Observed

Based on the forecast data above:

{chr(10).join(f"- {f}" for f in flags)}

*These are observations from the forecast data. They are not confirmed risk assessments. Actual field conditions may differ.*

---

### ✅ General Preparedness Checklist

{chr(10).join(checklist_items)}

---

> **Important:** This analysis is based on a 7-day gridded weather forecast only.  
> For crop-specific advice, consult your local **Agricultural Extension Officer** or **Krishi Vigyan Kendra (KVK)**.  
> For emergencies, contact your district's **State Disaster Management Authority**.

---
*ℹ️ Running in **Demo Mode** — weather data is real (Open-Meteo), AI interpretation is rule-based.*  
*Add AWS credentials to enable full Strands Agent + Amazon Bedrock AI analysis.*"""

    return {"response": response, "success": True, "error": None, "mode": "demo"}


# ── Public API ────────────────────────────────────────────────────────────────

def run_climate_agent(location: str, crop: str, question: str) -> dict[str, Any]:
    """
    Run the Vivasayi Climate Guide for a farmer query.

    Automatically selects demo mode (no AWS) or Bedrock mode (with AWS).

    Args:
        location: Place name, e.g. 'Chennai' or 'Coimbatore, Tamil Nadu'.
        crop:     Crop name, e.g. 'rice', 'groundnut', 'cotton'.
        question: The farmer's climate question.

    Returns:
        dict with keys: response (str), success (bool), error (str|None), mode (str)
    """
    location = location.strip()
    crop     = crop.strip()
    question = question.strip()

    if not location:
        return {"response": "", "success": False, "error": "Location is required.", "mode": "none"}
    if not question:
        return {"response": "", "success": False, "error": "Please enter a climate question.", "mode": "none"}

    if _use_demo_mode():
        return _run_demo_mode(location, crop, question)
    else:
        return _run_with_bedrock(location, crop, question)


# ── Error classification (Bedrock mode only) ──────────────────────────────────

def _classify_error(exc: Exception) -> str:
    msg = str(exc)
    if "ExpiredTokenException" in msg or "InvalidClientTokenId" in msg:
        return "AWS credentials have expired. Run `aws configure` or `aws sso login`."
    if "AccessDeniedException" in msg or "UnauthorizedException" in msg:
        return (
            f"Access denied to Bedrock model '{BEDROCK_MODEL_ID}'. "
            "Enable it in the Bedrock console → Model access (us-east-1)."
        )
    if "ThrottlingException" in msg:
        return "Amazon Bedrock is throttling requests. Please wait and try again."
    return f"Unexpected error: {msg}"
