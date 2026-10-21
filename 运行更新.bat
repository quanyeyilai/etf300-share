@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo  ETF 300 share fetcher  /  沪深300ETF份额抓取
echo ============================================
python update.py
if errorlevel 1 (
  echo.
  echo [ERROR] run failed. Make sure Python is installed and in PATH.
) else (
  echo.
  echo [OK] data updated. Open docs\index.html to view charts.
  python build_single.py
)
echo.
pause
