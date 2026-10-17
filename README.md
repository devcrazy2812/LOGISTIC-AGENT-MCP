# 📦 LogiSwarm AI: Autonomous Logistics Handler
### *Multi-Agent Swarm with Multimodal Vision, Conversational Dispatch, MCP, & Self-Healing Feedback Loops*
**Competition:** AI Agent Wars 2026 | **Problem Statement:** Logistics Handler

---

## 📑 Table of Contents
1. [Overview & Problem Statement](#-overview--problem-statement)
2. [Compliance with Competition Criteria](#-compliance-with-competition-criteria)
3. [System Architecture](#-system-architecture)
4. [Tool Sets & Google Products Integration](#-tool-sets--google-products-integration)
5. [A-to-Z Step-by-Step Setup Guide](#-a-to-z-step-by-step-setup-guide)
6. [How to Run the Application](#-how-to-run-the-application)
7. [MCP (Model Context Protocol) Integration](#-mcp-model-context-protocol-integration)
8. [Live Demo Walkthrough for Judges](#-live-demo-walkthrough-for-judges)
9. [How to Submit & Push to GitHub](#-how-to-submit--push-to-github)

---

## 🎯 Overview & Problem Statement

Global logistics networks frequently suffer catastrophic bottlenecks when static, rule-based dispatchers encounter real-world chaos: traffic gridlocks, highway washouts, vehicle mechanical failures, cold-chain temperature breaches, and emergency priority surges.

**LogiSwarm AI** is an enterprise-grade autonomous multi-agent logistics orchestrator. A swarm of specialized AI agents autonomously monitors telematics, balances multi-depot inventory, inspects cargo with multimodal vision, converses with human dispatchers, audits route quality via continuous feedback loops, and self-heals disruptions in under 2 seconds.

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

### The 6 Swarm Agents
1. **Commander-Prime (Master Orchestrator)**: Manages global mission state, delegates sub-tasks, and resolves multi-objective trade-offs.
2. **Sentinel-Risk (Anomaly & Hazard Radar)**: Continuously monitors telematics, road closures, and weather warnings. Triggers self-healing when disruptions occur.
3. **StockMaster (Warehouse & Inventory Specialist)**: Audits multi-depot stock, allocates orders, and schedules inter-warehouse transfers.
4. **RouteOptima (Fleet & Routing Specialist)**: Solves Capacitated Vehicle Routing (CVRP) with priority deadlines, weight/volume constraints, and electric vehicle (EV) emission minimization.
5. **QualityGuard (Evaluator-Optimizer & Feedback Loop)**: Scores route plans on SLA safety, carbon abatement, and load balance. Triggers iterative plan refinement.
6. **CommLiaison (Customer SLA & Carrier Negotiator)**: Formulates customer delay notifications, protects contractual SLAs, issues courtesy compensation credits, and simulates spot-carrier bidding.

---

## 🛠️ Tool Sets & Google Products Integration

- **Google Gemini 2.5 Flash**: Powering the Multimodal Cargo Inspector (detecting physical box puncture, temperature breach, and estimated insurance liability) and the interactive Conversation Agent.
- **Model Context Protocol (MCP)**: Native JSON-RPC 2.0 tool server compatible with Claude Desktop, Cursor, Antigravity, and custom LLM sidecars.
- **Geo-Spatial Routing Solver**: Haversine distance matrix with 2-Opt local search refinement.

---

## 💻 A-to-Z Step-by-Step Setup Guide

### Prerequisites
- Python 3.9 or higher (tested on Python 3.10, 3.11, 3.12, 3.14)
- Web Browser (Chrome, Edge, Firefox, Brave)
- *Optional:* Google Gemini API Key (if omitted, the system seamlessly runs in embedded high-fidelity offline mode so your live demo never fails).

---

## 🚀 How to Run the Application

### Method 1: Windows Double-Click (Zero Setup)
Double-click [`start_app.bat`](start_app.bat) in the project root.

### Method 2: From Terminal / PowerShell
```bash
# Navigate to the project directory
cd C:\Users\ABHAY\LogisticsHandlerAI

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
*(All 7 unit tests pass in $<0.01$ seconds!)*

---

## 🔌 MCP (Model Context Protocol) Integration

LogiSwarm includes a built-in MCP server that implements the standard **JSON-RPC 2.0** protocol.

### Run MCP Server via stdio
```bash
python mcp_server.py
```

### Example MCP Configuration for Claude Desktop / Antigravity / Cursor
Add this to your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "logiswarm": {
      "command": "python",
      "args": ["C:\\Users\\ABHAY\\LogisticsHandlerAI\\mcp_server.py"]
    }
  }
}
```

### Exposed MCP Tools:
- `get_fleet_status`: Returns telematics, battery/fuel levels, and active route stops.
- `optimize_cvrp_routes`: Executes multi-agent Capacitated Vehicle Routing.
- `inject_disruption`: Simulates breakdown, weather hazard, or demand surge.
- `inspect_cargo_multimodal`: Runs Google Gemini Vision analysis on cargo photos.
- `evaluate_feedback_loop`: Audits solution quality and returns feedback loop scores.

---

## 🎭 Live Demo Walkthrough for Judges

Follow this exact 3-minute sequence to demonstrate all required criteria:

1. **Nominal Swarm Overview (30s)**:
   - Point out the 3 Regional Depots, 4 Fleet Vehicles (EV, Diesel, CNG, Reefer), and 8 Deliveries on the interactive map.
   - Point to the **Feedback Score Card (`92.5/100`)**: Explain that `QualityGuard` evaluated SLA risk, carbon footprint, and load balance before approving dispatch.
2. **Conversation Agent Tab (45s)**:
   - Click the **Conversation Agent** tab in the right pane.
   - Type: *"What is the status of VoltHauler EV?"*
   - Watch `Commander-Prime` reply with real-time telematics and cargo status.
3. **Multimodal Vision Tab (45s)**:
   - Click the **Multimodal Vision** tab.
   - Click **"Inspect Sample Damaged Vaccine Pallet"**.
   - Show Google Gemini Vision diagnosing container puncture, temperature breach ($>8^\circ\text{C}$), insurance estimate (\$1,450), and auto-dispatching replacement stock from Hub-North.
4. **Self-Healing Disruption Trigger (45s)**:
   - Click **"Truck Breakdown"** in the Disruption Simulator.
   - Watch the Swarm War Room Feed:
     - `Sentinel-Risk` flags the engine failure.
     - `RouteOptima` unassigns affected deliveries and re-routes them onto backup vehicles.
     - `CommLiaison` broadcasts real-time courtesy credits to customers.
   - The map dynamically updates and the **Self-Healed Events** metric increments with zero manual dispatch.
5. **Human Feedback & Audit Export (15s)**:
   - Click **"Prioritize Green"** in the Human Dispatcher Feedback bar.
   - Click **"Audit Report"** to copy the complete markdown execution audit.

---

## 📤 How to Submit & Push to GitHub

This repository is pre-initialized and ready to be pushed to your GitHub account:

```bash
cd C:\Users\ABHAY\LogisticsHandlerAI

# 1. Add your GitHub repository as remote origin (replace with your repo URL)
git remote add origin https://github.com/<YOUR_USERNAME>/<YOUR_REPOSITORY_NAME>.git

# 2. Stage and commit all files
git add .
git commit -m "feat: complete LogiSwarm AI logistics handler for AI Agent Wars"

# 3. Rename branch to main (if needed) and push
git branch -M main
git push -u origin main
```

Share your GitHub link with the competition organizers to secure your submission!
