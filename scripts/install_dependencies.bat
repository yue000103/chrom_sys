@echo off
echo ===============================================
echo Chromatography System Dependencies Installation
echo ===============================================

echo Installing backend dependencies...
cd ..
cd backend
pip install -r requirements.txt

echo Installing frontend dependencies...
cd ..\frontend
npm install

echo Dependencies installation completed!
pause