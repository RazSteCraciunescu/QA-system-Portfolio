@echo off
setlocal
cd /d "%~dp0\..\.."
docker compose up -d --build --wait --wait-timeout 180
if errorlevel 1 exit /b 1
python scripts\wait_for_service.py http://127.0.0.1:8080/health/ready 60
if errorlevel 1 exit /b 1
echo RelayHub is ready at http://127.0.0.1:8080
