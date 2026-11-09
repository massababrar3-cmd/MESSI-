@echo off
setlocal
cd /d "%~dp0"
"%~dp0runtime\python.exe" -I "%~dp0app\launcher.py"
if errorlevel 1 (
 echo.
 echo MESSI could not start. Please share the error above, without passwords.
 pause
)
