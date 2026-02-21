@echo off
title Sniper Bot
:start
echo Starting Sniper Bot...
python sniper_bot.py
timeout /t 5
goto start