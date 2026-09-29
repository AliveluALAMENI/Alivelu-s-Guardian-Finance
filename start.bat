@echo off
title GuardianFi AI — The Guardian Ledger Platform
echo ===================================================
echo     GuardianFi AI — Starting Backend Server
echo     • Automated Excel Persistence (4 Spreadsheets)
echo     • Real-Time Indian Equities & Stock Ticker Tape
echo ===================================================
echo.
echo Launching persistence engine and opening Chrome...
start "" http://localhost:3000
node server.js
pause

