#!/usr/bin/env python3
"""
MCP Server for UofTHacks Trends Data
Exposes trend data from JSON files to Cursor AI assistant.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, List, Optional

# Add parent directory to path to import backend services
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

try:
    from services.trends_service import trends_service
except ImportError:
    # Fallback if services not available
    trends_service = None


def get_trends_data_file() -> Path:
    """Get path to trends JSON file."""
    # Try backend data first
    backend_data = Path(__file__).parent.parent / "backend" / "data" / "sample_trends.json"
    if backend_data.exists():
        return backend_data
    
    # Try pipeline data
    pipeline_data = Path(__file__).parent.parent / "pipeline" / "genz_trends.json"
    if pipeline_data.exists():
        return pipeline_data
    
    # Default
    return backend_data


def load_trends() -> List[dict]:
    """Load trends from JSON file."""
    trends_file = get_trends_data_file()
    
    if not trends_file.exists():
        return []
    
    try:
        with open(trends_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different JSON structures
        if 'trends' in data:
            return data['trends']
        elif isinstance(data, list):
            return data
        else:
            return []
    except Exception as e:
        print(f"Error loading trends: {e}", file=sys.stderr)
        return []


def list_trends() -> List[dict]:
    """List all available trends."""
    if trends_service:
        try:
            return trends_service.get_current_trends()
        except Exception:
            pass
    
    return load_trends()


def get_trend_by_id(trend_id: str) -> Optional[dict]:
    """Get a specific trend by ID."""
    trends = list_trends()
    
    # Try different ID fields
    for trend in trends:
        if trend.get('id') == trend_id or trend.get('trend_id') == trend_id:
            return trend
        if str(trend.get('id')) == str(trend_id) or str(trend.get('trend_id')) == str(trend_id):
            return trend
    
    return None


def search_trends(query: str) -> List[dict]:
    """Search trends by name or description."""
    trends = list_trends()
    query_lower = query.lower()
    
    results = []
    for trend in trends:
        name = trend.get('name', '').lower()
        desc = trend.get('description', '').lower()
        
        if query_lower in name or query_lower in desc:
            results.append(trend)
    
    return results


def get_trends_by_platform(platform: str) -> List[dict]:
    """Get trends by platform."""
    trends = list_trends()
    platform_lower = platform.lower()
    
    results = []
    for trend in trends:
        platforms = trend.get('platforms', [])
        platform_str = trend.get('platform', '')
        
        if isinstance(platforms, list):
            if any(platform_lower in p.lower() for p in platforms):
                results.append(trend)
        elif platform_lower in platform_str.lower():
            results.append(trend)
    
    return results


def main():
    """MCP Server main entry point using stdio."""
    import asyncio
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Resource, Tool, TextContent
    
    server = Server("uofthacks-trends")
    
    @server.list_resources()
    async def handle_list_resources() -> List[Resource]:
        """List available trend resources."""
        trends = list_trends()
        return [
            Resource(
                uri=f"trend://{trend.get('id', i)}",
                name=trend.get('name', f"Trend {i}"),
                description=trend.get('description', '')[:100] + '...' if len(trend.get('description', '')) > 100 else trend.get('description', ''),
                mimeType="application/json"
            )
            for i, trend in enumerate(trends)
        ]
    
    @server.read_resource()
    async def handle_read_resource(uri: str) -> str:
        """Read a specific trend resource."""
        trend_id = uri.replace("trend://", "")
        trend = get_trend_by_id(trend_id)
        
        if not trend:
            return json.dumps({"error": f"Trend {trend_id} not found"})
        
        return json.dumps(trend, indent=2)
    
    @server.list_tools()
    async def handle_list_tools() -> List[Tool]:
        """List available tools."""
        return [
            Tool(
                name="list_trends",
                description="List all available trends from the UofTHacks trend database",
                inputSchema={
                    "type": "object",
                    "properties": {},
                }
            ),
            Tool(
                name="get_trend",
                description="Get a specific trend by ID or name",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "trend_id": {
                            "type": "string",
                            "description": "Trend ID or name"
                        }
                    },
                    "required": ["trend_id"]
                }
            ),
            Tool(
                name="search_trends",
                description="Search trends by keyword in name or description",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="get_trends_by_platform",
                description="Get all trends for a specific platform (TikTok, Instagram, etc.)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "platform": {
                            "type": "string",
                            "description": "Platform name (e.g., TikTok, Instagram)"
                        }
                    },
                    "required": ["platform"]
                }
            )
        ]
    
    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict) -> List[TextContent]:
        """Handle tool calls."""
        if name == "list_trends":
            trends = list_trends()
            return [TextContent(
                type="text",
                text=json.dumps({"trends": trends, "count": len(trends)}, indent=2)
            )]
        
        elif name == "get_trend":
            trend_id = arguments.get("trend_id")
            trend = get_trend_by_id(trend_id)
            
            if not trend:
                # Try search as fallback
                trends = search_trends(trend_id)
                if trends:
                    trend = trends[0]
            
            if trend:
                return [TextContent(
                    type="text",
                    text=json.dumps(trend, indent=2)
                )]
            else:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": f"Trend '{trend_id}' not found"})
                )]
        
        elif name == "search_trends":
            query = arguments.get("query", "")
            results = search_trends(query)
            return [TextContent(
                type="text",
                text=json.dumps({"query": query, "results": results, "count": len(results)}, indent=2)
            )]
        
        elif name == "get_trends_by_platform":
            platform = arguments.get("platform", "")
            results = get_trends_by_platform(platform)
            return [TextContent(
                type="text",
                text=json.dumps({"platform": platform, "trends": results, "count": len(results)}, indent=2)
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
    # If run directly without MCP library, provide simple CLI interface
    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            trends = list_trends()
            print(json.dumps({"trends": trends, "count": len(trends)}, indent=2))
        elif sys.argv[1] == "get" and len(sys.argv) > 2:
            trend = get_trend_by_id(sys.argv[2])
            print(json.dumps(trend, indent=2) if trend else json.dumps({"error": "Not found"}))
        elif sys.argv[1] == "search" and len(sys.argv) > 2:
            results = search_trends(sys.argv[2])
            print(json.dumps({"results": results, "count": len(results)}, indent=2))
    else:
        # Try to run as MCP server
        main()
