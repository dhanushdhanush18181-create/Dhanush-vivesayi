"""
make_video.py
-------------
Programmatically builds a ~2-minute demo video for Vivasayi Climate Guide.
Uses only PIL (Pillow) + moviepy — no screen recorder, no ffmpeg required.

Output: results/vivasayi_demo.mp4

Each slide is rendered as a 1280x720 PNG frame, held for its duration,
with narration text displayed at the bottom.

Run:
    python make_video.py
"""

import os, sys, textwrap, json
sys.path.insert(0, os.path.dirname(__file__))

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ── Config ─────────────────────────────────────────────────────────────────

W, H   = 1280, 720
FPS    = 24
OUT    = Path("results/vivasayi_demo.mp4")
OUT.parent.mkdir(exist_ok=True)

# Colours (green agriculture theme)
C_BG         = (240, 247, 238)   # light mint
C_HEADER     = (45,  106, 79)    # dark green
C_HEADER_TXT = (255, 255, 255)
C_ACCENT     = (82,  183, 136)   # mid green
C_CARD       = (255, 255, 255)
C_CARD_BORDER= (82,  183, 136)
C_TXT        = (27,  67,  50)    # very dark green
C_NARRATION  = (255, 255, 255)
C_NAR_BG     = (27,  67,  50)    # dark green bar
C_CODE_BG    = (30,  30,  30)
C_CODE_TXT   = (220, 220, 170)
C_CODE_KW    = (86,  156, 214)
C_CODE_STR   = (206, 145, 120)
C_CODE_CMT   = (106, 153, 85)
C_WARN_BG    = (255, 248, 225)
C_WARN_TXT   = (120, 85,  0)
C_OK_BG      = (209, 250, 229)
C_OK_TXT     = (6,   95,  70)
C_TABLE_HDR  = (45,  106, 79)
C_TABLE_ROW1 = (255, 255, 255)
C_TABLE_ROW2 = (240, 247, 238)

# ── Font loader ─────────────────────────────────────────────────────────────

def _font(size, bold=False):
    """Try system fonts, fall back to PIL default."""
    candidates = [
        r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\calibri.ttf",
        r"C:\Windows\Fonts\verdana.ttf",
    ]
    bold_candidates = [
        r"C:\Windows\Fonts\segoeuib.ttf",
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\calibrib.ttf",
        r"C:\Windows\Fonts\verdanab.ttf",
    ]
    paths = bold_candidates if bold else candidates
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()

# Pre-load font sizes
F_TITLE     = _font(52, bold=True)
F_SUBTITLE  = _font(30)
F_HEADING   = _font(36, bold=True)
F_BODY      = _font(24)
F_BODY_BOLD = _font(24, bold=True)
F_SMALL     = _font(19)
F_CODE      = _font(20)
F_NAR       = _font(22)
F_ICON      = _font(28)

# ── Drawing helpers ──────────────────────────────────────────────────────────

def new_frame():
    img = Image.new("RGB", (W, H), C_BG)
    return img, ImageDraw.Draw(img)

def header_bar(d, title, subtitle=""):
    d.rectangle([0, 0, W, 90], fill=C_HEADER)
    d.text((30, 12), title,    font=F_HEADING, fill=C_HEADER_TXT)
    if subtitle:
        d.text((30, 56), subtitle, font=F_SMALL, fill=C_ACCENT)

def narration_bar(d, text, y_start=630):
    d.rectangle([0, y_start, W, H], fill=C_NAR_BG)
    lines = textwrap.wrap(text, width=100)
    for i, line in enumerate(lines[:2]):
        d.text((30, y_start + 8 + i * 30), line, font=F_NAR, fill=C_NARRATION)

def card(d, x, y, w, h, fill=C_CARD, border=C_CARD_BORDER, radius=10):
    d.rounded_rectangle([x, y, x+w, y+h], radius=radius, fill=fill, outline=border, width=2)

def progress_bar(d, step, total, label=""):
    bw = W - 60
    d.rectangle([30, H-35, 30+bw, H-20], fill=(200, 230, 210), outline=C_ACCENT)
    filled = int(bw * step / total)
    if filled > 0:
        d.rectangle([30, H-35, 30+filled, H-20], fill=C_ACCENT)
    if label:
        d.text((30, H-18), label, font=_font(12), fill=C_TXT)

def multiline(d, text, x, y, font, fill, max_width=None, line_height=None):
    lh = line_height or (font.size + 8)
    if max_width:
        # Estimate chars per line from pixel width
        avg_char = font.size * 0.55
        chars = max(10, int(max_width / avg_char))
        lines = textwrap.wrap(text, width=chars)
    else:
        lines = text.split("\n")
    for i, line in enumerate(lines):
        d.text((x, y + i * lh), line, font=font, fill=fill)
    return y + len(lines) * lh

def code_block(d, lines_data, x, y, w):
    """lines_data: list of (text, colour)"""
    lh = 28
    h  = len(lines_data) * lh + 20
    card(d, x, y, w, h, fill=C_CODE_BG, border=(60, 60, 60))
    cy = y + 10
    for text, col in lines_data:
        d.text((x + 14, cy), text, font=F_CODE, fill=col)
        cy += lh
    return y + h

