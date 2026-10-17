import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestMCPServer(unittest.TestCase):
    def test_00_module_import(self):
        """Test that src.mcp.logistics_mcp_server can be imported cleanly without NameError or circular import."""
        try:
            import src.mcp.logistics_mcp_server
            from src.mcp.logistics_mcp_server import LogisticsMCPServer
            self.assertTrue(hasattr(LogisticsMCPServer, "TOOLS"))
        except Exception as e:
            self.fail(f"Failed to import src.mcp.logistics_mcp_server: {e}")

    def test_01_initialize(self):
        """Test standard initialize method."""
        from src.mcp.logistics_mcp_server import LogisticsMCPServer
        server = LogisticsMCPServer()
        req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        resp = server.handle_request(req)
        self.assertEqual(resp.get("jsonrpc"), "2.0")
        self.assertEqual(resp.get("id"), 1)
        self.assertIn("result", resp)
        self.assertIn("protocolVersion", resp["result"])
        self.assertIn("serverInfo", resp["result"])

    def test_02_tools_list(self):
        """Test tools/list returns all 5 tools with valid inputSchema."""
        from src.mcp.logistics_mcp_server import LogisticsMCPServer
        server = LogisticsMCPServer()
        req = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        resp = server.handle_request(req)
        self.assertEqual(resp.get("jsonrpc"), "2.0")
        self.assertEqual(resp.get("id"), 2)
        tools = resp.get("result", {}).get("tools", [])
        self.assertEqual(len(tools), 5)
        
        expected_tool_names = {
            "get_fleet_status",
            "optimize_cvrp_routes",
            "inject_disruption",
            "inspect_cargo_multimodal",
            "evaluate_feedback_loop"
        }
        found_names = {t["name"] for t in tools}
        self.assertEqual(expected_tool_names, found_names)
        
        for tool in tools:
            self.assertIn("description", tool)
            self.assertIn("inputSchema", tool)
            self.assertEqual(tool["inputSchema"].get("type"), "object")
            self.assertIn("properties", tool["inputSchema"])

    def test_03_tools_call_valid(self):
        """Test tools/call for each of the 5 tools with valid arguments."""
        from src.mcp.logistics_mcp_server import LogisticsMCPServer
        server = LogisticsMCPServer()

        # 1. get_fleet_status
        resp = server.handle_request({
            "jsonrpc": "2.0",
            "id": 31,
            "method": "tools/call",
            "params": {"name": "get_fleet_status", "arguments": {"include_routes": True}}
        })
        self.assertEqual(resp.get("id"), 31)
        self.assertIn("result", resp)
        self.assertIn("content", resp["result"])

        # 2. optimize_cvrp_routes
        resp = server.handle_request({
            "jsonrpc": "2.0",
            "id": 32,
            "method": "tools/call",
            "params": {"name": "optimize_cvrp_routes", "arguments": {}}
        })
        self.assertEqual(resp.get("id"), 32)
        self.assertIn("result", resp)

        # 3. inject_disruption
        resp = server.handle_request({
            "jsonrpc": "2.0",
            "id": 33,
            "method": "tools/call",
            "params": {"name": "inject_disruption", "arguments": {"disruption_type": "breakdown"}}
        })
        self.assertEqual(resp.get("id"), 33)
        self.assertIn("result", resp)

        # 4. inspect_cargo_multimodal
        resp = server.handle_request({
            "jsonrpc": "2.0",
            "id": 34,
            "method": "tools/call",
            "params": {
                "name": "inspect_cargo_multimodal",
                "arguments": {"cargo_id": "ORD-01", "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="}
            }
        })
        self.assertEqual(resp.get("id"), 34)
        self.assertIn("result", resp)

        # 5. evaluate_feedback_loop
        resp = server.handle_request({
            "jsonrpc": "2.0",
            "id": 35,
            "method": "tools/call",
            "params": {"name": "evaluate_feedback_loop", "arguments": {"iteration": 1}}
        })
        self.assertEqual(resp.get("id"), 35)
        self.assertIn("result", resp)

    def test_04_unknown_tool(self):
        """Test calling an unknown tool returns error -32602 or proper error structure."""
        from src.mcp.logistics_mcp_server import LogisticsMCPServer
        server = LogisticsMCPServer()
        resp = server.handle_request({
            "jsonrpc": "2.0",
            "id": 40,
            "method": "tools/call",
            "params": {"name": "non_existent_tool", "arguments": {}}
        })
        self.assertEqual(resp.get("id"), 40)
        self.assertTrue("error" in resp or resp.get("result", {}).get("isError") is True)

    def test_05_unknown_method(self):
        """Test unknown RPC method returns -32601 Method not found."""
        from src.mcp.logistics_mcp_server import LogisticsMCPServer
        server = LogisticsMCPServer()
        resp = server.handle_request({
            "jsonrpc": "2.0",
            "id": 50,
            "method": "non_existent_method",
            "params": {}
        })
        self.assertEqual(resp.get("id"), 50)
        self.assertIn("error", resp)
        self.assertEqual(resp["error"].get("code"), -32601)

    def test_06_malformed_input(self):
        """Test malformed request handling."""
        from src.mcp.logistics_mcp_server import LogisticsMCPServer
        server = LogisticsMCPServer()
        resp = server.handle_request({})
        self.assertIn("error", resp)

if __name__ == "__main__":
    unittest.main()
