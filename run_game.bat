@echo off
title Battleship Launcher
echo Starting Battleship Game Server and Clients...
echo.
echo Make sure you have installed the required packages by running:
echo pip install -r requirements.txt
echo.
echo Closing this window will NOT close the game windows.
echo.

start "Battleship Server" cmd /k python -m src.server
timeout /t 2 > nul
start "Battleship Client 1" cmd /k python -m src.client
start "Battleship Client 2" cmd /k python -m src.client