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

    def test_07_server_discover(self):
        """MCP 2026-07-28: Test server/discover method returns protocols and capabilities."""
        from src.mcp.logistics_mcp_server import LogisticsMCPServer
        server = LogisticsMCPServer()
        req = {
            "jsonrpc": "2.0",
            "id": 70,
            "method": "server/discover"
        }
        resp = server.handle_request(req)
        self.assertEqual(resp.get("id"), 70)
        result = resp.get("result", {})
        self.assertIn("protocols", result)
        self.assertIn("2026-07-28", result["protocols"])
        self.assertIn("2024-11-05", result["protocols"])
        self.assertIn("serverInfo", result)
        self.assertIn("capabilities", result)

    def test_08_ping(self):
        """Test ping method returns empty result."""
        from src.mcp.logistics_mcp_server import LogisticsMCPServer
        server = LogisticsMCPServer()
        req = {"jsonrpc": "2.0", "id": 80, "method": "ping"}
        resp = server.handle_request(req)
        self.assertEqual(resp.get("id"), 80)
        self.assertEqual(resp.get("result"), {})

    def test_09_tool_annotations(self):
        """Test that all tools declare annotations conforming to MCP hints."""
        from src.mcp.logistics_mcp_server import LogisticsMCPServer
        for tool in LogisticsMCPServer.TOOLS:
            self.assertIn("annotations", tool, f"Tool {tool['name']} missing annotations")
            annotations = tool["annotations"]
            self.assertIn("readOnlyHint", annotations)
            self.assertIn("destructiveHint", annotations)
            self.assertIn("idempotentHint", annotations)

    def test_10_dry_run_disruption(self):
        """Test inject_disruption with dry_run=True previews impact without modifying state."""
        from src.mcp.logistics_mcp_server import LogisticsMCPServer
        server = LogisticsMCPServer()
        initial_disruptions_count = len(server.controller.disruptions)
        resp = server.handle_request({
            "jsonrpc": "2.0",
            "id": 100,
            "method": "tools/call",
            "params": {
                "name": "inject_disruption",
                "arguments": {"disruption_type": "severe_weather", "dry_run": True}
            }
        })
        self.assertEqual(resp.get("id"), 100)
        self.assertIn("result", resp)
        text = resp["result"]["content"][0]["text"]
        self.assertIn("DRY_RUN_SIMULATION", text)
        self.assertEqual(len(server.controller.disruptions), initial_disruptions_count)

    def test_11_cargo_multimodal_missing_image(self):
        """Test inspect_cargo_multimodal missing image_base64 returns result with isError=True."""
        from src.mcp.logistics_mcp_server import LogisticsMCPServer
        server = LogisticsMCPServer()
        resp = server.handle_request({
            "jsonrpc": "2.0",
            "id": 110,
            "method": "tools/call",
            "params": {
                "name": "inspect_cargo_multimodal",
                "arguments": {"cargo_id": "ORD-999"}
            }
        })
        self.assertEqual(resp.get("id"), 110)
        self.assertIn("result", resp)
        self.assertTrue(resp["result"].get("isError"))
        self.assertIn("Validation Error", resp["result"]["content"][0]["text"])

    def test_12_resources_list_and_read(self):
        """Test resources/list and resources/read for all standard logistics resources."""
        from src.mcp.logistics_mcp_server import LogisticsMCPServer
        server = LogisticsMCPServer()
        
        # 1. list
        list_resp = server.handle_request({"jsonrpc": "2.0", "id": 120, "method": "resources/list"})
        self.assertEqual(list_resp.get("id"), 120)
        resources = list_resp.get("result", {}).get("resources", [])
        self.assertEqual(len(resources), 3)
        uris = {r["uri"] for r in resources}
        self.assertEqual(uris, {"fleet://status", "depots://list", "orders://open"})

        # 2. read fleet://status
        read_fleet = server.handle_request({"jsonrpc": "2.0", "id": 121, "method": "resources/read", "params": {"uri": "fleet://status"}})
        self.assertEqual(read_fleet.get("id"), 121)
        self.assertIn("contents", read_fleet.get("result", {}))

        # 3. read depots://list
        read_depots = server.handle_request({"jsonrpc": "2.0", "id": 122, "method": "resources/read", "params": {"uri": "depots://list"}})
        self.assertEqual(read_depots.get("id"), 122)
        self.assertIn("contents", read_depots.get("result", {}))

        # 4. read orders://open
        read_orders = server.handle_request({"jsonrpc": "2.0", "id": 123, "method": "resources/read", "params": {"uri": "orders://open"}})
        self.assertEqual(read_orders.get("id"), 123)
        self.assertIn("contents", read_orders.get("result", {}))

        # 5. read invalid URI
        bad_read = server.handle_request({"jsonrpc": "2.0", "id": 124, "method": "resources/read", "params": {"uri": "invalid://uri"}})
        self.assertIn("error", bad_read)
        self.assertEqual(bad_read["error"].get("code"), -32602)

    def test_13_prompts_list_and_get(self):
        """Test prompts/list and prompts/get for logistics prompts."""
        from src.mcp.logistics_mcp_server import LogisticsMCPServer
        server = LogisticsMCPServer()

        # 1. list
        list_resp = server.handle_request({"jsonrpc": "2.0", "id": 130, "method": "prompts/list"})
        self.assertEqual(list_resp.get("id"), 130)
        prompts = list_resp.get("result", {}).get("prompts", [])
        self.assertEqual(len(prompts), 2)

        # 2. get dispatcher_briefing
        p1 = server.handle_request({"jsonrpc": "2.0", "id": 131, "method": "prompts/get", "params": {"name": "dispatcher_briefing"}})
        self.assertEqual(p1.get("id"), 131)
        self.assertIn("messages", p1.get("result", {}))

        # 3. get disruption_postmortem
        p2 = server.handle_request({"jsonrpc": "2.0", "id": 132, "method": "prompts/get", "params": {"name": "disruption_postmortem", "arguments": {"incident_type": "breakdown"}}})
        self.assertEqual(p2.get("id"), 132)
        self.assertIn("messages", p2.get("result", {}))

        # 4. get unknown prompt
        bad_p = server.handle_request({"jsonrpc": "2.0", "id": 133, "method": "prompts/get", "params": {"name": "unknown_prompt"}})
        self.assertIn("error", bad_p)
        self.assertEqual(bad_p["error"].get("code"), -32602)

    def test_14_notifications(self):
        """Test that JSON-RPC notifications (id=None, method='notifications/*') return None (no response)."""
        from src.mcp.logistics_mcp_server import LogisticsMCPServer
        server = LogisticsMCPServer()
        req = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        }
        resp = server.handle_request(req)
        self.assertIsNone(resp)

    def test_15_protocol_version_meta_validation(self):
        """Test MCP 2026-07-28 _meta protocol version enforcement."""
        from src.mcp.logistics_mcp_server import LogisticsMCPServer
        server = LogisticsMCPServer()

        # Valid supported version in _meta
        good_req = {
            "jsonrpc": "2.0",
            "id": 150,
            "method": "ping",
            "_meta": {"io.modelcontextprotocol/protocolVersion": "2026-07-28"}
        }
        self.assertEqual(server.handle_request(good_req).get("result"), {})

        # Unsupported future or invalid version
        bad_req = {
            "jsonrpc": "2.0",
            "id": 151,
            "method": "ping",
            "_meta": {"io.modelcontextprotocol/protocolVersion": "1999-01-01"}
        }
        bad_resp = server.handle_request(bad_req)
        self.assertIn("error", bad_resp)
        self.assertEqual(bad_resp["error"].get("code"), -32000)


if __name__ == "__main__":
    unittest.main()
