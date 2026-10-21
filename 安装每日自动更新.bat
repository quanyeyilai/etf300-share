@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "T1=ETF300ShareEvening"
set "T2=ETF300ShareMorning"

for /f "delims=" %%i in ('where python 2^>nul') do (
  if not defined PY set "PY=%%i"
)
if not defined PY (
  echo [ERROR] python not found in PATH.
  pause
  exit /b 1
)

schtasks /create /tn "%T1%" /tr "\"%~dp0run_daily.bat\"" /sc daily /st 19:00 /f
schtasks /create /tn "%T2%" /tr "\"%~dp0run_daily.bat\"" /sc daily /st 08:30 /f

if errorlevel 1 (
  echo [ERROR] failed to create scheduled task. Try run as Administrator.
) else (
  echo [OK] Two scheduled tasks created:
  echo      %T1%  - daily 19:00  (T day preliminary)
  echo      %T2%  - daily 08:30  (T-1 day final)
  echo      Log: %~dp0data\daily.log
)
echo.
pause
