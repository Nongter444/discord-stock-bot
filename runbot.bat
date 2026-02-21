@echo off
title Market Bot
:start
echo Starting Market Bot...
python check.py
timeout /t 5
goto start