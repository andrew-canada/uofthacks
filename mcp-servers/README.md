# MCP Servers for UofTHacks Project

This directory contains Model Context Protocol (MCP) servers that expose project data to Cursor AI assistant.

## What is MCP?

MCP (Model Context Protocol) is a protocol that allows AI assistants like Cursor to access external data sources and tools. MCP servers provide:

- **Resources**: Data that can be read (trends, config, etc.)
- **Tools**: Actions that can be performed (search, list, etc.)

## Available MCP Servers

### 1. Trends Server (`trends-server.py`)

Exposes trend data from your project's JSON files.

**Resources:**
- `trend://<id>` - Individual trend data

**Tools:**
- `list_trends` - List all available trends
- `get_trend` - Get a specific trend by ID or name
- `search_trends` - Search trends by keyword
- `get_trends_by_platform` - Filter trends by platform (TikTok, Instagram, etc.)

### 2. Project Data Server (`project-data-server.py`)

Exposes project configuration, structure, and metadata.

**Resources:**
- `project://config` - Configuration and environment setup
- `project://structure` - Directory structure
- `project://endpoints` - API endpoint documentation
- `project://data-files` - Available data files

**Tools:**
- `get_config` - Get configuration information
- `get_structure` - Get project structure
- `get_endpoints` - Get API endpoint list
- `get_data_files` - List available data files

## Installation

### Prerequisites

Install the MCP Python SDK:

```bash
pip install mcp
```

Or if using a virtual environment:

```bash
# In backend directory
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install mcp
```

## Configuration in Cursor

### Method 1: Using Cursor Settings UI

1. Open Cursor Settings (`Ctrl+,` or `Cmd+,`)
2. Search for "MCP" or "Model Context Protocol"
3. Click "Edit in settings.json"
4. Add the server configurations (see below)

### Method 2: Direct Settings JSON

1. Open Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`)
2. Type "Preferences: Open User Settings (JSON)"
3. Add the following configuration:

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

**Important:** Update the paths to match your actual project location!

### Method 3: Using Virtual Environment (Recommended)

If you're using a virtual environment, use the Python interpreter from that venv:

```json
{
  "mcp.servers": {
    "uofthacks-trends": {
      "command": "C:/work/project/git-repo/uofthacks/backend/venv/Scripts/python.exe",
      "args": [
        "C:/work/project/git-repo/uofthacks/mcp-servers/trends-server.py"
      ]
    },
    "uofthacks-project-data": {
      "command": "C:/work/project/git-repo/uofthacks/backend/venv/Scripts/python.exe",
      "args": [
        "C:/work/project/git-repo/uofthacks/mcp-servers/project-data-server.py"
      ]
    }
  }
}
```

## Usage

Once configured, you can use these servers in Cursor:

### Example Queries

- "What trends are available in the database?"
- "Show me trends from TikTok"
- "Get the 'Aura Aesthetic' trend"
- "What are the API endpoints in this project?"
- "Show me the project structure"
- "What data files are available?"

The AI assistant will automatically use the MCP servers to fetch the relevant data.

## Testing MCP Servers

You can test the servers directly via command line:

```bash
# List all trends
python mcp-servers/trends-server.py list

# Get a specific trend
python mcp-servers/trends-server.py get "trend_001"

# Search trends
python mcp-servers/trends-server.py search "aura"
```

## Troubleshooting

### Server Not Starting

1. **Check Python Path**: Ensure Python is in your PATH or use full path to Python executable
2. **Check Dependencies**: Make sure `mcp` package is installed: `pip install mcp`
3. **Check File Paths**: Verify all paths in settings.json are correct
4. **Check Permissions**: Ensure Python scripts have execute permissions

### Import Errors

If you see import errors:
1. Ensure `PYTHONPATH` includes the `backend` directory
2. Or use the virtual environment's Python interpreter
3. Check that `backend/services/trends_service.py` exists

### Server Not Appearing in Cursor

1. Restart Cursor after adding MCP server configuration
2. Check Cursor's MCP server status (look for MCP icon in status bar)
3. Check Cursor logs for errors (Help → Toggle Developer Tools)

## Extending MCP Servers

To add new functionality:

1. Add new functions to the server script
2. Register new tools using `@server.list_tools()` and `@server.call_tool()`
3. Add new resources using `@server.list_resources()` and `@server.read_resource()`
4. Restart Cursor to reload the server

## Example: Adding Shopify Data

You could create a `shopify-server.py` that exposes product data:

```python
@server.list_tools()
async def handle_list_tools():
    return [
        Tool(
            name="get_products",
            description="Get products from Shopify",
            inputSchema={...}
        )
    ]
```

Then add it to your Cursor settings.json configuration.
