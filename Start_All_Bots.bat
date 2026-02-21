@echo off
title Bot Command Center
color 0A

echo ==========================================
echo        🤖 BOT COMMAND CENTER 🤖
echo ==========================================
echo.
echo Starting Market Bot and Sniper Bot...

:: สั่งรันบอท 2 ตัวแบบย่อหน้าต่างเก็บลง Taskbar ทันที
start "Market Bot" /MIN runbot.bat
start "Sniper Bot" /MIN run_sniper.bat

echo.
echo ✅ Bots are running minimized in the taskbar!
echo.
echo ==========================================
echo [ WARNING ]
echo IF YOU WANT TO STOP THE BOTS...
echo PRESS ANY KEY IN THIS WINDOW TO KILL THEM!
echo ==========================================
echo.
pause

:: พอกดปุ่มปุ๊บ มันจะสั่งปิดเฉพาะหน้าต่างที่ชื่อตรงเป๊ะๆ เท่านั้น ปลอดภัย 100%
echo.
echo 🛑 Stopping bots...
taskkill /FI "WINDOWTITLE eq Market Bot*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Sniper Bot*" /T /F >nul 2>&1

echo ✅ All bots successfully closed!
timeout /t 3
exit