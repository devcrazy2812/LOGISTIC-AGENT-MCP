# 📦 LogiSwarm AI: Autonomous Logistics Handler
### *Multi-Agent Swarm with Multimodal Vision, Conversational Dispatch, MCP, & Self-Healing Feedback Loops*
**Competition:** AI Agent Wars 2026 | **Problem Statement:** Logistics Handler  
**Engineering Standard:** Universal Full-Stack & AI Engineering Master Blueprint

---

## 📑 Table of Contents
1. [Overview & Problem Statement](#-overview--problem-statement)
2. [Compliance with Competition Criteria](#-compliance-with-competition-criteria)
3. [Master Blueprint Engineering Upgrades](#-master-blueprint-engineering-upgrades)
4. [System Architecture](#-system-architecture)
5. [Tool Sets & Google Products Integration](#-tool-sets--google-products-integration)
6. [A-to-Z Step-by-Step Setup Guide](#-a-to-z-step-by-step-setup-guide)
7. [How to Run the Application](#-how-to-run-the-application)
8. [MCP (Model Context Protocol) Integration](#-mcp-model-context-protocol-integration)
9. [Live Demo Walkthrough for Judges](#-live-demo-walkthrough-for-judges)
10. [How to Submit & Push to GitHub](#-how-to-submit--push-to-github)

---

## 🎯 Overview & Problem Statement

Global logistics networks frequently suffer catastrophic bottlenecks when static, rule-based dispatchers encounter real-world chaos: traffic gridlocks, highway washouts, vehicle mechanical failures, cold-chain temperature breaches, and emergency priority surges.

**LogiSwarm AI** is an enterprise-grade autonomous multi-agent logistics orchestrator. A swarm of specialized AI agents autonomously monitors telematics, balances multi-depot inventory, inspects cargo with multimodal vision, converses with human dispatchers, audits route quality via continuous feedback loops, and self-heals disruptions in under 2 seconds.

---

## 🛡️ Master Blueprint Engineering Upgrades

Our system adheres strictly to the **Universal Full-Stack & AI Engineering Master Blueprint**:

### 1. UI / UX Architecture
- **macOS-Style Floating Bottom Dock with Scroll Auto-Hide**: Route navigation is centered in a glassmorphic floating bottom dock that hides when scrolling down and reveals when scrolling up or moving the cursor to the bottom viewport edge.
- **Clean Uncluttered Top Bar**: Left side features institutional brand identity; right side houses live clock, 2FA status, printable official report CTA, and the primary "Deploy Swarm" action.
- **Decoupled Floating AI Agent Drawer**: Ambient floating action button (`bottom-6 right-6`) with expandable drawer modal preserving conversation state via `sessionStorage`.
- **1-Click Official Business / Consignment PDF Dossier**: Print-ready modal dossier with standardized institutional letterhead, benchmark variance table, SVG verification QR code, and `@media print` styling (`window.print()`).
- **De-Hyped Enterprise Copy**: Removed emojis and hyperbole in favor of crisp, institutional logistics terminology.

### 2. Defensive Cybersecurity
- **Standard-Library Two-Factor Authentication (2FA / TOTP RFC 6238)**: Zero external dependencies; Google Authenticator / Authy compatible TOTP generator and validator.
- **Ephemeral HMAC-SHA256 Signed Access Tokens**: Cryptographically signed, time-limited channel tokens for mission dispatch authorizations.
- **Dynamic CORS Whitelisting with Regex**: Enforces strict origin matching against trusted development and production domains.
- **Defense-in-Depth HTTP Headers & CSP**: Injects HSTS, CSP, COOP, and `X-Frame-Options: SAMEORIGIN`.
- **Anti-Bot Honeypots & Submission Debouncing**: Invisible form honeypots and client-side 1200ms submission debouncing.
- **Defensive JSON Request Parsing**: Fails gracefully on malformed payloads or empty bodies.

### 3. Database Architecture & Data Protection
- **Field-Level PII Encryption**: Authenticated symmetric encryption for sensitive customer addresses and medical consignment notes.
- **Immutable Security Audit Logging**: Append-only SHA-256 hashed audit log tracking all dispatch events, agent decisions, and IP addresses.
- **Live Multi-Format Administrative Database Backups**: 1-click JSON and CSV database backups at `/api/admin/backup`.

### 4. AI Agent & Intelligent System Architecture
- **Three-Tier Hybrid Architecture**:
  1. *Tier 1 (Deterministic Rules Matrix)*: Evaluates cold-chain temperature boundaries ($2\text{–}8^\circ\text{C}$), vehicle compatibility, and hazmat rules (<1ms execution, 0% hallucination).
  2. *Tier 2 (Online Cloud LLM)*: Google Gemini 2.5 Flash for natural multimodal vision analysis and conversational dialogue.
  3. *Tier 3 (Verified FAQ & Semantic Fallback Bank)*: Instant, verified domain response bank when offline or without API keys.
- **Longitudinal Trajectory Analysis**: Tracks rate of change ($\Delta t$) across runs (Cost reduction velocity, CO₂ abatement velocity, MTTR recovery speed).

---

## ✅ Compliance with Competition Criteria

| Hackathon Requirement | How LogiSwarm Implements It | Source File |
| :--- | :--- | :--- |
| **1. Multi-modal Agents** | Uses **Google Gemini 2.5 Flash Multimodal Vision** to analyze photos of damaged packages, structural pallet collapses, and cold-chain thermal breaches, auto-calculating insurance liability and auto-dispatching replacements. | [`src/tools/gemini_client.py`](src/tools/gemini_client.py) |
| **2. Conversation Agents** | Interactive natural language dialogue interface between human dispatchers and **Commander-Prime** (Fleet status, rerouting directives, SLA queries). | [`src/core/http_server.py`](src/core/http_server.py) (`/api/chat`) |
| **3. API Calls** | High-throughput REST endpoints, Google Gemini Generative AI API calls, and Haversine matrix calculators. | [`src/core/http_server.py`](src/core/http_server.py) |
| **4. MCP Integration** | Full JSON-RPC 2.0 **Model Context Protocol (MCP)** server exposing tools (`get_fleet_status`, `optimize_cvrp_routes`, `inject_disruption`, `inspect_cargo_multimodal`, `evaluate_feedback_loop`). | [`src/mcp/logistics_mcp_server.py`](src/mcp/logistics_mcp_server.py), [`mcp_server.py`](mcp_server.py) |
| **5. Feedback Loop** | **QualityGuard (Evaluator-Optimizer Agent)** audits proposed plans against SLA risk, carbon footprint, and load balance. If score $<85\%$, it generates structured critique and forces route refinement. Includes Human-in-the-Loop ratings. | [`src/agents/evaluator_agent.py`](src/agents/evaluator_agent.py) |
| **6. Self-Healing Agents** | When a vehicle fails or route is cut, `Sentinel-Risk` flags the telemetry distress, unassigns compromised deliveries, and `RouteOptima` automatically bypasses hazards and re-routes without manual dispatch. | [`src/agents/sentinel_agent.py`](src/agents/sentinel_agent.py), [`src/agents/router_agent.py`](src/agents/router_agent.py) |
| **7. Google Products** | Google Gemini Generative AI, Google Maps Geo-spatial coordinates, and Google Cloud design patterns. | [`src/tools/gemini_client.py`](src/tools/gemini_client.py) |

---

## 🏛️ System Architecture

```
                                [ 🧑‍💼 Human Dispatcher / Command UI ]
                                                │
                                                ▼
                                ┌──────────────────────────────┐
                                │       Commander-Prime        │
                                │ (Master Swarm Orchestrator)  │
                                └──────┬───────────────┬───────┘
                                       │               │
                     ┌─────────────────┴───┐       ┌───┴─────────────────┐
                     │                     │       │                     │
                     ▼                     ▼       ▼                     ▼
            ┌─────────────────┐ ┌───────────────┐ ┌────────────────┐ ┌────────────────┐
            │  Sentinel-Risk  │ │  StockMaster  │ │  RouteOptima   │ │  CommLiaison   │
            │(Anomaly Radar)  │ │  (Warehouse)  │ │ (CVRP Routing) │ │(SLA Negotiator)│
            └────────┬────────┘ └───────────────┘ └───────┬────────┘ └────────────────┘
                     │                                    │
                     │         ┌───────────────────────┐  │
                     └────────>│     QualityGuard      │<─┘
                               │ (Feedback Evaluator)  │
                               └───────────────────────┘
```

---

## 💻 A-to-Z Step-by-Step Setup Guide

### Prerequisites
- Python 3.9 or higher (tested on Python 3.10, 3.11, 3.12, 3.14)
- Web Browser (Chrome, Edge, Firefox, Brave)
- *Optional:* Google Gemini API Key in `.env` (if omitted, the system seamlessly runs on its embedded offline reasoning engine so your demo never fails).

---

## 🚀 How to Run the Application

### Method 1: Windows Double-Click (Zero Setup)
Double-click [`start_app.bat`](start_app.bat) in the project root.

### Method 2: From Terminal / PowerShell
```bash
# Navigate to the project directory
cd E:\LOGISTIC AGENT MCP

# Launch the full application
python run.py
```

The script will automatically:
1. Boot the multi-threaded REST and WebSocket server.
2. Run the initial multi-agent optimization pass with the Feedback Loop.
3. Launch your browser at `http://127.0.0.1:8000`.

### Running Automated Unit Tests
```bash
python -m unittest tests/test_swarm.py
```
*(All 11 unit tests pass in $<0.05$ seconds!)*

---

## 🔌 MCP (Model Context Protocol) Integration

LogiSwarm includes a built-in MCP server that implements the standard **JSON-RPC 2.0** protocol.

### Run MCP Server via stdio
```bash
python mcp_server.py
```

---

## 🎭 Live Demo Walkthrough for Judges

1. **Nominal Swarm Overview (30s)**:
   - Point out the 3 Regional Depots, 4 Fleet Vehicles (EV, Diesel, CNG, Reefer), and 8 Deliveries on the interactive map.
   - Point to the **Feedback Score Card (`92.5/100`)**: Explain that `QualityGuard` evaluated SLA risk, carbon footprint, and load balance before approving dispatch.
2. **Conversation Agent Drawer (45s)**:
   - Click the ambient floating bot button (`bottom-6 right-6`).
   - Ask: *"What is the status of VoltHauler EV?"*
   - Watch `Commander-Prime` reply with real-time telematics and cargo status.
3. **Multimodal Vision Tab (45s)**:
   - Click the **Multimodal Vision** tab.
   - Click **"Inspect Sample Compromised Vaccine Pallet"**.
   - Show Google Gemini Vision diagnosing container puncture, temperature breach ($>8^\circ\text{C}$), insurance estimate (\$1,450), and auto-dispatching replacement stock from Hub-North.
4. **Self-Healing Disruption Trigger (45s)**:
   - Click **"Mechanical Breakdown"** in the Disruption Simulator.
   - Watch the Swarm War Room Feed:
     - `Sentinel-Risk` flags the engine failure.
     - `RouteOptima` unassigns affected deliveries and re-routes them onto backup vehicles.
     - `CommLiaison` broadcasts real-time courtesy credits to customers.
5. **Official 1-Click Dossier & 2FA (15s)**:
   - Click **"Official Dossier"** in the top bar to generate the print-ready institutional report with QR verification hash.
   - Click **"2FA Active"** to demonstrate RFC 6238 TOTP verification and signed ephemeral access tokens.

---

## 📤 GitHub Repository

```bash
cd E:\LOGISTIC AGENT MCP
git push origin main
```
Live Repo: [https://github.com/devcrazy2812/LOGISTIC-AGENT-MCP](https://github.com/devcrazy2812/LOGISTIC-AGENT-MCP)
