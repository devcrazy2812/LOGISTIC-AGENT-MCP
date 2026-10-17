import unittest
import sys
import os
import json
import subprocess

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class TestMCPProtocolStdio(unittest.TestCase):
    """End-to-end integration test of LogisticsMCPServer over stdio subprocess."""

    def setUp(self):
        self.proc = subprocess.Popen(
            [sys.executable, os.path.join(PROJECT_ROOT, "mcp_server.py")],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            cwd=PROJECT_ROOT
        )

    def tearDown(self):
        if self.proc:
            try:
                if self.proc.stdin and not self.proc.stdin.closed:
                    self.proc.stdin.close()
                if self.proc.stdout and not self.proc.stdout.closed:
                    self.proc.stdout.close()
                if self.proc.stderr and not self.proc.stderr.closed:
                    self.proc.stderr.close()
                self.proc.terminate()
                self.proc.wait(timeout=3)
            except Exception:
                self.proc.kill()

    def _send_and_receive(self, req: dict) -> dict:
        line = json.dumps(req) + "\n"
        self.proc.stdin.write(line)
        self.proc.stdin.flush()
        resp_line = self.proc.stdout.readline()
        self.assertTrue(resp_line, "Received empty response from MCP server stdout")
        return json.loads(resp_line.strip())

    def test_stdio_full_handshake_and_dispatch(self):
        # 1. Initialize
        init_req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05", "capabilities": {}}
        }
        init_resp = self._send_and_receive(init_req)
        self.assertEqual(init_resp.get("id"), 1)
        self.assertEqual(init_resp.get("result", {}).get("protocolVersion"), "2024-11-05")

        # 2. Notification: initialized (server must NOT write any response line)
        notif = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        self.proc.stdin.write(json.dumps(notif) + "\n")
        self.proc.stdin.flush()

        # 3. Modern server/discover (MCP 2026-07-28)
        discover_req = {"jsonrpc": "2.0", "id": 2, "method": "server/discover"}
        discover_resp = self._send_and_receive(discover_req)
        self.assertEqual(discover_resp.get("id"), 2)
        self.assertIn("2026-07-28", discover_resp["result"]["protocols"])

        # 4. Ping
        ping_req = {"jsonrpc": "2.0", "id": 3, "method": "ping"}
        ping_resp = self._send_and_receive(ping_req)
        self.assertEqual(ping_resp.get("id"), 3)
        self.assertEqual(ping_resp.get("result"), {})

        # 5. Resources list
        res_req = {"jsonrpc": "2.0", "id": 4, "method": "resources/list"}
        res_resp = self._send_and_receive(res_req)
        self.assertEqual(res_resp.get("id"), 4)
        self.assertEqual(len(res_resp["result"]["resources"]), 3)

        # 6. Tools call: get_fleet_status
        tool_req = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {"name": "get_fleet_status", "arguments": {}}
        }
        tool_resp = self._send_and_receive(tool_req)
        self.assertEqual(tool_resp.get("id"), 5)
        self.assertIn("content", tool_resp["result"])


if __name__ == "__main__":
    unittest.main()
