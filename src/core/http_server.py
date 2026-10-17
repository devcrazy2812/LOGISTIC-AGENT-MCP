import json
import os
import time
import mimetypes
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Optional, Dict
from .swarm_controller import SwarmController
from ..mcp.logistics_mcp_server import LogisticsMCPServer
from ..tools.security import (
    generate_totp_secret, generate_totp_code, verify_totp_code,
    generate_channel_token, verify_channel_token,
    SecurityAuditLogger, ALLOWED_ORIGIN_REGEX
)

RATE_LIMIT_STORE: Dict[str, list] = {}
MAX_REQUESTS_PER_MINUTE = 90
ACTIVE_2FA_STORE: Dict[str, str] = {}  # {user_id: secret}

class LogisticsAPIHandler(BaseHTTPRequestHandler):
    controller: Optional[SwarmController] = None
    mcp_server: Optional[LogisticsMCPServer] = None
    web_dir: str = ""

    def _get_client_ip(self) -> str:
        """Extracts real client IP behind proxies (Blueprint 3.D)."""
        forwarded = self.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return self.client_address[0] if self.client_address else "127.0.0.1"

    def _apply_security_headers(self, status_code: int = 200, content_type: str = "application/json", is_static: bool = False):
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        
        # Dynamic CORS Whitelisting with Regex (Blueprint 2.B)
        origin = self.headers.get("Origin", "")
        if origin and ALLOWED_ORIGIN_REGEX.match(origin):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Credentials", "true")
        else:
            self.send_header("Access-Control-Allow-Origin", "*")

        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With, X-Dispatch-Token")
        
        # Defense-in-Depth HTTP Security Headers (Blueprint 2.D)
        self.send_header("Strict-Transport-Security", "max-age=31536000; includeSubDomains; preload")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("Permissions-Policy", "geolocation=(), camera=(), microphone=()")
        self.send_header("Content-Security-Policy", 
                         "default-src 'self'; "
                         "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://unpkg.com; "
                         "style-src 'self' 'unsafe-inline' https://unpkg.com; "
                         "img-src 'self' data: blob: https://*.tile.openstreetmap.org https://unpkg.com; "
                         "connect-src 'self' http://localhost:* http://127.0.0.1:* ws: wss: https:; "
                         "font-src 'self' https: data:;")

        if is_static:
            self.send_header("Cache-Control", "public, max-age=86400, stale-while-revalidate=3600")
        else:
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")

        self.end_headers()

    def _check_rate_limit(self) -> bool:
        client_ip = self._get_client_ip()
        now = time.time()
        timestamps = RATE_LIMIT_STORE.get(client_ip, [])
        timestamps = [t for t in timestamps if now - t < 60]
        if len(timestamps) >= MAX_REQUESTS_PER_MINUTE:
            return False
        timestamps.append(now)
        RATE_LIMIT_STORE[client_ip] = timestamps
        return True

    def _parse_json_body_defensive(self) -> Dict[str, Any]:
        """Defensive JSON request parsing (Blueprint 2.H)."""
        content_len = int(self.headers.get("Content-Length", 0))
        if content_len <= 0 or content_len > 2 * 1024 * 1024:
            return {}
        try:
            raw = self.rfile.read(content_len).decode("utf-8", errors="replace")
            return json.loads(raw) if raw else {}
        except Exception:
            return {}

    def do_OPTIONS(self):
        self._apply_security_headers(200)

    def do_GET(self):
        # Force HTTPS redirect if behind TLS termination proxy (Blueprint 2.D)
        if self.headers.get("X-Forwarded-Proto") == "http":
            host = self.headers.get("Host", "localhost")
            self.send_response(301)
            self.send_header("Location", f"https://{host}{self.path}")
            self.end_headers()
            return

        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

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

        # 2FA Secret Generation (Blueprint 2.E)
        elif path == "/api/auth/2fa/generate":
            user_id = query.get("user", ["DISPATCHER-01"])[0]
            secret = generate_totp_secret()
            ACTIVE_2FA_STORE[user_id] = secret
            current_code = generate_totp_code(secret)
            self._apply_security_headers(200, "application/json")
            self.wfile.write(json.dumps({
                "status": "success",
                "user_id": user_id,
                "secret": secret,
                "preview_code": current_code,
                "message": "RFC 6238 TOTP Secret generated successfully."
            }).encode("utf-8"))
            return

        # Administrative Multi-Format Database Backup (Blueprint 3.E)
        elif path == "/api/admin/backup":
            auth_header = self.headers.get("Authorization", "")
            token = ""
            if auth_header.startswith("Bearer "):
                token = auth_header[7:].strip()
            elif "token" in query:
                token = query["token"][0].strip()

            client_ip = self._get_client_ip()
            is_local = client_ip in ("127.0.0.1", "::1", "localhost")
            is_authenticated = False

            if token:
                valid_admin, _ = verify_channel_token(token, "ADMIN_BACKUP")
                valid_cmd, _ = verify_channel_token(token, "FLEET_COMMAND")
                is_authenticated = valid_admin or valid_cmd

            if not is_authenticated:
                is_prod = os.environ.get("ENVIRONMENT", "").lower() in ("production", "prod") or os.environ.get("PRODUCTION") == "1"
                if is_prod or not is_local:
                    SecurityAuditLogger.log("DATABASE_BACKUP_UNAUTHORIZED", client_ip, "ANONYMOUS", "Rejected unauthenticated admin backup attempt")
                    self._apply_security_headers(401, "application/json")
                    self.wfile.write(json.dumps({"error": "Unauthorized: Valid signed admin token required"}).encode("utf-8"))
                    return
                else:
                    SecurityAuditLogger.log("DATABASE_BACKUP_LOCAL_DEV", client_ip, "LOCAL_DEV", "Allowed database backup on localhost dev mode")

            fmt = query.get("format", ["json"])[0]
            backup_data = self.controller.export_database_backup(format_type=fmt)
            mime = "text/csv; charset=utf-8" if fmt == "csv" else "application/json"
            self._apply_security_headers(200, mime)
            self.wfile.write(backup_data.encode("utf-8"))
            return

        # Static assets and SEO endpoints
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
            # Custom 404 handler
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
        body = self._parse_json_body_defensive()

        # Bot / Spam Honeypot Check (Blueprint 2.G)
        if body.get("hp_field"):
            SecurityAuditLogger.log("BOT_HONEYPOT_TRIGGERED", self._get_client_ip(), "ANONYMOUS_BOT", "Honeypot filled.")
            self._apply_security_headers(400, "application/json")
            self.wfile.write(json.dumps({"error": "Automated submission rejected"}).encode("utf-8"))
            return

        # 2FA Verification (Blueprint 2.E)
        if path == "/api/auth/2fa/verify":
            user_id = str(body.get("user_id", "DISPATCHER-01"))
            submitted_code = str(body.get("code", "")).strip()
            secret = ACTIVE_2FA_STORE.get(user_id) or generate_totp_secret()
            
            is_valid = verify_totp_code(secret, submitted_code)
            if is_valid:
                # Issue signed ephemeral access token
                signed_token = generate_channel_token(user_id, "CHIEF_DISPATCHER", "FLEET_COMMAND")
                SecurityAuditLogger.log("2FA_VERIFICATION_SUCCESS", self._get_client_ip(), user_id, "TOTP 2FA verified.")
                self._apply_security_headers(200, "application/json")
                self.wfile.write(json.dumps({
                    "status": "success",
                    "verified": True,
                    "access_token": signed_token,
                    "message": "Two-Factor Authentication successful."
                }).encode("utf-8"))
            else:
                SecurityAuditLogger.log("2FA_VERIFICATION_FAILURE", self._get_client_ip(), user_id, f"Invalid code: {submitted_code}")
                self._apply_security_headers(401, "application/json")
                self.wfile.write(json.dumps({
                    "status": "error",
                    "verified": False,
                    "error": "Invalid or expired 6-digit TOTP code."
                }).encode("utf-8"))
            return

        elif path == "/api/optimize":
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
            raw_msg = str(body.get("message", "")).strip()
            if not raw_msg or len(raw_msg) < 2:
                self._apply_security_headers(400, "application/json")
                self.wfile.write(json.dumps({"error": "Message must be at least 2 characters long."}).encode("utf-8"))
                return
            if len(raw_msg) > 600:
                raw_msg = raw_msg[:600]

            # Prompt injection defense: sanitize delimiters and bound within user dispatch query
            sanitized_msg = raw_msg.replace("<user_dispatch_query>", "").replace("</user_dispatch_query>", "")
            guarded_prompt = f"<user_dispatch_query>\n{sanitized_msg}\n</user_dispatch_query>"

            chat_res = self.controller.chat_with_agent(guarded_prompt)
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
            self._apply_security_headers(200, "application/json")
            self.wfile.write(json.dumps({"status": "received"}).encode("utf-8"))

        elif path == "/api/mcp":
            resp = self.mcp_server.handle_request(body)
            if resp is None:
                self._apply_security_headers(204, "application/json")
                return
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