def table_rows(d, headers, rows, x, y, col_widths):
    """Draw a simple table."""
    row_h = 34
    # Header
    cx = x
    for i, (hdr, cw) in enumerate(zip(headers, col_widths)):
        d.rectangle([cx, y, cx+cw, y+row_h], fill=C_TABLE_HDR, outline=C_CARD_BORDER)
        d.text((cx+8, y+8), hdr, font=_font(16, bold=True), fill=C_HEADER_TXT)
        cx += cw
    y += row_h
    for ri, row in enumerate(rows):
        cx = x
        bg = C_TABLE_ROW1 if ri % 2 == 0 else C_TABLE_ROW2
        for val, cw in zip(row, col_widths):
            d.rectangle([cx, y, cx+cw, y+row_h], fill=bg, outline=C_CARD_BORDER)
            d.text((cx+8, y+8), str(val), font=_font(15), fill=C_TXT)
            cx += cw
        y += row_h
    return y


# ══════════════════════════════════════════════════════════════════════════════
# SLIDES
# ══════════════════════════════════════════════════════════════════════════════

def slide_title():
    """Slide 1 — Title card"""
    img, d = new_frame()
    # Big green background block
    d.rectangle([0, 0, W, H], fill=C_HEADER)
    d.rectangle([40, 40, W-40, H-40], fill=C_BG, outline=C_ACCENT, width=3)

    d.text((80, 100), "🌱", font=_font(80), fill=C_ACCENT)
    d.text((80, 195), "Vivasayi Climate Guide", font=_font(54, bold=True), fill=C_HEADER)
    d.text((80, 275), "AI-powered weather assistant for smallholder farmers",
           font=F_SUBTITLE, fill=C_TXT)

    # Tags
    tags = ["Strands Agents SDK", "Amazon Bedrock", "Open-Meteo", "Streamlit"]
    tx = 80
    for tag in tags:
        tw = len(tag) * 14 + 20
        d.rounded_rectangle([tx, 330, tx+tw, 366], radius=6,
                             fill=C_ACCENT, outline=C_HEADER)
        d.text((tx+10, 336), tag, font=_font(17, bold=True), fill=C_HEADER_TXT)
        tx += tw + 12

    d.text((80, 400), "AWS Builder Center — Strands SDK: Workshop to Ship",
           font=_font(20), fill=C_TXT)
    d.text((80, 430), "Focus area: Climate Resilience 🌍  |  November 2026",
           font=_font(20), fill=C_TXT)

    narration_bar(d,
        "Hi, I'm Dhanush. This is Vivasayi Climate Guide — a climate resilience "
        "assistant for smallholder farmers, built with the Strands Agents SDK.",
        y_start=550)
    return img

def slide_problem():
    """Slide 2 — The problem"""
    img, d = new_frame()
    header_bar(d, "🌾  The Problem", "What farmers have — and what they're missing")

    # Left: what they have
    card(d, 30, 105, 590, 420)
    d.text((50, 120), "What farmers have today", font=F_BODY_BOLD, fill=C_HEADER)
    items_have = [
        "📱  Weather apps with raw numbers",
        "🌡️  '38 °C max, 2 mm rain'",
        "📊  Accurate but not actionable",
        "❓  No farm-level interpretation",
    ]
    for i, item in enumerate(items_have):
        d.text((50, 165 + i*55), item, font=F_BODY, fill=C_TXT)

    # Right: what they need
    card(d, 650, 105, 600, 420, fill=C_OK_BG)
    d.text((670, 120), "What they actually need", font=F_BODY_BOLD, fill=C_HEADER)
    items_need = [
        "💧  Should I irrigate today?",
        "🌧️  Will there be enough rain?",
        "🏜️  Is drought risk rising?",
        "✅  What should I do this week?",
    ]
    for i, item in enumerate(items_need):
        d.text((670, 165 + i*55), item, font=F_BODY, fill=C_OK_TXT)

    # Gap arrow
    d.text((603, 280), "→", font=_font(60, bold=True), fill=C_ACCENT)

    d.rectangle([30, 540, W-30, 600], fill=C_WARN_BG, outline=C_ACCENT, width=1)
    d.text((50, 555),
           "⚠️  A language model alone is dangerous here — it can invent a confident-sounding forecast from memory.",
           font=_font(19), fill=C_WARN_TXT)

    narration_bar(d,
        "A farmer in Madurai grows rice. She reads '30°C, 2mm rain'. "
        "But she needs to know: should I irrigate, check drainage, or is this week safe?",
        y_start=615)
    return img

def slide_solution():
    """Slide 3 — Solution overview"""
    img, d = new_frame()
    header_bar(d, "✅  The Solution", "Vivasayi Climate Guide — real data, grounded AI")

    steps = [
        ("1", "Enter location, crop & question", C_ACCENT),
        ("2", "Strands agent calls weather tool", C_HEADER),
        ("3", "Tool fetches REAL forecast from Open-Meteo", C_ACCENT),
        ("4", "Agent interprets data on Amazon Bedrock", C_HEADER),
        ("5", "Farmer receives forecast + checklist", C_ACCENT),
    ]
    for i, (num, text, col) in enumerate(steps):
        y = 115 + i * 95
        d.ellipse([40, y, 82, y+42], fill=col)
        d.text((52, y+6), num, font=_font(22, bold=True), fill=C_HEADER_TXT)
        card(d, 100, y, W-140, 68, fill=C_CARD)
        d.text((120, y+18), text, font=F_BODY, fill=C_TXT)
        if i < len(steps)-1:
            d.line([61, y+42, 61, y+95], fill=C_ACCENT, width=3)

    narration_bar(d,
        "The key design rule: the agent MUST call the weather tool before making any claim. "
        "It cannot invent forecast values. If the tool fails, it says so.",
        y_start=615)
    return img

