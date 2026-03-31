@echo off
REM ===================================================================
REM Hydrology FTE Agent - Automated Runner
REM ===================================================================
REM This batch file runs the Hydrology FTE Agent and logs all output
REM to Hydrology-Vault/agent_log.txt with timestamps.
REM
REM Usage:
REM   Double-click this file, or it will be run automatically by
REM   Windows Task Scheduler every day at 8:00 AM
REM ===================================================================

REM Set UTF-8 encoding to support emojis
chcp 65001 > nul

echo ============================================================
echo Hydrology FTE Agent - Starting...
echo ============================================================

REM Get the directory where this batch file is located
set "SCRIPT_DIR=%~dp0"

REM Navigate to the script directory
cd /d "%SCRIPT_DIR%"

echo 📁 Working Directory: %CD%
echo 🕐 Start Time: %DATE% %TIME%
echo ============================================================

REM Create log directory if it doesn't exist
if not exist "%SCRIPT_DIR%Hydrology-Vault" mkdir "%SCRIPT_DIR%Hydrology-Vault"

REM Define log file path
set "LOG_FILE=%SCRIPT_DIR%Hydrology-Vault\agent_log.txt"

REM Add timestamp header to log
echo ============================================================ >> "%LOG_FILE%"
echo 🌊 Hydrology FTE Agent - Run Log >> "%LOG_FILE%"
echo Date: %DATE% >> "%LOG_FILE%"
echo Time: %TIME% >> "%LOG_FILE%"
echo ============================================================ >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

REM Check if virtual environment exists
if exist "%SCRIPT_DIR%venv\Scripts\activate.bat" (
    echo ℹ️  Activating virtual environment...
    echo ℹ️  Activating virtual environment... >> "%LOG_FILE%"
    call "%SCRIPT_DIR%venv\Scripts\activate.bat"
) else if exist "%SCRIPT_DIR%.venv\Scripts\activate.bat" (
    echo ℹ️  Activating virtual environment...
    echo ℹ️  Activating virtual environment... >> "%LOG_FILE%"
    call "%SCRIPT_DIR%.venv\Scripts\activate.bat"
) else (
    echo ℹ️  No virtual environment found, using system Python
    echo ℹ️  No virtual environment found, using system Python >> "%LOG_FILE%"
)

REM Update Dashboard with run timestamp
echo 📝 Updating Dashboard with run timestamp...
powershell -ExecutionPolicy Bypass -File "%SCRIPT_DIR%update_dashboard.ps1"

REM Run the main agent script
echo 🚀 Starting Hydrology FTE Agent...
echo 🚀 Starting Hydrology FTE Agent... >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

REM Run in watcher mode for 5 minutes then exit (for scheduled runs)
REM This allows processing any files dropped overnight
start /B cmd /c "echo Agent running at %DATE% %TIME% >> "%LOG_FILE%" & python "%SCRIPT_DIR%main.py" --watcher >> "%LOG_FILE%" 2>&1 & echo Agent finished at %DATE% %TIME% >> "%LOG_FILE%""

REM Capture exit code
set "EXIT_CODE=%ERRORLEVEL%"

echo.
echo ============================================================
echo 🏁 Agent Run Complete
echo Exit Code: %EXIT_CODE%
echo End Time: %DATE% %TIME%
echo ============================================================

REM Log completion
echo. >> "%LOG_FILE%"
echo ============================================================ >> "%LOG_FILE%"
echo 🏁 Agent Run Complete >> "%LOG_FILE%"
echo Exit Code: %EXIT_CODE% >> "%LOG_FILE%"
echo End Time: %DATE% %TIME% >> "%LOG_FILE%"
echo ============================================================ >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

REM If there was an error, highlight it
if %EXIT_CODE% NEQ 0 (
    echo.
    echo ⚠️  WARNING: Agent exited with error code %EXIT_CODE%
    echo ⚠️  Check %LOG_FILE% for details
    echo.
    echo ⚠️  WARNING: Agent exited with error code %EXIT_CODE% >> "%LOG_FILE%"
)

echo.
echo 📝 Log file: %LOG_FILE%
echo.
echo ============================================================
echo ✅ Batch file execution complete
echo ============================================================

REM Keep window open for 2 seconds if run manually (so user can see output)
timeout /t 2 /nobreak > nul

exit /B %EXIT_CODE%
