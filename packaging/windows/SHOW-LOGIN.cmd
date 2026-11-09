@echo off
setlocal
cd /d "%~dp0"
"%~dp0runtime\python.exe" -I "%~dp0app\launcher.py" --login-details
if errorlevel 1 pause