def slide_app_ui():
    """Slide 4 — App UI mockup"""
    img, d = new_frame()
    header_bar(d, "🖥️  The App", "Streamlit web interface — http://localhost:8501")

    # Browser chrome
    card(d, 30, 100, W-60, H-150, fill=(245,245,245), border=(180,180,180))
    d.rectangle([30, 100, W-30, 135], fill=(220,220,220), outline=(180,180,180))
    d.ellipse([42, 112, 58, 124], fill=(255,100,80))
    d.ellipse([65, 112, 81, 124], fill=(255,190,40))
    d.ellipse([88, 112, 104, 124], fill=(80,200,120))
    d.rounded_rectangle([160, 108, 900, 130], radius=5, fill=(255,255,255), outline=(200,200,200))
    d.text((170, 111), "http://localhost:8501", font=_font(16), fill=(100,100,100))

    # App header inside browser
    d.rectangle([30, 135, W-30, 185], fill=C_HEADER)
    d.text((50, 145), "🌱 Vivasayi Climate Guide", font=_font(25, bold=True),
           fill=C_HEADER_TXT)
    d.text((50, 172), "AI-powered weather and climate risk assistant for smallholder farmers",
           font=_font(14), fill=C_ACCENT)

    # Demo mode badge
    d.rounded_rectangle([40, 195, 660, 225], radius=5, fill=C_WARN_BG, outline=C_ACCENT)
    d.text((55, 202),
           "🔬  Demo Mode — real weather data (Open-Meteo) + rule-based analysis",
           font=_font(16), fill=C_WARN_TXT)

    # Input fields
    fields = [
        ("📍 Location",  "Madurai, Tamil Nadu",                   40,  235),
        ("🌾 Crop",      "rice",                                   680, 235),
    ]
    for label, val, fx, fy in fields:
        d.text((fx, fy), label, font=_font(16, bold=True), fill=C_TXT)
        d.rounded_rectangle([fx, fy+22, fx+290, fy+52], radius=4,
                             fill=C_CARD, outline=C_ACCENT)
        d.text((fx+10, fy+30), val, font=_font(16), fill=C_TXT)

    d.text((40, 300), "❓ Your Climate Question", font=_font(16, bold=True), fill=C_TXT)
    d.rounded_rectangle([40, 322, W-40, 378], radius=4, fill=C_CARD, outline=C_ACCENT)
    d.text((55, 337), "Is there too much rain expected this week?", font=_font(16), fill=C_TXT)

    # Button
    d.rounded_rectangle([40, 390, 420, 430], radius=6, fill=C_HEADER)
    d.text((70, 400), "🔍  Analyse Weather & Get Guidance",
           font=_font(17, bold=True), fill=C_HEADER_TXT)

    # Output preview
    card(d, 40, 445, W-80, 120, fill=C_OK_BG)
    d.text((60, 460), "📊 7-Day Forecast  |  ⚠️ Climate Conditions  |  ✅ Preparedness Checklist",
           font=_font(16, bold=True), fill=C_HEADER)
    d.text((60, 490), "Every value comes directly from Open-Meteo API — nothing invented by AI",
           font=_font(16), fill=C_TXT)
    d.text((60, 520), "📂 Data source + 🕐 Timestamp included in every response",
           font=_font(16), fill=C_TXT)

    narration_bar(d,
        "The farmer types their location, crop, and question, then clicks Analyse. "
        "The app makes a live call to Open-Meteo and returns real forecast data.",
        y_start=615)
    return img

def slide_forecast_output():
    """Slide 5 — Real forecast output (actual data from smoke test)"""
    img, d = new_frame()
    header_bar(d, "📊  Real Forecast Output", "Chennai, Tamil Nadu — 2 November 2026 (actual API data)")

    # Location info card
    card(d, 30, 100, W-60, 52, fill=C_OK_BG)
    d.text((50, 112),
           "📍 Chennai, Tamil Nadu, India   |   🕐 Retrieved: 2026-11-02 09:08 UTC   |   📂 Open-Meteo (free, no API key)",
           font=_font(17), fill=C_OK_TXT)

    # Forecast table
    headers   = ["Date", "Max °C", "Min °C", "Rain mm", "Condition"]
    col_widths= [160, 110, 110, 115, 380]
    rows = [
        ["2026-11-02", "26.6", "24.9", "29.2", "⛈ Thunderstorm"],
        ["2026-11-03", "30.8", "24.0",  "2.5", "🌦 Moderate drizzle"],
        ["2026-11-04", "30.2", "23.7",  "8.1", "⛈ Thunderstorm"],
        ["2026-11-05", "29.4", "23.8",  "4.4", "🌦 Slight rain showers"],
        ["2026-11-06", "28.5", "24.4", "14.4", "🌦 Moderate drizzle"],
        ["2026-11-07", "28.2", "24.1", "10.2", "🌫 Dense drizzle"],
        ["2026-11-08", "28.7", "23.3",  "9.6", "🌦 Moderate drizzle"],
    ]
    table_rows(d, headers, rows, 30, 162, col_widths)

    # Conditions summary
    card(d, 30, 420, W-60, 120, fill=C_WARN_BG)
    d.text((50, 432), "⚠️  Conditions observed from data:", font=F_BODY_BOLD, fill=C_HEADER)
    conds = [
        "🌧️  Heavy rainfall — 78.4 mm total (check drainage, watch for waterlogging)",
        "⛈️  Heavy rain day: 2026-11-02 (29.2 mm)   |   ⚡  Thunderstorm risk: 2 days",
    ]
    for i, c in enumerate(conds):
        d.text((50, 462 + i*34), c, font=_font(19), fill=C_WARN_TXT)

    narration_bar(d,
        "Every number in this table is real — fetched live from Open-Meteo at 09:08 UTC. "
        "78.4 mm total rainfall. 2 thunderstorm days. The agent identified this from the numbers.",
        y_start=555)
    return img

