@echo off
:repeat
    python bot.py
    timeout 5 >nul
if %errorlevel% == 3 goto repeat
