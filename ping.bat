@echo off
setlocal

:: Set the URL here
set "URL=https://ballatics.onrender.com/health_check"

:loop
echo Fetching response from %URL% at %time%
powershell -Command "Invoke-RestMethod -Uri '%URL%'"
timeout /t 30 >nul
goto loop