def slide_checklist():
    """Slide 6 — Preparedness checklist"""
    img, d = new_frame()
    header_bar(d, "✅  Preparedness Checklist", "Generated from actual forecast data — grounded, not invented")

    checklist = [
        ("✅", "Review IMD forecast for your district",     "imd.gov.in (India Meteorological Dept)"),
        ("✅", "Inspect drainage channels before rain day", "29.2 mm forecast on 2 Nov — clear blockages"),
        ("✅", "Monitor soil moisture daily",               "Adjust irrigation based on actual conditions"),
        ("✅", "Harvest mature produce before heavy rain",  "If any crop is ready — prioritise before the storm"),
        ("✅", "Consult a local agronomist",                "For crop-specific decisions — we only provide weather guidance"),
    ]
    for i, (icon, action, reason) in enumerate(checklist):
        y = 110 + i * 90
        card(d, 30, y, W-60, 78, fill=C_OK_BG if i % 2 == 0 else C_CARD)
        d.text((50,  y+10), icon,   font=_font(28), fill=C_ACCENT)
        d.text((100, y+10), action, font=F_BODY_BOLD, fill=C_HEADER)
        d.text((100, y+40), reason, font=F_SMALL, fill=C_TXT)

    narration_bar(d,
        "The checklist is grounded in the actual forecast. Every step is safe and general. "
        "The app does not prescribe pesticides, fertiliser doses, or irrigation volumes.",
        y_start=580)
    return img

