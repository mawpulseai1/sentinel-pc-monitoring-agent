@echo off
title PC Monitoring Agent - Animated Wallpaper HUD
cd /d "%~dp0"
python main.py %*
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Agent exited with error code %ERRORLEVEL%.
    pause
)
