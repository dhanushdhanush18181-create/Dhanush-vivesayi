"""Quick smoke test — runs demo agent against a real location."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
os.environ["DEMO_MODE"] = "true"   # force demo mode

from agent import run_climate_agent

print("Running demo agent for Chennai / rice ...\n")
result = run_climate_agent("Chennai, Tamil Nadu", "rice", "Will it be too hot this week?")

if result["success"]:
    print(f"MODE   : {result['mode']}")
    print(f"STATUS : SUCCESS")
    print("-" * 60)
    # Print first 1200 chars of response
    print(result["response"][:1200])
    print("..." if len(result["response"]) > 1200 else "")
    print("-" * 60)
    print("SMOKE TEST PASSED")
else:
    print(f"ERROR  : {result['error']}")
    print("SMOKE TEST FAILED")
    sys.exit(1)
