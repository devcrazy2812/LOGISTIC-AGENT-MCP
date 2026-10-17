from __future__ import annotations
import sys
import json
import logging
from typing import Dict, Any, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.swarm_controller import SwarmController

from ..tools.gemini_client import GoogleGeminiClient

logger = logging.getLogger("LogisticsMCPServer")
if not logger.handlers:
    _handler = logging.StreamHandler(sys.stderr)
    _handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] [MCP] %(message)s"))
    logger.addHandler(_handler)
logger.setLevel(logging.INFO)


class LogisticsMCPServer:
    """
    Model Context Protocol (MCP) Server for Logistics Handler:
    Exposes logistics capabilities, fleet telematics, disruption injection,
    and multimodal cargo analysis via dual MCP JSON-RPC 2.0 protocol specifications:
    - Modern 2026-07-28 (stateless discover, _meta versioning)
    - Legacy 2024-11-05 (initialize handshake)
    """

    SUPPORTED_PROTOCOLS = ["2026-07-28", "2024-11-05"]

    TOOLS = [
        {
            "name": "get_fleet_status",
            "description": "Returns telematics, current locations, payloads, and status of all fleet vehicles.",
            "annotations": {
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True
            },
            "inputSchema": {
                "type": "object",
                "properties": {
                    "include_routes": {"type": "boolean", "description": "Whether to include full route stops"}
                }
            },
            "outputSchema": {
                "type": "object",
                "properties": {
                    "vehicles": {"type": "array"},
                    "metrics": {"type": "object"}
                }
            }
        },
        {
            "name": "optimize_cvrp_routes",
            "description": "Executes multi-agent Capacitated Vehicle Routing optimization taking into account weight, volume, deadlines, and EV prioritization.",
            "annotations": {
                "readOnlyHint": False,
                "destructiveHint": False,
                "idempotentHint": False
            },
            "inputSchema": {
                "type": "object",
                "properties": {}
            }
        },
        {
            "name": "inject_disruption",
            "description": "Simulates a supply chain crisis (breakdown, severe_weather, road_closure, urgent_surge) and triggers self-healing rerouting.",
            "annotations": {
                "readOnlyHint": False,
                "destructiveHint": True,
                "idempotentHint": False
            },
            "inputSchema": {
                "type": "object",
                "properties": {
                    "disruption_type": {
                        "type": "string",
                        "enum": ["breakdown", "severe_weather", "road_closure", "urgent_surge"],
                        "description": "Type of disruption to inject"
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "If true, simulates disruption impact without mutating live controller state",
                        "default": False
                    }
                },
                "required": ["disruption_type"]
            }
        },
        {
            "name": "inspect_cargo_multimodal",
            "description": "Performs Google Gemini multimodal vision inspection on cargo damage or shipping labels.",
            "annotations": {
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True
            },
            "inputSchema": {
                "type": "object",
                "properties": {
                    "image_base64": {"type": "string", "description": "Base64-encoded image of the package or cargo"},
                    "cargo_id": {"type": "string", "description": "Consignment / Order ID"}
                },
                "required": ["image_base64"]
            }
        },
        {
            "name": "evaluate_feedback_loop",
            "description": "Audits current logistics plan and returns SLA, green carbon, and load balance critique scores.",
            "annotations": {
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True
            },
            "inputSchema": {
                "type": "object",
                "properties": {
                    "iteration": {"type": "integer", "description": "Optimization loop iteration number"}
                }
            }
        }
    ]

    RESOURCES = [
        {
            "uri": "fleet://status",
            "name": "Fleet Telematics & Status",
            "description": "Real-time positions, telemetry, battery, and capacity of all active fleet vehicles",
            "mimeType": "application/json"
        },
        {
            "uri": "depots://list",
            "name": "Logistics Hubs & Depots",
            "description": "Central warehouse and regional distribution hubs with geographic coordinates and capacities",
            "mimeType": "application/json"
        },
        {
            "uri": "orders://open",
            "name": "Open Priority Consignments",
            "description": "Active orders, delivery coordinates, deadlines, and SLA penalty weightings",
            "mimeType": "application/json"
        }
    ]

    PROMPTS = [
        {
            "name": "dispatcher_briefing",
            "description": "Generates a tactical morning briefing for dispatchers with fleet availability and pending order volume.",
            "arguments": []
        },
        {
            "name": "disruption_postmortem",
            "description": "Analyzes root causes and recovery actions following a simulated supply chain crisis.",
            "arguments": [
                {
                    "name": "incident_type",
                    "description": "Type of disruption analyzed (breakdown, severe_weather, road_closure, urgent_surge)",
                    "required": False
                }
            ]
        }
    ]

    def __init__(self, controller: Optional[SwarmController] = None):
        if controller is None:
            from ..core.swarm_controller import SwarmController
            self.controller = SwarmController()
        else:
            self.controller = controller
        self.gemini_client = GoogleGeminiClient()

    def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Processes an MCP JSON-RPC 2.0 request or notification."""
        if not isinstance(request, dict) or ("jsonrpc" not in request and "method" not in request):
            return {
                "jsonrpc": "2.0",
                "id": request.get("id") if isinstance(request, dict) else None,
                "error": {
                    "code": -32600,
                    "message": "Invalid Request: expected JSON-RPC 2.0 object"
                }
            }

        req_id = request.get("id")
        method = request.get("method", "")
        params = request.get("params") or {}

        # Handle JSON-RPC Notifications (no id)
        if req_id is None and (method.startswith("notifications/") or not method):
            logger.info(f"Received notification: {method}")
            return None

        # Protocol version validation from _meta (MCP 2026-07-28)
        meta = request.get("_meta") or params.get("_meta") or {}
        client_version = meta.get("io.modelcontextprotocol/protocolVersion")
        if client_version and client_version not in self.SUPPORTED_PROTOCOLS:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32000,
                    "message": f"Unsupported protocol version '{client_version}'. Supported: {self.SUPPORTED_PROTOCOLS}"
                }
            }

        if method == "initialize":
            client_proto = params.get("protocolVersion", "2024-11-05")
            negotiated = client_proto if client_proto in self.SUPPORTED_PROTOCOLS else "2024-11-05"
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": negotiated,
                    "serverInfo": {
                        "name": "LogiSwarm-MCP-Server",
                        "version": "1.0.0"
                    },
                    "capabilities": {
                        "tools": {},
                        "resources": {},
                        "prompts": {}
                    }
                }
            }

        elif method == "server/discover":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "serverInfo": {
                        "name": "LogiSwarm-MCP-Server",
                        "version": "1.0.0"
                    },
                    "capabilities": {
                        "tools": {},
                        "resources": {},
                        "prompts": {}
                    },
                    "protocols": list(self.SUPPORTED_PROTOCOLS)
                }
            }

        elif method == "ping":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {}
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
            arguments = params.get("arguments") or {}
            return self._execute_tool(req_id, tool_name, arguments)

        elif method == "resources/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "resources": self.RESOURCES
                }
            }

        elif method == "resources/read":
            uri = params.get("uri", "")
            return self._read_resource(req_id, uri)

        elif method == "prompts/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "prompts": self.PROMPTS
                }
            }

        elif method == "prompts/get":
            prompt_name = params.get("name", "")
            prompt_args = params.get("arguments") or {}
            return self._get_prompt(req_id, prompt_name, prompt_args)

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
                data = {
                    "vehicles": state["vehicles"],
                    "metrics": state["metrics"]
                }
                result_text = json.dumps(data, indent=2)

            elif tool_name == "optimize_cvrp_routes":
                res = self.controller.run_initial_optimization()
                result_text = json.dumps(res, indent=2)

            elif tool_name == "inject_disruption":
                dtype = args.get("disruption_type", "breakdown")
                dry_run = bool(args.get("dry_run", False))
                if dry_run:
                    preview = {
                        "mode": "DRY_RUN_SIMULATION",
                        "disruption_type": dtype,
                        "projected_impact": {
                            "status": "simulated",
                            "affected_scope": f"Simulated impact preview for {dtype}",
                            "estimated_sla_risk": "Moderate",
                            "recommended_healing_strategy": "Dynamic rerouting via secondary depot with EV load balancing",
                            "state_mutated": False
                        }
                    }
                    result_text = json.dumps(preview, indent=2)
                else:
                    res = self.controller.inject_disruption(dtype)
                    result_text = json.dumps(res, indent=2)

            elif tool_name == "inspect_cargo_multimodal":
                img_b64 = args.get("image_base64")
                if not img_b64 or not isinstance(img_b64, str) or not img_b64.strip():
                    return {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Validation Error: 'image_base64' is required and cannot be empty."
                                }
                            ],
                            "isError": True
                        }
                    }
                cargo_id = args.get("cargo_id")
                analysis = self.gemini_client.analyze_multimodal_cargo(image_base64=img_b64, cargo_id=cargo_id)
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
            logger.error(f"Execution failed for tool '{tool_name}': {e}", exc_info=True)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Tool execution failed: {str(e)}"
                        }
                    ],
                    "isError": True
                }
            }

    def _read_resource(self, req_id: Any, uri: str) -> Dict[str, Any]:
        if uri == "fleet://status":
            raw_data = self.controller.get_state().get("vehicles", [])
        elif uri == "depots://list":
            raw_data = [d.to_dict() for d in self.controller.depots.values()]
        elif uri == "orders://open":
            raw_data = [o.to_dict() for o in self.controller.orders]
        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32602,
                    "message": f"Resource URI not found: '{uri}'"
                }
            }
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(raw_data, indent=2)
                    }
                ]
            }
        }

    def _get_prompt(self, req_id: Any, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        if name == "dispatcher_briefing":
            v_count = len(self.controller.vehicles)
            o_count = len(self.controller.orders)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "description": "Tactical Dispatcher Morning Operational Briefing",
                    "messages": [
                        {
                            "role": "user",
                            "content": {
                                "type": "text",
                                "text": f"Summarize current logistics operational readiness. There are {v_count} active fleet assets and {o_count} consignments queued. Identify bottleneck risks, EV battery charging constraints, and recommend initial swarm dispatch prioritization."
                            }
                        }
                    ]
                }
            }
        elif name == "disruption_postmortem":
            inc_type = args.get("incident_type", "unspecified supply chain crisis")
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "description": "Disruption Recovery & Root Cause Analysis",
                    "messages": [
                        {
                            "role": "user",
                            "content": {
                                "type": "text",
                                "text": f"Analyze the recent logistics disruption: '{inc_type}'. Review recovery steps executed by the multi-agent swarm, audit SLA penalty exposure, and detail preventive fleet routing safeguards."
                            }
                        }
                    ]
                }
            }
        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32602,
                    "message": f"Prompt '{name}' not found"
                }
            }

    def run_stdio(self):
        """Standard IO server loop for MCP client integrations."""
        for line in sys.stdin:
            line_str = line.strip()
            if not line_str:
                continue
            try:
                req = json.loads(line_str)
            except Exception as e:
                err = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": f"Parse error: {e}"}
                }
                sys.stdout.write(json.dumps(err) + "\n")
                sys.stdout.flush()
                continue

            resp = self.handle_request(req)
            if resp is not None:
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()
