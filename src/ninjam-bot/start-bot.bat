@echo off
:repeat
    python -O bot.py
    timeout 5 >nul
if %errorlevel% == 3 goto repeat