def slide_code_tool():
    """Slide 7 — The @tool code"""
    img, d = new_frame()
    header_bar(d, "🔧  The Weather Tool", "Strands @tool — real API call, honest error handling")

    code_lines = [
        ("from strands import tool",                          C_CODE_KW),
        ("import requests, json",                            C_CODE_TXT),
        ("",                                                 C_CODE_TXT),
        ("@tool",                                            C_CODE_STR),
        ("def get_weather_forecast(location: str) -> str:",  C_CODE_KW),
        ('    """Retrieve 7-day forecast. Agent MUST',       C_CODE_CMT),
        ('       include data_source in response."""',       C_CODE_CMT),
        ("    try:",                                         C_CODE_TXT),
        ("        place  = _geocode(location)        # lat/lon", C_CODE_TXT),
        ("        raw    = _fetch_forecast(place)    # 7-day JSON", C_CODE_TXT),
        ("        return json.dumps(_format(raw, place))",   C_CODE_TXT),
        ("    except ValueError as exc:              # not found", C_CODE_CMT),
        ('        return json.dumps({"error": str(exc)})',   C_CODE_TXT),
        ("    except ConnectionError as exc:         # API down", C_CODE_CMT),
        ('        return json.dumps({"error": str(exc)})',   C_CODE_TXT),
    ]
    code_block(d, code_lines, 30, 100, W//2 - 40)

    # Call-outs on the right
    callouts = [
        (C_ACCENT,   "@tool",         "Single decorator exposes the function to the Strands agent"),
        (C_ACCENT,   "Returns JSON",  "String — not dict. Agent sees it directly in context window"),
        (C_ACCENT,   "3 error paths", "ValueError (bad loc), ConnectionError (API down), generic"),
        (C_HEADER,   "No exception",  "Every failure returns structured JSON — agent explains to farmer"),
        (C_ACCENT,   "Docstring",     "Instruction in docstring: agent MUST cite the data source"),
    ]
    cy = 110
    for col, label, desc in callouts:
        card(d, W//2 + 20, cy, W//2 - 50, 72, fill=C_CARD)
        d.rounded_rectangle([W//2+20, cy, W//2+8+len(label)*12, cy+28], radius=4, fill=col)
        d.text((W//2+28, cy+6), label, font=_font(15, bold=True), fill=C_HEADER_TXT)
        multiline(d, desc, W//2+28, cy+34, _font(16), C_TXT, max_width=W//2-80)
        cy += 88

    narration_bar(d,
        "The @tool decorator from Strands is the only thing needed. No routing table, "
        "no JSON schema. Every failure path returns JSON — the agent never crashes silently.",
        y_start=615)
    return img

def slide_code_agent():
    """Slide 8 — The agent assembly"""
    img, d = new_frame()
    header_bar(d, "🤖  The Strands Agent", "Three lines of code — tool routing handled by Strands")

    code_lines = [
        ("from strands import Agent",                        C_CODE_KW),
        ("from strands.models import BedrockModel",         C_CODE_KW),
        ("",                                                C_CODE_TXT),
        ("agent = Agent(",                                  C_CODE_TXT),
        ("    model=BedrockModel(",                         C_CODE_TXT),
        ('        model_id="us.amazon.nova-lite-v1:0",',   C_CODE_STR),
        ('        region_name="us-east-1"',                C_CODE_STR),
        ("    ),",                                          C_CODE_TXT),
        ("    system_prompt=CLIMATE_SYSTEM_PROMPT,",        C_CODE_TXT),
        ("    tools=[get_weather_forecast],",               C_CODE_TXT),
        (")",                                               C_CODE_TXT),
        ("",                                               C_CODE_TXT),
        ("result = agent(farmer_message)",                  C_CODE_KW),
        ("# → Strands calls the tool automatically",        C_CODE_CMT),
        ("# → Returns interpreted markdown response",       C_CODE_CMT),
    ]
    code_block(d, code_lines, 30, 100, W//2 - 20)

    # What Strands handles for you
    card(d, W//2 + 20, 100, W//2 - 50, 380, fill=C_CARD)
    d.text((W//2+40, 115), "What Strands handles for you:", font=F_BODY_BOLD, fill=C_HEADER)
    handled = [
        "✅  Tool-call JSON parsing",
        "✅  Deciding when to call the tool",
        "✅  Passing tool result back to model",
        "✅  Multi-turn conversation management",
        "✅  Error propagation from tools",
    ]
    for i, h in enumerate(handled):
        d.text((W//2+40, 155 + i*50), h, font=F_BODY, fill=C_OK_TXT)

    card(d, W//2+20, 490, W//2-50, 80, fill=C_WARN_BG)
    d.text((W//2+40, 500),
           "Amazon Nova Lite — no Marketplace",
           font=_font(18, bold=True), fill=C_WARN_TXT)
    d.text((W//2+40, 528),
           "subscription required. Enable in Bedrock console.",
           font=_font(17), fill=C_WARN_TXT)

    narration_bar(d,
        "The Strands agent is three lines. I did not write tool routing, parse JSON, "
        "or manage turns. Strands decides when to call the weather tool and what to do with the result.",
        y_start=615)
    return img

def slide_system_prompt():
    """Slide 9 — System prompt as guardrail"""
    img, d = new_frame()
    header_bar(d, "🛡️  System Prompt as Guardrail", "The most important file in the project")

    must_do = [
        "Call the weather tool BEFORE making any claim",
        "Base EVERY response on tool data only",
        "Include the data source in every response",
        "Say clearly if the tool returned an error",
    ]
    must_not = [
        "Invent forecast values or risk levels",
        "Prescribe pesticide / fertiliser / irrigation amounts",
        "State inference as confirmed fact",
        "Fill a gap silently if the tool fails",
    ]

    card(d, 30, 100, 590, 400, fill=C_OK_BG)
    d.text((50, 112), "Agent MUST ✅", font=F_BODY_BOLD, fill=C_HEADER)
    for i, rule in enumerate(must_do):
        d.text((50, 148 + i * 60), f"• {rule}", font=_font(20), fill=C_OK_TXT)

    card(d, 650, 100, 600, 400, fill=(255,235,235))
    d.text((670, 112), "Agent MUST NOT ❌", font=F_BODY_BOLD, fill=(150,0,0))
    for i, rule in enumerate(must_not):
        d.text((670, 148 + i * 60), f"• {rule}", font=_font(20), fill=(180,30,30))

    card(d, 30, 515, W-60, 72, fill=C_WARN_BG)
    d.text((50, 527),
           "💡  Why this matters: an LLM trained on agricultural text can generate a plausible forecast",
           font=_font(19), fill=C_WARN_TXT)
    d.text((50, 552),
           "    from memory — confident, authoritative, and completely wrong for this location this week.",
           font=_font(19), fill=C_WARN_TXT)

    narration_bar(d,
        "The system prompt is the real guardrail. "
        "It took longer to write than all the code. That is the right balance for responsible AI.",
        y_start=602)
    return img

def slide_tests():
    """Slide 10 — Test results"""
    img, d = new_frame()
    header_bar(d, "🧪  Test Results", "8 unit tests — all mocked, all pass, no AWS needed")

    # Test result rows
    tests = [
        ("PASSED", "test_valid_location_geocoding",           "Chennai → lat 13.08, lon 80.27"),
        ("PASSED", "test_invalid_location_raises_value_error","Bad loc → helpful ValueError, not crash"),
        ("PASSED", "test_successful_weather_retrieval",       "@tool returns 7 days, all fields correct"),
        ("PASSED", "test_weather_api_network_failure",        "Network error → error JSON, no exception"),
        ("PASSED", "test_missing_weather_data_fields",        "Missing fields → None/'Unknown', no KeyError"),
        ("PASSED", "test_heat_related_forecast_detected",     "40°C forecast → represented correctly"),
        ("PASSED", "test_rainfall_related_forecast_detected", "WMO 65→Heavy rain, 82→Violent showers"),
        ("PASSED", "test_wmo_codes_map_contains_common_codes","0,1,63,65,80,95 all in map"),
    ]
    for i, (status, name, desc) in enumerate(tests):
        y = 105 + i * 57
        bg = C_OK_BG if i % 2 == 0 else C_CARD
        card(d, 30, y, W-60, 50, fill=bg)
        d.rounded_rectangle([38, y+8, 118, y+42], radius=4, fill=(6,95,70))
        d.text((48, y+14), status, font=_font(14, bold=True), fill=C_HEADER_TXT)
        d.text((130, y+8),  name, font=_font(15, bold=True), fill=C_HEADER)
        d.text((130, y+28), desc, font=_font(14), fill=C_TXT)

    # Summary bar
    d.rectangle([30, 568, W-30, 608], fill=C_HEADER, outline=C_ACCENT)
    d.text((50, 577),
           "✅  8 passed, 3 warnings in 1.11s   |   Mocked HTTP — no internet or AWS needed",
           font=_font(20, bold=True), fill=C_HEADER_TXT)

    narration_bar(d,
        "All 8 tests use mocked API responses — no internet or AWS account needed. "
        "They verify the tool's behaviour, not agricultural correctness.",
        y_start=622)
    return img

def slide_architecture():
    """Slide 11 — Architecture"""
    img, d = new_frame()
    header_bar(d, "🏗️  Architecture", "Full data flow — from farmer input to response")

    boxes = [
        (500, 105, 280, 55, "Farmer's Browser", C_BG, C_ACCENT),
        (500, 205, 280, 55, "Streamlit UI (app.py)", C_CARD, C_HEADER),
        (500, 305, 280, 55, "Strands Agent (agent.py)", C_HEADER, C_HEADER),
        (180, 420, 280, 55, "weather_tool.py (@tool)", C_CARD, C_ACCENT),
        (820, 420, 280, 55, "Amazon Bedrock", C_CARD, C_HEADER),
        (30,  530, 220, 55, "Open-Meteo Geocoding", C_BG, C_ACCENT),
        (280, 530, 220, 55, "Open-Meteo Forecast", C_BG, C_ACCENT),
    ]
    for bx, by, bw, bh, label, fill, border in boxes:
        card(d, bx, by, bw, bh, fill=fill, border=border)
        cx = bx + bw // 2
        # Estimate text width
        tw = len(label) * 10
        d.text((cx - tw//2, by + 16), label,
               font=_font(17, bold=True),
               fill=C_HEADER_TXT if fill == C_HEADER else C_TXT)

    # Arrows
    arrows = [
        (640, 160, 640, 205),
        (640, 260, 640, 305),
        (540, 360, 320, 420),
        (740, 360, 960, 420),
        (210, 475, 140, 530),
        (320, 475, 390, 530),
    ]
    for x1, y1, x2, y2 in arrows:
        d.line([x1, y1, x2, y2], fill=C_ACCENT, width=3)
        # Arrowhead
        dx, dy = x2 - x1, y2 - y1
        length = (dx**2 + dy**2) ** 0.5
        if length > 0:
            ux, uy = dx/length, dy/length
            d.polygon([
                (x2, y2),
                (x2 - ux*12 - uy*6, y2 - uy*12 + ux*6),
                (x2 - ux*12 + uy*6, y2 - uy*12 - ux*6),
            ], fill=C_ACCENT)

    # Callout
    card(d, 30, 105, 420, 180, fill=C_OK_BG)
    d.text((50, 118), "No database", font=F_BODY_BOLD, fill=C_HEADER)
    d.text((50, 148), "No paid APIs", font=F_BODY_BOLD, fill=C_HEADER)
    d.text((50, 178), "Open-Meteo is completely free", font=F_BODY_BOLD, fill=C_HEADER)
    d.text((50, 220), "All weather data fetched live", font=_font(18), fill=C_TXT)
    d.text((50, 248), "on every request", font=_font(18), fill=C_TXT)

    narration_bar(d,
        "Streamlit → Strands Agent → weather tool → Open-Meteo → Amazon Bedrock. "
        "No database. No paid APIs. Open-Meteo is completely free.",
        y_start=605)
    return img

def slide_demo_mode():
    """Slide 12 — Demo mode"""
    img, d = new_frame()
    header_bar(d, "🔬  Demo Mode", "Full app — works without AWS account")

    card(d, 30, 110, W//2 - 40, 400)
    d.text((50, 125), "Demo Mode (no AWS)", font=F_BODY_BOLD, fill=C_HEADER)
    demo_items = [
        "✅  Weather data: REAL (Open-Meteo API)",
        "✅  Geocoding: REAL (live coordinates)",
        "✅  7-day forecast: REAL (live numbers)",
        "🔧  Interpretation: rule-based logic",
        "🔧  No Bedrock / no LLM needed",
        "📍  Activates automatically if no AWS",
    ]
    for i, item in enumerate(demo_items):
        d.text((50, 165 + i * 55), item, font=_font(20), fill=C_TXT)

    card(d, W//2 + 20, 110, W//2 - 50, 400, fill=C_OK_BG)
    d.text((W//2+40, 125), "Bedrock Mode (with AWS)", font=F_BODY_BOLD, fill=C_HEADER)
    bedrock_items = [
        "✅  Weather data: REAL (Open-Meteo API)",
        "✅  Geocoding: REAL (live coordinates)",
        "✅  7-day forecast: REAL (live numbers)",
        "🤖  Interpretation: Strands + Bedrock",
        "🤖  Amazon Nova Lite (us-east-1)",
        "🔄  Auto-activates with aws configure",
    ]
    for i, item in enumerate(bedrock_items):
        d.text((W//2+40, 165 + i * 55), item, font=_font(20), fill=C_OK_TXT)

    card(d, 30, 520, W-60, 72, fill=C_WARN_BG)
    d.text((50, 532),
           "💡  The switch is automatic — no code changes needed. Run `aws configure` and Bedrock mode activates.",
           font=_font(19), fill=C_WARN_TXT)
    d.text((50, 557),
           "     Demo mode: zero-barrier proof that real weather data flows through the entire pipeline.",
           font=_font(19), fill=C_WARN_TXT)

    narration_bar(d,
        "Anyone can clone this repo and see it working with real weather data in 5 minutes — "
        "no AWS account needed. Add credentials later and the full Strands agent activates automatically.",
        y_start=607)
    return img

def slide_verification():
    """Slide 13 — Verification results"""
    img, d = new_frame()
    header_bar(d, "🔎  Full Verification — 13/13 Passed", "Every non-AWS component verified before launch")

    checks = [
        ("✓", "Python 3.13",                     "3.10–3.13 required"),
        ("✓", "streamlit 1.40.2",               "Web UI framework"),
        ("✓", "strands-agents 0.1.6",           "Agent SDK"),
        ("✓", "requests 2.32.3",                "HTTP client for APIs"),
        ("✓", "tools.weather_tool imports",      "Module loads cleanly"),
        ("✓", "prompts.climate_prompt imports",  "System prompt loads"),
        ("✓", "Open-Meteo geocoding (live)",     "Chennai → 13.08°N, 80.27°E"),
        ("✓", "Open-Meteo forecast (live)",      "3 days returned (2026-11-02)"),
        ("✓", "@tool end-to-end (live)",         "Madurai — 7 days real data"),
        ("✓", "8 pytest unit tests",             "8/8 passed in 1.11s"),
        ("✓", "Demo agent smoke test",           "Full response generated"),
        ("✓", "Streamlit starts on :8501",       "200 GET confirmed"),
        ("✓", "app.py imports cleanly",          "No missing dependencies"),
    ]
    col1 = checks[:7]
    col2 = checks[7:]
    for i, (icon, label, detail) in enumerate(col1):
        y = 106 + i * 58
        d.rounded_rectangle([30, y, 64, y+34], radius=4, fill=(6,95,70))
        d.text((38, y+8), icon, font=_font(16, bold=True), fill=C_HEADER_TXT)
        d.text((74, y+4),  label,  font=_font(16, bold=True), fill=C_HEADER)
        d.text((74, y+24), detail, font=_font(14), fill=C_TXT)
    for i, (icon, label, detail) in enumerate(col2):
        y = 106 + i * 58
        d.rounded_rectangle([W//2+20, y, W//2+54, y+34], radius=4, fill=(6,95,70))
        d.text((W//2+28, y+8), icon, font=_font(16, bold=True), fill=C_HEADER_TXT)
        d.text((W//2+64, y+4),  label,  font=_font(16, bold=True), fill=C_HEADER)
        d.text((W//2+64, y+24), detail, font=_font(14), fill=C_TXT)

    d.rectangle([30, 518, W-30, 558], fill=C_HEADER, outline=C_ACCENT)
    d.text((50, 527),
           "RESULT: ALL NON-AWS CHECKS PASSED  ✓  13 passed   ✗ 0 failed",
           font=_font(20, bold=True), fill=C_HEADER_TXT)

    narration_bar(d,
        "13 checks — Python, all packages, live geocoding, live forecast, the @tool end-to-end, "
        "8 unit tests, smoke test, Streamlit. All pass.",
        y_start=578)
    return img

def slide_next_steps():
    """Slide 14 — What's next"""
    img, d = new_frame()
    header_bar(d, "🚀  What I'd Build Next", "Extending Vivasayi beyond the hackathon")

    next_items = [
        ("🌐", "Tamil & Telugu output",
         "Amazon Translate @tool — same pattern as the weather tool"),
        ("📱", "SMS via Amazon SNS",
         "Daily 3-day forecast + checklist to feature phones (no smartphone needed)"),
        ("🔴", "Strands Evals red-team",
         "AdversarialCaseGenerator — measure how many prompt attacks the guardrail holds"),
        ("📈", "NASA POWER historical baseline",
         "Compare this week vs 30-year average — is this rainfall unusual for November?"),
        ("🛡️", "Bedrock Guardrail",
         "API-level guardrail independent of the system prompt — defense in depth"),
    ]
    for i, (icon, title, desc) in enumerate(next_items):
        y = 108 + i * 92
        card(d, 30, y, W-60, 78, fill=C_OK_BG if i%2==0 else C_CARD)
        d.text((50, y+12),  icon,  font=_font(32), fill=C_ACCENT)
        d.text((100, y+10), title, font=F_BODY_BOLD, fill=C_HEADER)
        d.text((100, y+40), desc,  font=_font(19), fill=C_TXT)

    narration_bar(d,
        "Five concrete next steps — Tamil output, SMS delivery, Evals red-team, "
        "historical baseline, and a Bedrock Guardrail for production safety.",
        y_start=580)
    return img

def slide_closing():
    """Slide 15 — Closing"""
    img, d = new_frame()
    d.rectangle([0, 0, W, H], fill=C_HEADER)
    d.rectangle([40, 40, W-40, H-40], fill=C_BG, outline=C_ACCENT, width=3)

    d.text((80, 90),  "🌱", font=_font(70), fill=C_ACCENT)
    d.text((80, 175), "Vivasayi Climate Guide", font=_font(50, bold=True), fill=C_HEADER)
    d.text((80, 250), "Real weather data. Grounded AI. Honest guidance.",
           font=_font(28), fill=C_TXT)

    lessons = [
        "🔧  The @tool decorator — one import, one line",
        "🤖  The Agent — three lines of setup",
        "🛡️  The system prompt — more thought than all the code",
        "✅  8/8 tests passing   |   13/13 checks passing",
        "🌐  Open-Meteo — free, live, global, no API key",
    ]
    for i, lesson in enumerate(lessons):
        d.text((80, 310 + i*58), lesson, font=_font(24), fill=C_TXT)

    d.text((80, 625),
           "github.com/YOUR_USERNAME/vivasayi-climate-guide",
           font=_font(20), fill=C_ACCENT)

    narration_bar(d,
        "The Strands Agents SDK made the plumbing simple — so the hard work went where it belongs: "
        "the rules. The farmer gets honest, data-backed guidance. Thank you.",
        y_start=670)
    return img


# ══════════════════════════════════════════════════════════════════════════════
# COMPOSE THE VIDEO
# ══════════════════════════════════════════════════════════════════════════════

# (slide_function, duration_in_seconds)
SLIDES = [
    (slide_title,         6),
    (slide_problem,       8),
    (slide_solution,      7),
    (slide_app_ui,        9),
    (slide_forecast_output, 10),
    (slide_checklist,     9),
    (slide_code_tool,     10),
    (slide_code_agent,    9),
    (slide_system_prompt, 9),
    (slide_tests,         9),
    (slide_architecture,  9),
    (slide_demo_mode,     9),
    (slide_verification,  8),
    (slide_next_steps,    8),
    (slide_closing,       7),
]

TOTAL = sum(d for _, d in SLIDES)

def build_video():
    try:
        from moviepy.editor import ImageClip, concatenate_videoclips
    except ImportError:
        print("moviepy not installed. Run: pip install moviepy==1.0.3")
        sys.exit(1)

    print(f"\nBuilding video — {len(SLIDES)} slides, {TOTAL}s total")
    print(f"Output: {OUT.resolve()}\n")

    clips = []
    elapsed = 0
    for i, (fn, dur) in enumerate(SLIDES):
        print(f"  [{i+1:02d}/{len(SLIDES)}]  {fn.__name__:<30}  {dur}s  ", end="", flush=True)
        frame = fn()
        # Save frame temporarily
        tmp = Path(f"results/_frame_{i:02d}.png")
        frame.save(tmp)
        clip = ImageClip(str(tmp)).set_duration(dur)
        # Fade in/out
        if i > 0:
            clip = clip.crossfadein(0.4)
        clips.append(clip)
        elapsed += dur
        print(f"✓  (total {elapsed}s)")

    print("\nConcatenating clips...")
    final = concatenate_videoclips(clips, method="compose")

    print(f"Writing {OUT} ...")
    final.write_videofile(
        str(OUT),
        fps=FPS,
        codec="libx264",
        audio=False,
        logger=None,
    )

    # Clean up temp frames
    for i in range(len(SLIDES)):
        tmp = Path(f"results/_frame_{i:02d}.png")
        if tmp.exists():
            tmp.unlink()

    print(f"\n✅  VIDEO COMPLETE")
    print(f"   File   : {OUT.resolve()}")
    size_mb = OUT.stat().st_size / (1024*1024)
    print(f"   Size   : {size_mb:.1f} MB")
    print(f"   Length : ~{TOTAL}s ({TOTAL//60}m {TOTAL%60}s)")
    print(f"   Format : MP4 (H.264, {W}×{H}, {FPS}fps, no audio)")
    print(f"\n   Open   : start {OUT.resolve()}")


def build_frames_only():
    """Fallback: save individual PNG frames if moviepy is unavailable."""
    frames_dir = Path("results/frames")
    frames_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nSaving {len(SLIDES)} PNG frames to {frames_dir.resolve()}")
    for i, (fn, dur) in enumerate(SLIDES):
        print(f"  [{i+1:02d}/{len(SLIDES)}]  {fn.__name__}  ({dur}s) ... ", end="", flush=True)
        frame = fn()
        out_path = frames_dir / f"slide_{i+1:02d}_{fn.__name__}.png"
        frame.save(out_path)
        print("✓")
    print(f"\n✅  {len(SLIDES)} frames saved to: {frames_dir.resolve()}")
    print("   Import into any video editor (DaVinci Resolve, Premiere, iMovie) or")
    print("   use these slides for a narrated screen recording.")


if __name__ == "__main__":
    try:
        import moviepy
        build_video()
    except ImportError:
        print("moviepy not found — saving PNG frames instead.")
        build_frames_only()
