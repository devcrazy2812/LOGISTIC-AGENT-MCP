import unittest
from src.core.swarm_controller import SwarmController
from src.mcp.logistics_mcp_server import LogisticsMCPServer
from src.tools.security import (
    generate_totp_secret, generate_totp_code, verify_totp_code,
    generate_channel_token, verify_channel_token,
    encrypt_sensitive_field, decrypt_sensitive_field,
    SecurityAuditLogger
)

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
        init_res = self.mcp_server.handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        self.assertEqual(init_res["result"]["serverInfo"]["name"], "LogiSwarm-MCP-Server")

        tools_res = self.mcp_server.handle_request({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        tools = tools_res["result"]["tools"]
        tool_names = [t["name"] for t in tools]
        self.assertIn("get_fleet_status", tool_names)
        self.assertIn("inspect_cargo_multimodal", tool_names)
        self.assertIn("evaluate_feedback_loop", tool_names)

        call_res = self.mcp_server.handle_request({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "get_fleet_status", "arguments": {}}
        })
        self.assertIn("content", call_res["result"])

    def test_totp_rfc6238_authentication(self):
        """Blueprint 2.E: Two-Factor Authentication Verification."""
        secret = generate_totp_secret()
        self.assertEqual(len(secret), 16)
        code = generate_totp_code(secret)
        self.assertEqual(len(code), 6)
        self.assertTrue(verify_totp_code(secret, code))
        self.assertFalse(verify_totp_code(secret, "000000" if code != "000000" else "999999"))

    def test_signed_channel_tokens(self):
        """Blueprint 2.F: Ephemeral HMAC-SHA256 Signed Access Tokens."""
        token = generate_channel_token("DISPATCHER-01", "CHIEF", "FLEET_COMMAND", expiry_seconds=60)
        valid, data = verify_channel_token(token, "FLEET_COMMAND")
        self.assertTrue(valid)
        self.assertEqual(data["user_id"], "DISPATCHER-01")

        # Tampered or wrong action fails
        invalid, _ = verify_channel_token(token, "UNAUTHORIZED_ACTION")
        self.assertFalse(invalid)

    def test_field_level_encryption(self):
        """Blueprint 3.B: Sensitive PII Field Encryption."""
        secret_address = "402 Apollo Medical Complex, Cold-Storage Dock 4B"
        encrypted = encrypt_sensitive_field(secret_address)
        self.assertNotEqual(secret_address, encrypted)
        decrypted = decrypt_sensitive_field(encrypted)
        self.assertEqual(secret_address, decrypted)

    def test_administrative_database_backups(self):
        """Blueprint 3.E: Administrative Multi-Format Backups."""
        json_backup = self.controller.export_database_backup(format_type="json")
        self.assertIn("vehicles", json_backup)
        csv_backup = self.controller.export_database_backup(format_type="csv")
        self.assertIn("Entity,ID,Name_or_Customer", csv_backup)

    def test_trajectory_and_audit_logging(self):
        """Blueprint 3.D & 4.B: Trajectory Tracking and Audit Logging."""
        state = self.controller.get_state()
        self.assertIn("trajectory", state)
        self.assertIn("audit_logs", state)
        self.assertGreater(len(state["trajectory"]), 0)

if __name__ == "__main__":
    unittest.main()
