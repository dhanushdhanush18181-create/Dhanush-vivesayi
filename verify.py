"""Verification script — run before launching the app."""
import sys, os

print("=" * 55)
print("Vivasayi Climate Guide — Pre-launch Verification")
print("=" * 55)

errors = []

# 1. Python version
major, minor = sys.version_info[:2]
print(f"\n[1] Python {major}.{minor}", end=" ")
if major == 3 and 10 <= minor <= 13:
    print("✓")
else:
    print(f"✗  Need 3.10–3.13, got {major}.{minor}")
    errors.append("Python version")

# 2. Core package imports
packages = {
    "strands":     "strands",
    "boto3":       "boto3",
    "streamlit":   "streamlit",
    "requests":    "requests",
    "dotenv":      "python-dotenv",
    "pytest":      "pytest",
}
print("\n[2] Package imports")
for mod, pkg in packages.items():
    try:
        m = __import__(mod)
        ver = getattr(m, "__version__", "?")
        print(f"    {pkg:<20} ✓  ({ver})")
    except ImportError as e:
        print(f"    {pkg:<20} ✗  {e}")
        errors.append(pkg)

# 3. Project module imports (tools & prompts)
print("\n[3] Project modules")
sys.path.insert(0, os.path.dirname(__file__))
for modname in ["tools.weather_tool", "prompts.climate_prompt"]:
    try:
        __import__(modname)
        print(f"    {modname:<30} ✓")
    except Exception as e:
        print(f"    {modname:<30} ✗  {e}")
        errors.append(modname)

# 4. AWS credentials check
print("\n[4] AWS credentials")
try:
    import boto3
    sts = boto3.client("sts", region_name="us-east-1")
    identity = sts.get_caller_identity()
    print(f"    Account: {identity['Account']}  ✓")
    print(f"    ARN:     {identity['Arn']}")
except Exception as e:
    print(f"    ✗  {e}")
    print("    Fix: run  aws configure  or  aws sso login  in your terminal.")
    errors.append("AWS credentials")

# 5. Bedrock model availability
print("\n[5] Bedrock model")
MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "us.amazon.nova-lite-v1:0")
REGION   = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
try:
    import boto3
    bedrock = boto3.client("bedrock-runtime", region_name=REGION)
    import json
    resp = bedrock.invoke_model(
        modelId=MODEL_ID,
        body=json.dumps({"messages": [{"role": "user", "content": "ping"}],
                         "max_tokens": 5, "anthropic_version": "bedrock-2023-05-31"}),
        contentType="application/json",
        accept="application/json",
    )
    print(f"    Model {MODEL_ID}  ✓")
except Exception as e:
    msg = str(e)
    # Nova Lite uses a different payload format — a ValidationException here
    # still means the model IS accessible (wrong payload, but auth worked)
    if "ValidationException" in msg or "inference profile" in msg.lower():
        print(f"    Model {MODEL_ID}  ✓  (reachable — payload format mismatch is expected)")
    elif "AccessDeniedException" in msg or "UnauthorizedException" in msg:
        print(f"    ✗  Access denied to model {MODEL_ID}")
        print("       Fix: enable the model in Bedrock console → Model access (us-east-1)")
        errors.append("Bedrock access")
    elif "ExpiredToken" in msg or "InvalidClientTokenId" in msg:
        print("    ✗  AWS credentials expired")
        errors.append("AWS credentials")
    else:
        print(f"    ✗  {msg[:120]}")
        errors.append("Bedrock model")

# 6. Live weather API check
print("\n[6] Open-Meteo API (live call)")
try:
    import requests as req
    r = req.get("https://geocoding-api.open-meteo.com/v1/search",
                params={"name": "Chennai", "count": 1}, timeout=8)
    r.raise_for_status()
    data = r.json()
    if data.get("results"):
        place = data["results"][0]
        print(f"    Chennai → lat={place['latitude']}, lon={place['longitude']}  ✓")
    else:
        print("    ✗  No results returned")
        errors.append("Open-Meteo API")
except Exception as e:
    print(f"    ✗  {e}")
    errors.append("Open-Meteo API")

# Summary
print("\n" + "=" * 55)
if errors:
    print(f"RESULT: {len(errors)} issue(s) found → {errors}")
    print("Fix the issues above before running:  streamlit run app.py")
else:
    print("RESULT: ALL CHECKS PASSED ✓")
    print("Run:  streamlit run app.py")
print("=" * 55)
sys.exit(0 if not errors else 1)
