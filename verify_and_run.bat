@echo off
setlocal
set PROJECT=c:\Users\Dhanu\OneDrive\Documents\Desktop\Dhanush\vivasayi-climate-guide
set PYTHON=%PROJECT%\.venv\Scripts\python.exe
set STREAMLIT=%PROJECT%\.venv\Scripts\streamlit.exe

echo.
echo ============================================================
echo   STEP 1 — Non-AWS Verification
echo ============================================================
%PYTHON% %PROJECT%\verify_noaws.py
if errorlevel 1 (
    echo.
    echo VERIFICATION FAILED. Fix the errors above before running.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   STEP 2 — Smoke Test (demo agent + live weather)
echo ============================================================
set DEMO_MODE=true
%PYTHON% %PROJECT%\smoke_test.py
if errorlevel 1 (
    echo.
    echo SMOKE TEST FAILED.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   STEP 3 — Launching Streamlit on http://localhost:8501
echo ============================================================

if not exist "%USERPROFILE%\.streamlit" mkdir "%USERPROFILE%\.streamlit"
echo [general]          > "%USERPROFILE%\.streamlit\credentials.toml"
echo email = ""        >> "%USERPROFILE%\.streamlit\credentials.toml"

set STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
echo.
echo   App URL  :  http://localhost:8501
echo   Stop     :  Press Ctrl+C in this window
echo.

%STREAMLIT% run %PROJECT%\app.py --server.port 8501
