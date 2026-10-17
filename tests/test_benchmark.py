import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.benchmark import BenchmarkHarness


class TestBenchmarkHarness(unittest.TestCase):
    def test_01_benchmark_execution(self):
        """Test that benchmark harness executes all scenarios and generates valid metrics."""
        results = BenchmarkHarness.run_benchmark()
        self.assertIn("scenarios", results)
        self.assertIn("summary", results)

        for sc in BenchmarkHarness.SCENARIOS:
            self.assertIn(sc, results["scenarios"])
            sc_data = results["scenarios"][sc]
            self.assertIn("static_baseline", sc_data)
            self.assertIn("logiswarm_swarm", sc_data)
            self.assertGreaterEqual(sc_data["logiswarm_swarm"]["sla_adherence_pct"], 0.0)

        summary = results["summary"]
        self.assertIn("total_static_penalty_usd", summary)
        self.assertIn("total_swarm_penalty_usd", summary)
        self.assertIn("sla_penalty_mitigated_pct", summary)
        self.assertIn("average_swarm_mttr_seconds", summary)

    def test_02_format_table(self):
        """Test formatting benchmark results into table output."""
        results = BenchmarkHarness.run_benchmark()
        table = BenchmarkHarness.format_table(results)
        self.assertIn("LOGISWARM AI: AUTONOMOUS SWARM VS STATIC DISPATCH BENCHMARK", table)
        self.assertIn("EXECUTIVE SUMMARY", table)
        self.assertIn("breakdown", table)


if __name__ == "__main__":
    unittest.main()
