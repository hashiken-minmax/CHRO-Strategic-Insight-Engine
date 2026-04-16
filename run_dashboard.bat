@echo off
REM ダッシュボード起動スクリプト (Windows)

cd /d "%~dp0"
echo Starting CHRO-SIE Dashboard...
echo Open your browser to: http://localhost:8501
echo.

streamlit run dashboard.py
pause
