#!/usr/bin/env python3
"""
LogiSwarm AI - Benchmark Simulation Runner
Compares Static Nearest-Neighbor Routing against the Autonomous Multi-Agent Swarm
across nominal and stochastic supply chain disruption scenarios.

Usage:
  python benchmark.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.tools.benchmark import BenchmarkHarness


def main():
    print("[*] Running LogiSwarm AI Multi-Scenario Benchmark Harness...\n")
    results = BenchmarkHarness.run_benchmark()
    print(BenchmarkHarness.format_table(results))


if __name__ == "__main__":
    main()
