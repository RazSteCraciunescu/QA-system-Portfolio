@echo off
setlocal
cd /d "%~dp0\..\.."
python -m venv .venv
if errorlevel 1 exit /b 1
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
if errorlevel 1 exit /b 1
python -m pip install -r requirements-dev.txt
if errorlevel 1 exit /b 1
python -m playwright install chromium
if errorlevel 1 exit /b 1
echo.
echo Setup complete. Activate with: .venv\Scripts\activate.bat
