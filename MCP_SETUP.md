# MCP Server Setup Guide for UofTHacks

This guide will help you set up MCP (Model Context Protocol) servers in Cursor to expose your project data to the AI assistant.

## Quick Start

### Step 1: Install MCP Package

```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install mcp
```

### Step 2: Configure in Cursor

1. **Open Cursor Settings:**
   - Press `Ctrl+,` (Windows/Linux) or `Cmd+,` (Mac)
   - Or go to `File → Preferences → Settings`

2. **Open Settings JSON:**
   - Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac)
   - Type "Preferences: Open User Settings (JSON)"
   - Select it

3. **Add MCP Server Configuration:**

Copy this configuration and **update the paths** to match your project:

```json
{
  "mcp.servers": {
    "uofthacks-trends": {
      "command": "python",
      "args": [
        "C:/work/project/git-repo/uofthacks/mcp-servers/trends-server.py"
      ],
      "env": {
        "PYTHONPATH": "C:/work/project/git-repo/uofthacks/backend"
      }
    },
    "uofthacks-project-data": {
      "command": "python",
      "args": [
        "C:/work/project/git-repo/uofthacks/mcp-servers/project-data-server.py"
      ],
      "env": {
        "PYTHONPATH": "C:/work/project/git-repo/uofthacks/backend"
      }
    }
  }
}
```

**Important:** Replace `C:/work/project/git-repo/uofthacks` with your actual project path!

### Step 3: Restart Cursor

Close and reopen Cursor to load the MCP servers.

### Step 4: Verify

1. Look for the MCP icon in Cursor's status bar
2. Try asking the AI assistant: "What trends are available in the project?"
3. The assistant should use the MCP servers to fetch data

## Alternative: Using Virtual Environment

If you're using a Python virtual environment (recommended), use the venv's Python interpreter:

**On Windows:**
```json
{
  "mcp.servers": {
    "uofthacks-trends": {
      "command": "C:/work/project/git-repo/uofthacks/backend/venv/Scripts/python.exe",
      "args": [
        "C:/work/project/git-repo/uofthacks/mcp-servers/trends-server.py"
      ]
    }
  }
}
```

**On Mac/Linux:**
```json
{
  "mcp.servers": {
    "uofthacks-trends": {
      "command": "/absolute/path/to/uofthacks/backend/venv/bin/python",
      "args": [
        "/absolute/path/to/uofthacks/mcp-servers/trends-server.py"
      ]
    }
  }
}
```

## What These Servers Do

### Trends Server
- Exposes trend data from `backend/data/sample_trends.json` and `pipeline/genz_trends.json`
- Allows AI to answer questions about trends
- Tools: list trends, search trends, get by ID, filter by platform

### Project Data Server
- Exposes project structure, configuration, and API endpoints
- Helps AI understand your project layout
- Tools: get config, get structure, get endpoints, list data files

## Example Queries

Once set up, you can ask:

- ✅ "What trends are in the database?"
- ✅ "Show me TikTok trends"
- ✅ "What's the 'Aura Aesthetic' trend?"
- ✅ "What API endpoints are available?"
- ✅ "Show me the project structure"
- ✅ "What data files exist in the project?"

## Troubleshooting

### "Module not found" or Import Errors

**Solution:** Use the virtual environment's Python interpreter (see "Alternative" section above) or ensure `PYTHONPATH` includes the backend directory.

### Server Not Starting

**Check:**
1. Python path is correct in settings.json
2. MCP package is installed: `pip install mcp`
3. Script files exist at the specified paths
4. File paths use forward slashes `/` or escaped backslashes `\\`

### Server Not Appearing in Cursor

**Try:**
1. Restart Cursor completely
2. Check Cursor's developer console (Help → Toggle Developer Tools)
3. Verify JSON syntax in settings.json (use a JSON validator)

### Path Issues on Windows

Use one of these formats:
- Forward slashes: `C:/work/project/git-repo/uofthacks/...`
- Escaped backslashes: `C:\\work\\project\\git-repo\\uofthacks\\...`
- Or use relative paths if possible

## Getting Help

- Check `mcp-servers/README.md` for detailed documentation
- Test servers manually: `python mcp-servers/trends-server.py list`
- Check Cursor's MCP server status in the status bar
