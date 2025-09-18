@echo off
echo ===============================================
echo Chromatography Control System Startup Script
echo ===============================================

echo Starting backend service...
cd ..\backend
start "Backend" cmd /k "python main.py"

timeout /t 5

echo Starting frontend service...
cd ..\frontend
start "Frontend" cmd /k "npm run dev"

echo System startup completed!
echo Frontend URL: http://localhost:3000
echo Backend URL: http://localhost:8008
echo API Documentation: http://localhost:8008/docs

pause