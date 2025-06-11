@echo off
title Client Launcher
echo Starting 2 Battleship Game Clients...
echo Make sure the server is already running.
echo.

start "Battleship Client 1" cmd /k python -m src.client
start "Battleship Client 2" cmd /k python -m src.client