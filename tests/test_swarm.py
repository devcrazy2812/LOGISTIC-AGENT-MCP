import unittest
from src.core.swarm_controller import SwarmController
from src.mcp.logistics_mcp_server import LogisticsMCPServer

class TestLogiSwarm(unittest.TestCase):
    def setUp(self):
        self.controller = SwarmController()
        self.controller.run_initial_optimization()
        self.mcp_server = LogisticsMCPServer(controller=self.controller)

    def test_initial_dispatch_with_feedback_loop(self):
        state = self.controller.get_state()
        self.assertGreater(len(state["vehicles"]), 0)
        self.assertGreater(len(state["orders"]), 0)
        self.assertEqual(state["metrics"]["sla_compliance_rate"], 100.0)
        self.assertIn("composite_score", state["latest_feedback"])

    def test_breakdown_recovery(self):
        res = self.controller.inject_disruption("breakdown")
        self.assertEqual(res["status"], "RECOVERED")
        self.assertEqual(self.controller.recovery_count, 1)

    def test_multimodal_cargo_inspection(self):
        res = self.controller.inspect_cargo_multimodal()
        self.assertIn("analysis", res)
        self.assertIn("damage_severity", res["analysis"])

    def test_conversation_agent_dialogue(self):
        res = self.controller.chat_with_agent("What is the status of the EV fleet?")
        self.assertIn("reply", res)
        self.assertTrue(len(res["reply"]) > 10)

    def test_human_feedback_recording(self):
        fb = self.controller.record_human_feedback("positive", "Great route optimization")
        self.assertEqual(fb["type"], "positive")

    def test_mcp_server_protocol(self):
        # 1. Initialize
        init_res = self.mcp_server.handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        self.assertEqual(init_res["result"]["serverInfo"]["name"], "LogiSwarm-MCP-Server")

        # 2. List Tools
        tools_res = self.mcp_server.handle_request({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        tools = tools_res["result"]["tools"]
        tool_names = [t["name"] for t in tools]
        self.assertIn("get_fleet_status", tool_names)
        self.assertIn("inspect_cargo_multimodal", tool_names)
        self.assertIn("evaluate_feedback_loop", tool_names)

        # 3. Call Tool
        call_res = self.mcp_server.handle_request({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "get_fleet_status", "arguments": {}}
        })
        self.assertIn("content", call_res["result"])

    def test_audit_report_generation(self):
        report = self.controller.export_report()
        self.assertIn("LogiSwarm AI", report)
        self.assertIn("Feedback Loop & Quality Critique", report)

if __name__ == "__main__":
    unittest.main()
