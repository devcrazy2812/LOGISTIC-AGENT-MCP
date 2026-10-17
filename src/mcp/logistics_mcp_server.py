import sys
import json
from typing import Dict, Any, List
from ..core.swarm_controller import SwarmController
from ..tools.gemini_client import GoogleGeminiClient

class LogisticsMCPServer:
    """
    Model Context Protocol (MCP) Server for Logistics Handler:
    Exposes logistics capabilities, fleet telematics, disruption injection,
    and multimodal cargo analysis via the standard MCP JSON-RPC 2.0 protocol.
    """

    TOOLS = [
        {
            "name": "get_fleet_status",
            "description": "Returns telematics, current locations, payloads, and status of all fleet vehicles.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "include_routes": {"type": "boolean", "description": "Whether to include full route stops"}
                }
            }
        },
        {
            "name": "optimize_cvrp_routes",
            "description": "Executes multi-agent Capacitated Vehicle Routing optimization taking into account weight, volume, deadlines, and EV prioritization.",
            "inputSchema": {
                "type": "object",
                "properties": {}
            }
        },
        {
            "name": "inject_disruption",
            "description": "Simulates a supply chain crisis (breakdown, severe_weather, road_closure, urgent_surge) and triggers self-healing rerouting.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "disruption_type": {
                        "type": "string",
                        "enum": ["breakdown", "severe_weather", "road_closure", "urgent_surge"],
                        "description": "Type of disruption to inject"
                    }
                },
                "required": ["disruption_type"]
            }
        },
        {
            "name": "inspect_cargo_multimodal",
            "description": "Performs Google Gemini multimodal vision inspection on cargo damage or shipping labels.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "image_base64": {"type": "string", "description": "Base64-encoded image of the package or cargo"},
                    "cargo_id": {"type": "string", "description": "Consignment / Order ID"}
                }
            }
        },
        {
            "name": "evaluate_feedback_loop",
            "description": "Audits current logistics plan and returns SLA, green carbon, and load balance critique scores.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "iteration": {"type": "integer", "description": "Optimization loop iteration number"}
                }
            }
        }
    ]

    def __init__(self, controller: Optional[SwarmController] = None):
        self.controller = controller or SwarmController()
        self.gemini_client = GoogleGeminiClient()

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Processes an MCP JSON-RPC 2.0 request."""
        req_id = request.get("id")
        method = request.get("method", "")
        params = request.get("params", {})

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {
                        "name": "LogiSwarm-MCP-Server",
                        "version": "1.0.0"
                    },
                    "capabilities": {
                        "tools": {}
                    }
                }
            }

        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": self.TOOLS
                }
            }

        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            return self._execute_tool(req_id, tool_name, arguments)

        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32601,
                    "message": f"Method '{method}' not found"
                }
            }

    def _execute_tool(self, req_id: Any, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if tool_name == "get_fleet_status":
                state = self.controller.get_state()
                result_text = json.dumps({
                    "vehicles": state["vehicles"],
                    "metrics": state["metrics"]
                }, indent=2)

            elif tool_name == "optimize_cvrp_routes":
                res = self.controller.run_initial_optimization()
                result_text = json.dumps(res, indent=2)

            elif tool_name == "inject_disruption":
                dtype = args.get("disruption_type", "breakdown")
                res = self.controller.inject_disruption(dtype)
                result_text = json.dumps(res, indent=2)

            elif tool_name == "inspect_cargo_multimodal":
                img_b64 = args.get("image_base64")
                analysis = self.gemini_client.analyze_multimodal_cargo(image_base64=img_b64)
                result_text = json.dumps(analysis, indent=2)

            elif tool_name == "evaluate_feedback_loop":
                iteration = args.get("iteration", 1)
                fb = self.controller.evaluator.evaluate_plan(
                    self.controller.vehicles, self.controller.orders, iteration=iteration
                )
                result_text = json.dumps(fb, indent=2)

            else:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32602, "message": f"Unknown tool: {tool_name}"}
                }

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": result_text
                        }
                    ]
                }
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32000, "message": f"Execution failed: {str(e)}"}
            }

    def run_stdio(self):
        """Standard IO server loop for MCP client integrations."""
        for line in sys.stdin:
            if not line.strip():
                continue
            try:
                req = json.loads(line)
                resp = self.handle_request(req)
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()
            except Exception as e:
                err = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": f"Parse error: {e}"}
                }
                sys.stdout.write(json.dumps(err) + "\n")
                sys.stdout.flush()
