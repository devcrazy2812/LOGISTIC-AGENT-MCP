import json
import os
import mimetypes
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Optional
from .swarm_controller import SwarmController
from ..mcp.logistics_mcp_server import LogisticsMCPServer

class LogisticsAPIHandler(BaseHTTPRequestHandler):
    controller: Optional[SwarmController] = None
    mcp_server: Optional[LogisticsMCPServer] = None
    web_dir: str = ""

    def _set_headers(self, status_code: int = 200, content_type: str = "application/json"):
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/state":
            self._set_headers(200, "application/json")
            state = self.controller.get_state()
            self.wfile.write(json.dumps(state).encode("utf-8"))
            return

        elif path == "/api/export":
            self._set_headers(200, "text/plain; charset=utf-8")
            report = self.controller.export_report()
            self.wfile.write(report.encode("utf-8"))
            return

        elif path == "/api/mcp/tools":
            self._set_headers(200, "application/json")
            tools = self.mcp_server.TOOLS
            self.wfile.write(json.dumps({"tools": tools}).encode("utf-8"))
            return

        # Serve static web files
        if path == "/" or path == "":
            file_path = os.path.join(self.web_dir, "index.html")
        else:
            clean_path = path.lstrip("/")
            file_path = os.path.join(self.web_dir, clean_path)

        if os.path.exists(file_path) and os.path.isfile(file_path):
            mime_type, _ = mimetypes.guess_type(file_path)
            mime_type = mime_type or "application/octet-stream"
            if file_path.endswith(".js"):
                mime_type = "application/javascript"
            elif file_path.endswith(".css"):
                mime_type = "text/css"

            try:
                with open(file_path, "rb") as f:
                    content = f.read()
                self._set_headers(200, mime_type)
                self.wfile.write(content)
            except Exception as e:
                self._set_headers(500, "text/plain")
                self.wfile.write(f"Server Error: {e}".encode("utf-8"))
        else:
            self._set_headers(404, "application/json")
            self.wfile.write(json.dumps({"error": "Not Found"}).encode("utf-8"))

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        content_len = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_len) if content_len > 0 else b"{}"

        try:
            body = json.loads(post_body.decode("utf-8")) if post_body else {}
        except Exception:
            body = {}

        if path == "/api/optimize":
            res = self.controller.run_initial_optimization()
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps({
                "status": "success",
                "message": "Optimization completed with Feedback Loop validation.",
                "data": self.controller.get_state()
            }).encode("utf-8"))

        elif path == "/api/disruption":
            dtype = body.get("type", "breakdown")
            custom_params = body.get("custom_params")
            res = self.controller.inject_disruption(dtype, custom_params)
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps({
                "status": "success",
                "message": f"Disruption injected: {dtype}. Autonomous recovery completed.",
                "data": self.controller.get_state()
            }).encode("utf-8"))

        elif path == "/api/chat":
            message = body.get("message", "")
            chat_res = self.controller.chat_with_agent(message)
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps({
                "status": "success",
                "data": chat_res
            }).encode("utf-8"))

        elif path == "/api/inspect_cargo":
            img_b64 = body.get("image_base64")
            analysis = self.controller.inspect_cargo_multimodal(image_base64=img_b64)
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps({
                "status": "success",
                "data": analysis
            }).encode("utf-8"))

        elif path == "/api/feedback":
            rating = body.get("rating", "positive")
            comment = body.get("comment", "")
            fb = self.controller.record_human_feedback(rating, comment)
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps({
                "status": "success",
                "message": "Human feedback recorded by Evaluator agent.",
                "data": fb
            }).encode("utf-8"))

        elif path == "/api/mcp":
            # Standard JSON-RPC 2.0 endpoint for MCP over HTTP
            resp = self.mcp_server.handle_request(body)
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps(resp).encode("utf-8"))

        elif path == "/api/reset":
            self.controller.reset()
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps({
                "status": "success",
                "message": "Swarm state reset to baseline scenario.",
                "data": self.controller.get_state()
            }).encode("utf-8"))

        else:
            self._set_headers(404, "application/json")
            self.wfile.write(json.dumps({"error": "Endpoint not recognized"}).encode("utf-8"))

    def log_message(self, format, *args):
        return

def run_server(port: int = 8000, host: str = "127.0.0.1") -> ThreadingHTTPServer:
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    web_dir = os.path.join(base_dir, "web")
    
    controller = SwarmController()
    controller.run_initial_optimization()

    mcp_server = LogisticsMCPServer(controller=controller)

    LogisticsAPIHandler.controller = controller
    LogisticsAPIHandler.mcp_server = mcp_server
    LogisticsAPIHandler.web_dir = web_dir

    server = ThreadingHTTPServer((host, port), LogisticsAPIHandler)
    return server
