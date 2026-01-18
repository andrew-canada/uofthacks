#!/bin/bash
# Setup script for MCP servers

echo "Setting up MCP servers for UofTHacks..."

# Check if we're in the right directory
if [ ! -f "trends-server.py" ]; then
    echo "Error: Please run this script from the mcp-servers directory"
    exit 1
fi

# Check if Python virtual environment exists
if [ -d "../backend/venv" ]; then
    echo "Found virtual environment, activating it..."
    source ../backend/venv/bin/activate
elif [ -d "../backend/venv/Scripts" ]; then
    echo "Found virtual environment (Windows), activating it..."
    source ../backend/venv/Scripts/activate
fi

# Install MCP package
echo "Installing MCP package..."
pip install mcp

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Open Cursor Settings (Ctrl+, or Cmd+,)"
echo "2. Open User Settings JSON (Ctrl+Shift+P -> 'Preferences: Open User Settings (JSON)')"
echo "3. Add the configuration from .cursor-settings-example.json"
echo "4. Update the file paths to match your project location"
echo "5. Restart Cursor"
echo ""
echo "See MCP_SETUP.md for detailed instructions."
