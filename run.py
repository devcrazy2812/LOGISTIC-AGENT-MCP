import os
import sys
import webbrowser
import threading
import socket
from src.core.http_server import run_server

BANNER = r"""
========================================================================
   __               _  ____                                       ___   ____ 
  / /  ___   ____ _(_)/ __/ _      __ ___ _ ____ ___        /\   |_ _| / __/ 
 / /__/ _ \ / _ `/ / _\ \ | | /| / // _ `// __// _ \      /  \   | | _\ \   
/____/\___//\_, /_/ /___/ | |/ |/ //\_,_//_/  /___/      / /\ \ |___//___/   
          /___/                                         / /__\ \             
  AUTONOMOUS MULTI-AGENT LOGISTICS & SUPPLY CHAIN SWARM
  AI Agent Wars Edition - 2026
========================================================================
"""

def find_available_port(start_port: int = 8000, max_attempts: int = 20) -> int:
    """Finds an available local port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return start_port

def main():
    print(BANNER)
    port = find_available_port(8000)
    url = f"http://127.0.0.1:{port}"

    print(f"[*] Initializing Multi-Agent Swarm Controller...")
    print(f"[*] Agents Loaded:")
    print(f"    - Commander-Prime (Master Orchestrator)")
    print(f"    - Sentinel-Risk (Disruption & Telematics Radar)")
    print(f"    - StockMaster (Multi-Depot Inventory Allocator)")
    print(f"    - RouteOptima (CVRP Fleet & Route Specialist)")
    print(f"    - CommLiaison (Customer SLA & Carrier Negotiator)")
    print()
    print(f"[+] Starting Mission Control Web Dashboard at: {url}")
    print(f"[+] Press Ctrl+C in this terminal to stop the server.")
    print("=" * 72)

    server = run_server(port=port)

    # Automatically launch browser in a thread after 1 second
    def open_browser():
        webbrowser.open(url)

    threading.Timer(1.0, open_browser).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Shutting down Logistics Swarm Server safely. Goodbye!")
        server.shutdown()
        sys.exit(0)

if __name__ == "__main__":
    main()
