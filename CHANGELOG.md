# Changelog

All notable changes to the **LogiSwarm AI** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.0] - 2026-10-17

### Added
- **Dual MCP Protocol Specification Support**: Implemented dual-mode server supporting both modern MCP 2026-07-28 (`server/discover`, per-request `_meta` protocol verification) and legacy MCP 2024-11-05 (`initialize` handshake).
- **MCP Resources**: Added `fleet://status`, `depots://list`, and `orders://open` with full JSON payload retrieval via `resources/read`.
- **MCP Prompts**: Added `dispatcher_briefing` and `disruption_postmortem` prompt templates via `prompts/get`.
- **MCP Annotations & Mutation Controls**: Annotated all tools with `readOnlyHint`, `destructiveHint`, and `idempotentHint`. Added `dry_run: bool = False` argument to `inject_disruption`.
- **Cryptographic Hash-Chained Audit Ledger**: Upgraded `SecurityAuditLogger` to build an immutable, tamper-evident hash chain linking each entry to its predecessor. Added `verify_chain()` verification engine.
- **Authenticated PII Encryption**: Upgraded field-level encryption to Encrypt-then-MAC (PBKDF2 100k rounds + HMAC-SHA256 authentication tag).
- **TOTP Replay Protection**: Added time-step cache `_TOTP_REPLAY_CACHE` to prevent replay attacks within drift tolerance windows.
- **Enterprise UI/UX Modernization**: Redesigned front-end with clean typography (Inter / JetBrains Mono), CartoDB Dark Matter map styling, drag-and-drop cargo vision upload, and toast notifications.
- **End-to-End Test Suites**: Added `tests/test_mcp_server.py`, `tests/test_mcp_protocol.py`, `tests/test_gemini_client.py`, and `tests/test_security.py` bringing test coverage to 41 passing tests.

### Fixed
- Fixed missing `Optional` import and circular import deadlock in `src/mcp/logistics_mcp_server.py`.
- Replaced hardcoded `gemini-2.5-flash` URL with configurable `GEMINI_MODEL` environment variable.
- Relocated Gemini API keys from URL query parameters to `x-goog-api-key` HTTP header.
- Replaced fragile JSON string sniffing with Gemini structured schema output (`responseMimeType: "application/json"`, `responseSchema`).
- Added magic-byte image MIME detection (JPEG, PNG, WebP) and 5MB payload limit.
- Replaced silent exception swallowing with exponential backoff retries and structured stderr logging.
- Secured `/api/admin/backup` endpoint with signed channel token verification.

---

## [1.0.0] - 2026-10-15

### Added
- Initial release of LogiSwarm multi-agent transportation management system.
- Capacitated Vehicle Routing Problem (CVRP) solver with 2-Opt local search.
- Six specialized autonomous agents: `Commander-Prime`, `Sentinel-Risk`, `StockMaster`, `RouteOptima`, `CommLiaison`, and `QualityGuard`.
- Multimodal optical cargo diagnostic vision analyzer.
- Standard-library RFC 6238 TOTP two-factor authentication.
- Single-page application dashboard with interactive Leaflet map and mission report generation.
