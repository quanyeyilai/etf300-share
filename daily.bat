@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ===== 开始 %date% %time% =====
python update.py
python sector.py
python notify.py
python build_single.py
git add -A
git commit -m "chore: 每日自动更新"
git push origin main
echo ===== 完成 %date% %time% =====
