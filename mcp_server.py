#!/usr/bin/env python3
"""
LogiSwarm Model Context Protocol (MCP) Server Entrypoint
Usage:
  python mcp_server.py
Configured for Claude Desktop, Antigravity, Cursor, or any standard MCP client.
"""
import sys
import os

# Add project root to PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.mcp.logistics_mcp_server import LogisticsMCPServer

if __name__ == "__main__":
    server = LogisticsMCPServer()
    server.run_stdio()
