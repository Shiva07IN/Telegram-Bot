@echo off
echo Starting Telegram Affidavit Bot...
call venv\Scripts\activate.bat
pip install -r requirements.txt
python Bot_enhanced.py

pause
