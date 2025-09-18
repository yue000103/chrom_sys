@echo off
echo ===============================================
echo Chromatography System Database Initialization
echo ===============================================

echo Initializing SQLite database...
cd ..\data\database
python init_database.py --init

echo Displaying database information...
python init_database.py --info

echo Database initialization completed!
pause