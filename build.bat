@echo off
echo ==================================================
echo Building Tool TL - CLOUD v1.3 (ONEDIR)
echo ==================================================

if exist TLCLOUD.spec del /f /q TLCLOUD.spec
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

pyinstaller --onedir --noconfirm --windowed --name="TLCLOUD" --icon="icon.ico" --add-data "icon.ico;." "TLCLOUD.py"

if %ERRORLEVEL% NEQ 0 (
    echo Compile error!
    pause
    exit /b %ERRORLEVEL%
)

echo Copying database to output directory...
if not exist "dist\TLCLOUD\database" mkdir "dist\TLCLOUD\database"
xcopy /y /e "database\*.*" "dist\TLCLOUD\database\"

if exist "config.json" (
    xcopy /y "config.json" "dist\TLCLOUD\"
)

echo ==================================================
echo Build finished successfully!
echo Output directory: dist\TLCLOUD
echo ==================================================
pause
