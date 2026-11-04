@echo off
rem Starts the test runner web page and opens it in your default browser.
cd /d "%~dp0"
start "" http://localhost:5000
venv\Scripts\python.exe -m runner.app
pause