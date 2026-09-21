@echo off
title Tool TL - CLOUD
cd /d "%~dp0"
call ".\.venv\Scripts\activate.bat"
python TLCLOUD.py
if errorlevel 1 (
    echo.
    echo Da xay ra loi khi chay phan mem!
    pause
)
