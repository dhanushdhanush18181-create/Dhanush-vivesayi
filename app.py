"""
app.py
------
Vivasayi Climate Guide – Streamlit web interface.

Run with:
    streamlit run app.py
"""

from __future__ import annotations

import json

import streamlit as st

from agent import run_climate_agent, _use_demo_mode
from tools.weather_tool import get_weather_forecast

# Detect mode once at startup
DEMO_MODE = _use_demo_mode()

# ── Page configuration ────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Vivasayi Climate Guide 🌱",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS (green agriculture theme) ─────────────────────────────────────

st.markdown(
    """
    <style>
    /* Main background */
    .stApp {
        background-color: #f0f7ee;
    }

    /* Header strip */
    .app-header {
        background: linear-gradient(135deg, #2d6a4f, #52b788);
        color: white;
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
    }
    .app-header h1 { margin: 0; font-size: 2rem; }
    .app-header p  { margin: 0.4rem 0 0; font-size: 1rem; opacity: 0.9; }

    /* Card containers */
    .info-card {
        background: white;
        border-left: 5px solid #52b788;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin-bottom: 1rem;
    }
    .warn-card {
        background: #fff8e1;
        border-left: 5px solid #f9a825;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin-bottom: 1rem;
    }
    .error-card {
        background: #fdecea;
        border-left: 5px solid #c62828;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin-bottom: 1rem;
    }

    /* Forecast table */
    table { width: 100%; border-collapse: collapse; }
    th { background-color: #2d6a4f; color: white; padding: 8px 12px; text-align: left; }
    td { padding: 8px 12px; border-bottom: 1px solid #d8f3dc; }
    tr:nth-child(even) td { background-color: #f0f7ee; }

    /* Responsive tweaks for small screens */
    @media (max-width: 640px) {
        .app-header h1 { font-size: 1.4rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Header ────────────────────────────────────────────────────────────────────

st.markdown(
    """
    <div class="app-header">
        <h1>🌱 Vivasayi Climate Guide</h1>
        <p>AI-powered weather and climate risk assistant for smallholder farmers</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Mode badge
if DEMO_MODE:
    st.info("🔬 **Demo Mode** — real weather data (Open-Meteo) + rule-based analysis. No AWS account needed.", icon="ℹ️")
else:
    st.success("🤖 **Bedrock Mode** — Strands Agent + Amazon Bedrock AI active.", icon="✅")

# ── Disclaimer ────────────────────────────────────────────────────────────────

st.markdown(
    """
    <div class="warn-card">
    ⚠️ <strong>Disclaimer:</strong> This tool provides general weather-based guidance only.
    It is not a substitute for advice from a certified agronomist or official agricultural
    extension services. Always verify important decisions with local experts.
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Input form ────────────────────────────────────────────────────────────────

st.subheader("🗺️ Your Farm Details")

col1, col2 = st.columns([1, 1])

with col1:
    location = st.text_input(
        "📍 Location",
        placeholder="e.g. Chennai, Tamil Nadu",
        help="Enter your district or nearest town. Be specific for better results.",
    )

with col2:
    crop = st.text_input(
        "🌾 Crop (optional)",
        placeholder="e.g. rice, groundnut, cotton",
        help="Enter the crop you are growing or planning to grow.",
    )

question = st.text_area(
    "❓ Your Climate Question",
    placeholder=(
        "e.g. Will it be too hot for my rice crop this week?\n"
        "     Is there enough rain expected?\n"
        "     Should I worry about drought conditions?"
    ),
    height=100,
    help="Ask any weather or climate-related question about your farm.",
)

# ── Tabs: AI Analysis | Raw Weather Data ─────────────────────────────────────

tab_ai, tab_weather = st.tabs(["🤖 AI Climate Analysis", "📊 Raw Weather Data"])

# ── Analyse button ────────────────────────────────────────────────────────────

with tab_ai:
    analyze_btn = st.button(
        "🔍 Analyse Weather & Get Guidance",
        type="primary",
        use_container_width=True,
        disabled=not (location.strip() and question.strip()),
    )

    if not location.strip():
        st.info("Enter your location above to get started.")
    elif not question.strip():
        st.info("Enter a climate question to run the AI analysis.")

    if analyze_btn:
        with st.spinner("🌦️ Fetching real weather data and running analysis..."):
            result = run_climate_agent(location.strip(), crop.strip(), question.strip())

        if result["success"]:
            mode = result.get("mode", "")
            if mode == "demo":
                st.markdown(
                    """
                    <div class="warn-card">
                    🔬 <strong>Demo Mode</strong> — weather data is <strong>real</strong>
                    (Open-Meteo live API). Interpretation is rule-based.
                    Add AWS credentials to enable full Strands Agent + Bedrock AI.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    """
                    <div class="info-card">
                    ✅ <strong>Analysis complete</strong> — Strands Agent + Amazon Bedrock,
                    based on real forecast data from Open-Meteo.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            st.markdown(result["response"])
        else:
            st.markdown(
                f"""
                <div class="error-card">
                ❌ <strong>Error:</strong> {result["error"]}
                </div>
                """,
                unsafe_allow_html=True,
            )

# ── Raw weather tab ───────────────────────────────────────────────────────────

with tab_weather:
    fetch_btn = st.button(
        "📡 Fetch Raw Forecast",
        type="secondary",
        use_container_width=True,
        disabled=not location.strip(),
    )

    if not location.strip():
        st.info("Enter your location above and click Fetch Raw Forecast.")

    if fetch_btn and location.strip():
        with st.spinner("Fetching forecast from Open-Meteo..."):
            raw_json = get_weather_forecast(location.strip())
            data = json.loads(raw_json)

        if "error" in data:
            st.markdown(
                f"""
                <div class="error-card">
                ❌ <strong>Error:</strong> {data["error"]}
                {data.get("suggestion", "")}
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            # Location and source
            st.markdown(
                f"""
                <div class="info-card">
                📍 <strong>Location resolved:</strong> {data["location"]}<br>
                🌐 <strong>Coordinates:</strong> {data["latitude"]}°N, {data["longitude"]}°E<br>
                🕐 <strong>Retrieved at:</strong> {data["retrieved_at"]}<br>
                📂 <strong>Source:</strong> {data["data_source"]}
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Forecast table
            st.subheader("7-Day Forecast")

            forecast_days = data.get("forecast_days", [])
            if forecast_days:
                # Build a simple HTML table
                rows = ""
                for day in forecast_days:
                    precip = day["precipitation_mm"]
                    precip_str = f"{precip:.1f} mm" if precip is not None else "N/A"
                    tmax = day["temp_max_c"]
                    tmin = day["temp_min_c"]
                    tmax_str = f"{tmax:.1f} °C" if tmax is not None else "N/A"
                    tmin_str = f"{tmin:.1f} °C" if tmin is not None else "N/A"
                    rows += (
                        f"<tr><td>{day['date']}</td>"
                        f"<td>{tmax_str}</td>"
                        f"<td>{tmin_str}</td>"
                        f"<td>{precip_str}</td>"
                        f"<td>{day['condition']}</td></tr>"
                    )

                table_html = f"""
                <table>
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Max Temp</th>
                      <th>Min Temp</th>
                      <th>Precipitation</th>
                      <th>Condition</th>
                    </tr>
                  </thead>
                  <tbody>{rows}</tbody>
                </table>
                """
                st.markdown(table_html, unsafe_allow_html=True)
            else:
                st.warning("No daily forecast data was returned.")

# ── Footer ────────────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown(
    """
    <small>
    Vivasayi Climate Guide | Built with
    <a href="https://strandsagents.com" target="_blank">Strands Agents SDK</a>,
    Amazon Bedrock, and
    <a href="https://open-meteo.com" target="_blank">Open-Meteo</a> |
    AWS Strands SDK Hackathon 2026
    </small>
    """,
    unsafe_allow_html=True,
)
