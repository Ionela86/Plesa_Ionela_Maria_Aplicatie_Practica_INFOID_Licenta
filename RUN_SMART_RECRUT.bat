@echo off
cd /d %~dp0
python -m pip install -r requirements.txt
python -m spacy download en_core_web_sm
python app.py
pause
