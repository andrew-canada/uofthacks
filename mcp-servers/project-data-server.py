#!/usr/bin/env python3
"""
MCP Server for UofTHacks Project Data
Exposes project configuration, structure, and data to Cursor AI assistant.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, List, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


def get_project_root() -> Path:
    """Get project root directory."""
    return Path(__file__).parent.parent


def get_config_info() -> dict:
    """Get configuration information."""
    config_file = get_project_root() / "backend" / "config.py"
    config_info = {
        "config_file": str(config_file),
        "exists": config_file.exists(),
        "environment_variables": {}
    }
    
    # List relevant env vars (without values for security)
    env_vars = [
        "SHOP_DOMAIN", "SHOPIFY_STORE_DOMAIN", "SHOPIFY_ACCESS_TOKEN",
        "GEMINI_API_KEY", "TWELVE_LABS_API_KEY", "YOUTUBE_API_KEY"
    ]
    
    for var in env_vars:
        if os.environ.get(var):
            config_info["environment_variables"][var] = "***configured***"
        else:
            config_info["environment_variables"][var] = "not set"
    
    return config_info


def get_project_structure() -> dict:
    """Get project directory structure."""
    root = get_project_root()
    
    structure = {
        "backend": {
            "services": list((root / "backend" / "services").glob("*.py")) if (root / "backend" / "services").exists() else [],
            "routes": list((root / "backend" / "routes").glob("*.py")) if (root / "backend" / "routes").exists() else [],
            "graphs": list((root / "backend" / "graphs").glob("*.py")) if (root / "backend" / "graphs").exists() else [],
        },
        "pipeline": {
            "files": list((root / "pipeline").glob("*.py")) if (root / "pipeline").exists() else [],
        },
        "frontend": {
            "shopify_app": list((root / "frontend" / "shopify-app").glob("*.js")) if (root / "frontend" / "shopify-app").exists() else [],
        }
    }
    
    # Convert Path objects to strings
    for section in structure.values():
        if isinstance(section, dict):
            for key in section:
                section[key] = [str(p.relative_to(root)) for p in section[key]]
    
    return structure


def get_api_endpoints() -> dict:
    """Get API endpoint information."""
    return {
        "backend": {
            "base_url": "http://localhost:5000",
            "endpoints": [
                {"path": "/health", "method": "GET", "description": "Health check"},
                {"path": "/api/products", "method": "GET", "description": "List all products"},
                {"path": "/api/products/analyze", "method": "POST", "description": "Analyze products with AI"},
                {"path": "/api/trends", "method": "GET", "description": "List all trends"},
                {"path": "/api/trends/<id>", "method": "GET", "description": "Get specific trend"},
            ]
        },
        "frontend": {
            "base_url": "http://localhost:3000",
            "endpoints": [
                {"path": "/api/replace-product", "method": "POST", "description": "Replace product in collection"},
                {"path": "/api/collections", "method": "GET", "description": "List collections"},
                {"path": "/api/products", "method": "GET", "description": "List products"},
            ]
        }
    }


def get_data_files() -> dict:
    """Get list of data files."""
    root = get_project_root()
    
    data_files = {}
    
    # Backend data
    backend_data = root / "backend" / "data"
    if backend_data.exists():
        data_files["backend"] = [str(p.relative_to(root)) for p in backend_data.glob("*.json")]
    
    # Pipeline data
    pipeline_data = root / "pipeline"
    if pipeline_data.exists():
        data_files["pipeline"] = [str(p.relative_to(root)) for p in pipeline_data.glob("*.json")]
    
    return data_files


def main():
    """MCP Server main entry point using stdio."""
    import asyncio
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Resource, Tool, TextContent
    
    server = Server("uofthacks-project-data")
    
    @server.list_resources()
    async def handle_list_resources() -> List[Resource]:
        """List available project resources."""
        return [
            Resource(
                uri="project://config",
                name="Project Configuration",
                description="Configuration and environment setup",
                mimeType="application/json"
            ),
            Resource(
                uri="project://structure",
                name="Project Structure",
                description="Directory structure and file organization",
                mimeType="application/json"
            ),
            Resource(
                uri="project://endpoints",
                name="API Endpoints",
                description="Available API endpoints",
                mimeType="application/json"
            ),
            Resource(
                uri="project://data-files",
                name="Data Files",
                description="Available data files (JSON, etc.)",
                mimeType="application/json"
            ),
        ]
    
    @server.read_resource()
    async def handle_read_resource(uri: str) -> str:
        """Read a specific project resource."""
        if uri == "project://config":
            return json.dumps(get_config_info(), indent=2)
        elif uri == "project://structure":
            return json.dumps(get_project_structure(), indent=2)
        elif uri == "project://endpoints":
            return json.dumps(get_api_endpoints(), indent=2)
        elif uri == "project://data-files":
            return json.dumps(get_data_files(), indent=2)
        else:
            return json.dumps({"error": f"Unknown resource: {uri}"})
    
    @server.list_tools()
    async def handle_list_tools() -> List[Tool]:
        """List available tools."""
        return [
            Tool(
                name="get_config",
                description="Get project configuration information",
                inputSchema={
                    "type": "object",
                    "properties": {},
                }
            ),
            Tool(
                name="get_structure",
                description="Get project directory structure",
                inputSchema={
                    "type": "object",
                    "properties": {},
                }
            ),
            Tool(
                name="get_endpoints",
                description="Get API endpoint information",
                inputSchema={
                    "type": "object",
                    "properties": {},
                }
            ),
            Tool(
                name="get_data_files",
                description="List available data files in the project",
                inputSchema={
                    "type": "object",
                    "properties": {},
                }
            )
        ]
    
    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict) -> List[TextContent]:
        """Handle tool calls."""
        if name == "get_config":
            return [TextContent(
                type="text",
                text=json.dumps(get_config_info(), indent=2)
            )]
        
        elif name == "get_structure":
            return [TextContent(
                type="text",
                text=json.dumps(get_project_structure(), indent=2)
            )]
        
        elif name == "get_endpoints":
            return [TextContent(
                type="text",
                text=json.dumps(get_api_endpoints(), indent=2)
            )]
        
        elif name == "get_data_files":
            return [TextContent(
                type="text",
                text=json.dumps(get_data_files(), indent=2)
            )]
        
        else:
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"Unknown tool: {name}"})
            )]
    
    async def run():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())
    
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
