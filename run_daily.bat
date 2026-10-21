@echo off
cd /d "%~dp0"
if not exist data mkdir data
echo ===== %date% %time% ===== >> data\daily.log
python update.py >> data\daily.log 2>&1
echo. >> data\daily.log
