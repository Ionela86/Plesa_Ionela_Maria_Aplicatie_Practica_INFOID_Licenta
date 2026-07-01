@echo off
cd /d %~dp0
python -m pip install -r requirements.txt pyinstaller
python -m spacy download en_core_web_sm
pyinstaller --clean app.spec
pause
