@echo off
echo Checking OmniRoute status...
curl -s http://localhost:20128/v1/models >nul 2>&1
if %errorlevel% equ 0 (
    echo OmniRoute is running on port 20128
) else (
    echo OmniRoute is NOT running. Starting it now...
    start /b cmd /c "set PORT=20128 && omniroute start"
    timeout /t 5 >nul
    curl -s http://localhost:20128/v1/models >nul 2>&1
    if %errorlevel% equ 0 (
        echo OmniRoute started successfully!
    ) else (
        echo Failed to start OmniRoute. Check logs.
    )
)
