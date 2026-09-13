@echo off
title Human Tap GUI V1.2
cd /d "%~dp0"
echo Launching Human Tap Secure Transmission GUI V1.2...
python app_v1_2.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo An error occurred running the application.
    pause
)
