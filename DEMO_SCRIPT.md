# Demo Video Script — Vivasayi Climate Guide
### Duration: under 3 minutes | Format: screen recording + narration

---

## Before you record — checklist

- [ ] App running at http://localhost:8501
- [ ] Browser window at 1280 × 720 or wider
- [ ] Screen recorder started (OBS, Loom, or Windows Game Bar Win+G)
- [ ] Microphone tested
- [ ] Close Slack / notifications
- [ ] Pre-type the inputs so typing is smooth on camera

---

## [0:00 – 0:18]  Opening

**Screen:** App homepage — green header visible, Demo Mode badge showing

> "Hi, I'm Dhanush. This is Vivasayi Climate Guide — a climate resilience
> assistant built for smallholder farmers using the AWS Strands Agents SDK."

> "The problem is simple: weather apps give farmers raw numbers —
> 38 degrees, 2 millimetres of rain. But a farmer growing rice in Tamil Nadu
> needs to know what those numbers actually mean for their field."

---

## [0:18 – 0:35]  Show the app — inputs

**Screen:** Scroll down slowly to the input fields

> "A farmer opens the app, types their location, their crop, and asks a question
> in plain language."

**Type live (pre-typed in notepad, paste to avoid typos):**
- Location: `Madurai, Tamil Nadu`
- Crop: `rice`
- Question: `Is there too much rain expected this week?`

> "Then clicks Analyse."

**Click:** 🔍 Analyse Weather & Get Guidance

> "The app is now making a live call to the Open-Meteo weather API."

---

## [0:35 – 1:10]  Show the response

**Screen:** Wait for the spinner to finish — show the full response loading

> "Here's the result."

**Scroll through the response slowly while narrating:**

> "At the top — the 7-day forecast table. Every value here is real.
> Dates, maximum and minimum temperatures, precipitation in millimetres,
> weather conditions. This came directly from the Open-Meteo API —
> no AI invented these numbers."

> "Below that — climate conditions observed from the data.
> In this case, the forecast is showing heavy rainfall and thunderstorm risk.
> The app identifies that from the actual numbers — not from a guess."

> "And finally — a preparedness checklist.
> Concrete steps the farmer can take right now:
> check drainage, monitor soil moisture, review local advisories."

> "Notice the data source and timestamp at the bottom —
> the farmer knows exactly where this information came from."

---

## [1:10 – 1:35]  Raw weather tab

**Click:** 📊 Raw Weather Data tab

**Type:** `Madurai, Tamil Nadu` → Click 📡 Fetch Raw Forecast

**Screen:** Table loads with 7 days of data

> "This tab shows the raw data the agent is working from.
> Geocoding resolved Madurai to coordinates —
> 9.9 degrees North, 78.1 degrees East —
> then fetched 7 days of daily forecast data.
> This is the exact JSON the weather tool returns to the Strands agent."

---

## [1:35 – 2:05]  How the agent works — code

**Screen:** Switch to VS Code / Kiro, show agent.py briefly

> "Here's the Strands agent. Three lines of code:
> a BedrockModel, a system prompt, and a list of tools."

```python
agent = Agent(
    model=BedrockModel(model_id="us.amazon.nova-lite-v1:0"),
    system_prompt=CLIMATE_SYSTEM_PROMPT,
    tools=[get_weather_forecast],
)
```

**Switch to tools/weather_tool.py — show the @tool decorator**

> "The weather tool uses the @tool decorator from Strands.
> The agent decides when to call it — I didn't write any routing logic."

```python
@tool
def get_weather_forecast(location: str) -> str:
    """Retrieve a 7-day weather forecast for a given location."""
```

**Switch to prompts/climate_prompt.py — highlight the key rule**

> "The system prompt has one hard rule:
> the agent must call the weather tool before making any claim.
> It cannot invent forecast values. If the tool fails, it says so."

---

## [2:05 – 2:30]  Tests

**Screen:** Terminal — run pytest

```
.venv\Scripts\pytest.exe tests\ -v
```

**Screen:** All 8 tests passing

> "I wrote 8 unit tests: valid locations, invalid locations, network failures,
> missing data fields, heat scenarios, rainfall scenarios.
> All 8 pass with mocked API responses — no internet or AWS account needed
> to run the tests."

> "The key test: if the API fails, the tool returns a plain error JSON.
> The agent never silently fills a gap with invented data."

---

## [2:30 – 2:50]  Architecture summary

**Screen:** architecture.md diagram or hand-drawn slide

> "The full flow in one picture:
> Streamlit takes the farmer's input,
> passes it to the Strands agent,
> the agent calls the weather tool,
> the tool hits Open-Meteo,
> the data comes back,
> and the agent interprets it on Amazon Bedrock."

> "No database. No paid APIs. Open-Meteo is completely free."

---

## [2:50 – 3:00]  Closing

**Screen:** Back to the app — full response visible

> "Vivasayi Climate Guide shows how the Strands Agents SDK makes it
> straightforward to build grounded, responsible AI for real people.
> The farmer gets honest, data-backed guidance — not hallucinated advice."

> "Thank you."

---

## Recording tips

| Tip | Detail |
|---|---|
| **Paste inputs** | Pre-type location/crop/question in Notepad, paste to avoid fumbling |
| **Show the spinner** | Don't cut while the app is loading — it proves it's a real live call |
| **Scroll slowly** | Give the viewer time to read the forecast table |
| **Keep code readable** | Zoom VS Code to 16–18pt font before recording |
| **One take is fine** | Trim long pauses in editing rather than re-recording |
| **Captions** | Add auto-captions in YouTube / Loom for accessibility |
| **File format** | MP4 preferred; WebM is acceptable (YouTube supports both) |
