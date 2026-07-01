@echo off
cd /d "%~dp0"
echo =====================================
echo Construire SMART-RECRUT app.exe local
echo =====================================
python --version >nul 2>&1
if errorlevel 1 (
  echo Nu gasesc Python. Instaleaza Python 3.10+ si bifeaza Add Python to PATH.
  pause
  exit /b 1
)
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller
python -m PyInstaller --noconfirm --clean --onedir --name app --add-data "logo.png;." app_desktop.py

echo.
echo Gata. Exe-ul este aici:
echo %cd%\dist\app\app.exe
echo.
pause
