@echo off
setlocal
cd /d "%~dp0\..\.."
call .venv\Scripts\activate.bat
if errorlevel 1 exit /b 1
python -m pytest -m "unit or component or contract or security" --cov=app --cov-report=term-missing --cov-report=xml:artifacts\coverage.xml --junitxml=artifacts\fast-tests-junit.xml
if errorlevel 1 exit /b 1
set RUN_INTEGRATION=1
set BASE_URL=http://127.0.0.1:8080
set PARTNER_BASE_URL=http://127.0.0.1:8083
python -m pytest -m integration --junitxml=artifacts\integration-junit.xml
if errorlevel 1 exit /b 1
robot --outputdir artifacts\robot tests\robot
