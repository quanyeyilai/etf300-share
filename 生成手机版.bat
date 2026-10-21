@echo off
chcp 65001 >nul
cd /d "%~dp0"
python build_single.py
if errorlevel 1 (
  echo [ERROR] failed.
) else (
  echo.
  echo Send 沪深300ETF份额看板.html to your phone and open it in a browser.
)
echo.
pause
