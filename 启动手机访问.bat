@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Starting LAN server, keep this window open...
echo If the phone cannot open the URL, allow Python in Windows Firewall.
echo.
python serve.py 8000
pause
