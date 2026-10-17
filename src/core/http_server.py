import json
import os
import time
import mimetypes
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from typing import Optional, Dict
from .swarm_controller import SwarmController
from ..mcp.logistics_mcp_server import LogisticsMCPServer

# In-memory IP rate limiter: {ip: [timestamp1, timestamp2, ...]}
RATE_LIMIT_STORE: Dict[str, list] = {}
MAX_REQUESTS_PER_MINUTE = 90

class LogisticsAPIHandler(BaseHTTPRequestHandler):
    controller: Optional[SwarmController] = None
    mcp_server: Optional[LogisticsMCPServer] = None
    web_dir: str = ""

    def _apply_security_headers(self, status_code: int = 200, content_type: str = "application/json", is_static: bool = False):
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Requested-With")
        
        # Security & Privacy Headers (Points 3, 4)
        self.send_header("Strict-Transport-Security", "max-age=31536000; includeSubDomains; preload")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("Permissions-Policy", "geolocation=(), camera=(), microphone=()")
        self.send_header("Content-Security-Policy", 
                         "default-src 'self'; "
                         "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://unpkg.com; "
                         "style-src 'self' 'unsafe-inline' https://unpkg.com; "
                         "img-src 'self' data: https://*.tile.openstreetmap.org https://unpkg.com; "
                         "connect-src 'self'; font-src 'self' https: data:;")

        # Cache-Control: Fast caching for static assets (Point 12)
        if is_static:
            self.send_header("Cache-Control", "public, max-age=86400, stale-while-revalidate=3600")
        else:
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")

        self.end_headers()

    def _check_rate_limit(self) -> bool:
        """Spam / Bot Protection Rate Limiter (Point 18)."""
        client_ip = self.client_address[0] if self.client_address else "unknown"
        now = time.time()
        timestamps = RATE_LIMIT_STORE.get(client_ip, [])
        # Filter timestamps within the last 60 seconds
        timestamps = [t for t in timestamps if now - t < 60]
        if len(timestamps) >= MAX_REQUESTS_PER_MINUTE:
            return False
        timestamps.append(now)
        RATE_LIMIT_STORE[client_ip] = timestamps
        return True

    def do_OPTIONS(self):
        self._apply_security_headers(200)

    def do_GET(self):
        # Force HTTPS redirect if behind TLS termination proxy (Point 4)
        proto = self.headers.get("X-Forwarded-Proto", "https")
        if proto == "http":
            host = self.headers.get("Host", "localhost")
            self.send_response(301)
            self.send_header("Location", f"https://{host}{self.path}")
            self.end_headers()
            return

        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/state":
            self._apply_security_headers(200, "application/json")
            state = self.controller.get_state()
            self.wfile.write(json.dumps(state).encode("utf-8"))
            return

        elif path == "/api/export":
            self._apply_security_headers(200, "text/plain; charset=utf-8")
            report = self.controller.export_report()
            self.wfile.write(report.encode("utf-8"))
            return

        elif path == "/api/mcp/tools":
            self._apply_security_headers(200, "application/json")
            tools = self.mcp_server.TOOLS
            self.wfile.write(json.dumps({"tools": tools}).encode("utf-8"))
            return

        # Serve static web files & SEO resources (sitemap, robots, favicon)
        if path in ("", "/"):
            file_path = os.path.join(self.web_dir, "index.html")
        else:
            clean_path = path.lstrip("/")
            file_path = os.path.join(self.web_dir, clean_path)

        if os.path.exists(file_path) and os.path.isfile(file_path):
            mime_type, _ = mimetypes.guess_type(file_path)
            mime_type = mime_type or "application/octet-stream"
            if file_path.endswith(".js"):
                mime_type = "application/javascript; charset=utf-8"
            elif file_path.endswith(".css"):
                mime_type = "text/css; charset=utf-8"
            elif file_path.endswith(".svg"):
                mime_type = "image/svg+xml"
            elif file_path.endswith(".xml"):
                mime_type = "application/xml; charset=utf-8"
            elif file_path.endswith(".txt"):
                mime_type = "text/plain; charset=utf-8"

            is_static_asset = any(file_path.endswith(ext) for ext in [".js", ".css", ".svg", ".png", ".jpg", ".ico"])
            try:
                with open(file_path, "rb") as f:
                    content = f.read()
                self._apply_security_headers(200, mime_type, is_static=is_static_asset)
                self.wfile.write(content)
            except Exception as e:
                self._apply_security_headers(500, "text/plain")
                self.wfile.write(f"Server Error: {e}".encode("utf-8"))
        else:
            # Custom 404 Page (Point 15)
            custom_404_path = os.path.join(self.web_dir, "404.html")
            if os.path.exists(custom_404_path):
                with open(custom_404_path, "rb") as f:
                    content = f.read()
                self._apply_security_headers(404, "text/html; charset=utf-8")
                self.wfile.write(content)
            else:
                self._apply_security_headers(404, "application/json")
                self.wfile.write(json.dumps({"error": "Resource Not Found"}).encode("utf-8"))

    def do_POST(self):
        if not self._check_rate_limit():
            self._apply_security_headers(429, "application/json")
            self.wfile.write(json.dumps({"error": "Too Many Requests. Rate limit exceeded."}).encode("utf-8"))
            return

        parsed = urlparse(self.path)
        path = parsed.path
        content_len = int(self.headers.get("Content-Length", 0))
        
        # Max payload size guard (2MB) (Point 18)
        if content_len > 2 * 1024 * 1024:
            self._apply_security_headers(413, "application/json")
            self.wfile.write(json.dumps({"error": "Payload Too Large"}).encode("utf-8"))
            return

        post_body = self.rfile.read(content_len) if content_len > 0 else b"{}"

        try:
            body = json.loads(post_body.decode("utf-8")) if post_body else {}
        except Exception:
            body = {}

        # Bot / Spam Honeypot Check (Point 18)
        if body.get("hp_field"):
            self._apply_security_headers(400, "application/json")
            self.wfile.write(json.dumps({"error": "Automated submission rejected"}).encode("utf-8"))
            return

        if path == "/api/optimize":
            res = self.controller.run_initial_optimization()
            self._apply_security_headers(200, "application/json")
            self.wfile.write(json.dumps({
                "status": "success",
                "message": "Optimization completed with Feedback Loop validation.",
                "data": self.controller.get_state()
            }).encode("utf-8"))

        elif path == "/api/disruption":
            dtype = str(body.get("type", "breakdown"))[:50]
            custom_params = body.get("custom_params")
            res = self.controller.inject_disruption(dtype, custom_params)
            self._apply_security_headers(200, "application/json")
            self.wfile.write(json.dumps({
                "status": "success",
                "message": f"Disruption injected: {dtype}. Autonomous recovery completed.",
                "data": self.controller.get_state()
            }).encode("utf-8"))

        elif path == "/api/chat":
            # Form Validation & Sanitization (Point 17)
            raw_msg = str(body.get("message", "")).strip()
            if not raw_msg or len(raw_msg) < 2:
                self._apply_security_headers(400, "application/json")
                self.wfile.write(json.dumps({"error": "Message must be at least 2 characters long."}).encode("utf-8"))
                return
            if len(raw_msg) > 600:
                raw_msg = raw_msg[:600]

            chat_res = self.controller.chat_with_agent(raw_msg)
            self._apply_security_headers(200, "application/json")
            self.wfile.write(json.dumps({
                "status": "success",
                "data": chat_res
            }).encode("utf-8"))

        elif path == "/api/inspect_cargo":
            img_b64 = body.get("image_base64")
            analysis = self.controller.inspect_cargo_multimodal(image_base64=img_b64)
            self._apply_security_headers(200, "application/json")
            self.wfile.write(json.dumps({
                "status": "success",
                "data": analysis
            }).encode("utf-8"))

        elif path == "/api/feedback":
            # Form Validation (Point 17)
            rating = str(body.get("rating", "positive"))[:20]
            comment = str(body.get("comment", ""))[:300]
            fb = self.controller.record_human_feedback(rating, comment)
            self._apply_security_headers(200, "application/json")
            self.wfile.write(json.dumps({
                "status": "success",
                "message": "Human feedback recorded by Evaluator agent.",
                "data": fb
            }).encode("utf-8"))

        elif path == "/api/analytics":
            # Analytics Ingestion (Point 19)
            # Lightweight privacy-friendly logging
            self._apply_security_headers(200, "application/json")
            self.wfile.write(json.dumps({"status": "received"}).encode("utf-8"))

        elif path == "/api/mcp":
            resp = self.mcp_server.handle_request(body)
            self._apply_security_headers(200, "application/json")
            self.wfile.write(json.dumps(resp).encode("utf-8"))

        elif path == "/api/reset":
            self.controller.reset()
            self._apply_security_headers(200, "application/json")
            self.wfile.write(json.dumps({
                "status": "success",
                "message": "Swarm state reset to baseline scenario.",
                "data": self.controller.get_state()
            }).encode("utf-8"))

        else:
            self._apply_security_headers(404, "application/json")
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
