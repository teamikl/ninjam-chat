@echo off
:repeat
    python bot.py
if %errorlevel% == 3 goto repeat
