@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 正在抓取最新板块估值...
python sector.py
echo 正在推送到微信...
python notify.py
echo.
echo 完成。按任意键关闭。
pause >nul
