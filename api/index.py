import sys
import os

# Ensure project root is available on sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.core.http_server import LogisticsAPIHandler
from src.core.swarm_controller import SwarmController
from src.mcp.logistics_mcp_server import LogisticsMCPServer

# Initialize singleton multi-agent swarm controller in serverless execution context
controller = SwarmController()
controller.run_initial_optimization()
mcp_server = LogisticsMCPServer(controller=controller)

web_dir = os.path.join(PROJECT_ROOT, "public")
if not os.path.exists(web_dir):
    web_dir = os.path.join(PROJECT_ROOT, "web")

LogisticsAPIHandler.controller = controller
LogisticsAPIHandler.mcp_server = mcp_server
LogisticsAPIHandler.web_dir = web_dir


class handler(LogisticsAPIHandler):
    """
    Vercel Serverless Function entrypoint.
    Vercel's Python runtime natively invokes classes named `handler`
    inheriting from BaseHTTPRequestHandler.
    """
    pass
