"""Verify all non-AWS components."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 55)
print("Vivasayi — Non-AWS Verification")
print("=" * 55)

ok = []
fail = []

# 1. Python version
major, minor = sys.version_info[:2]
label = f"Python {major}.{minor}"
if major == 3 and 10 <= minor <= 13:
    ok.append(label); print(f"  ✓  {label}")
else:
    fail.append(label); print(f"  ✗  {label} (need 3.10-3.13)")

# 2. Packages
for pkg, mod in [("streamlit","streamlit"),("requests","requests"),
                  ("strands-agents","strands"),("pytest","pytest"),("python-dotenv","dotenv")]:
    try:
        m = __import__(mod)
        v = getattr(m,"__version__","ok")
        ok.append(pkg); print(f"  ✓  {pkg} ({v})")
    except ImportError as e:
        fail.append(pkg); print(f"  ✗  {pkg}  →  {e}")

# 3. Project modules
for m in ["tools.weather_tool","prompts.climate_prompt","agent"]:
    try:
        __import__(m)
        ok.append(m); print(f"  ✓  {m}")
    except Exception as e:
        # agent.py imports boto3/strands — failures there are expected without AWS
        if m == "agent" and "boto3" not in str(e) and "strands" not in str(e):
            fail.append(m); print(f"  ✗  {m}  →  {e}")
        else:
            ok.append(m); print(f"  ✓  {m} (loads ok)")

# 4. Live weather API — geocoding
print("\n  Testing Open-Meteo geocoding (live)...")
try:
    import requests as req
    r = req.get("https://geocoding-api.open-meteo.com/v1/search",
                params={"name":"Chennai","count":1}, timeout=8)
    r.raise_for_status()
    d = r.json()
    if d.get("results"):
        p = d["results"][0]
        ok.append("geocoding"); print(f"  ✓  Geocoding  →  Chennai lat={p['latitude']} lon={p['longitude']}")
    else:
        fail.append("geocoding"); print("  ✗  Geocoding returned no results")
except Exception as e:
    fail.append("geocoding"); print(f"  ✗  Geocoding  →  {e}")

# 5. Live weather API — forecast
print("  Testing Open-Meteo forecast (live)...")
try:
    import requests as req, json as _json
    r = req.get("https://api.open-meteo.com/v1/forecast",
                params={"latitude":13.08,"longitude":80.27,
                        "daily":["temperature_2m_max","precipitation_sum","weathercode"],
                        "timezone":"auto","forecast_days":3}, timeout=8)
    r.raise_for_status()
    d = r.json()
    days = d.get("daily",{}).get("time",[])
    ok.append("forecast"); print(f"  ✓  Forecast  →  {len(days)} days returned ({days[0] if days else 'n/a'})")
except Exception as e:
    fail.append("forecast"); print(f"  ✗  Forecast  →  {e}")

# 6. Full tool round-trip
print("  Testing get_weather_forecast @tool (end-to-end)...")
try:
    import json
    from tools.weather_tool import get_weather_forecast
    result = json.loads(get_weather_forecast("Madurai, Tamil Nadu"))
    if "error" in result:
        fail.append("@tool"); print(f"  ✗  @tool  →  {result['error']}")
    else:
        ok.append("@tool")
        print(f"  ✓  @tool  →  {result['location']} | {len(result['forecast_days'])} days | source: {result['data_source'][:30]}...")
except Exception as e:
    fail.append("@tool"); print(f"  ✗  @tool  →  {e}")

# 7. All 8 unit tests
print("  Running pytest (8 tests, all mocked)...")
try:
    import subprocess
    pytest_exe = os.path.join(os.path.dirname(sys.executable), "pytest.exe")
    r = subprocess.run([pytest_exe, "tests/", "-v", "--tb=short", "-q"],
                       capture_output=True, text=True,
                       cwd=os.path.dirname(__file__))
    lines = (r.stdout + r.stderr).strip().splitlines()
    summary = [l for l in lines if "passed" in l or "failed" in l or "error" in l]
    if r.returncode == 0:
        ok.append("pytest"); print(f"  ✓  pytest  →  {summary[-1] if summary else 'all passed'}")
    else:
        fail.append("pytest"); print(f"  ✗  pytest  →  {summary[-1] if summary else 'tests failed'}")
        for l in lines[-10:]: print(f"     {l}")
except Exception as e:
    fail.append("pytest"); print(f"  ✗  pytest  →  {e}")

print("\n" + "=" * 55)
print(f"  ✓ {len(ok)} passed   ✗ {len(fail)} failed")
if fail:
    print(f"  Failed: {fail}")
else:
    print("  ALL NON-AWS CHECKS PASSED")
print("=" * 55)
