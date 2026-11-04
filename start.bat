@echo off
cd /d "c:\Users\Dhanu\OneDrive\Documents\Desktop\Dhanush\vivasayi-climate-guide"

REM Suppress Streamlit email prompt
set STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
set STREAMLIT_SERVER_HEADLESS=false

REM Write credentials inline to bypass interactive prompt
if not exist "%USERPROFILE%\.streamlit" mkdir "%USERPROFILE%\.streamlit"
echo [general] > "%USERPROFILE%\.streamlit\credentials.toml"
echo email = "" >> "%USERPROFILE%\.streamlit\credentials.toml"

echo Starting Vivasayi Climate Guide...
echo Open your browser at: http://localhost:8501
echo Press Ctrl+C to stop.
echo.

.venv\Scripts\streamlit.exe run app.py --server.port 8501
