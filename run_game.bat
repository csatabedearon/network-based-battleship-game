@echo off
start cmd /k python server.py
timeout /t 2 > nul
start cmd /k python client.py
start cmd /k python client.py
