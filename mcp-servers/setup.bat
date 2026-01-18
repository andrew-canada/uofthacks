@echo off
REM Setup script for MCP servers (Windows)

echo Setting up MCP servers for UofTHacks...

REM Check if we're in the right directory
if not exist "trends-server.py" (
    echo Error: Please run this script from the mcp-servers directory
    exit /b 1
)

REM Check if Python virtual environment exists
if exist "..\backend\venv\Scripts\activate.bat" (
    echo Found virtual environment, activating it...
    call ..\backend\venv\Scripts\activate.bat
)

REM Install MCP package
echo Installing MCP package...
pip install mcp

echo.
echo Setup complete!
echo.
echo Next steps:
echo 1. Open Cursor Settings (Ctrl+,)
echo 2. Open User Settings JSON (Ctrl+Shift+P -^> 'Preferences: Open User Settings (JSON)')
echo 3. Add the configuration from .cursor-settings-example.json
echo 4. Update the file paths to match your project location
echo 5. Restart Cursor
echo.
echo See MCP_SETUP.md for detailed instructions.

pause
