import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestVercelEntrypoint(unittest.TestCase):
    def test_01_api_index_import_and_handler(self):
        """Test that api/index.py imports cleanly and exports a valid Vercel handler."""
        try:
            import api.index as vercel_api
            self.assertTrue(hasattr(vercel_api, "handler"))
            self.assertTrue(hasattr(vercel_api, "controller"))
            self.assertTrue(hasattr(vercel_api, "mcp_server"))
            self.assertGreater(len(vercel_api.controller.vehicles), 0)
            self.assertGreater(len(vercel_api.controller.depots), 0)
        except Exception as e:
            self.fail(f"Failed to import api/index.py: {e}")

    def test_02_resolve_request_path_rewrites(self):
        """Test _resolve_request_path handles Vercel __route__ rewrite parameter and headers."""
        from src.core.http_server import LogisticsAPIHandler

        class DummyHandler(LogisticsAPIHandler):
            def __init__(self, path: str, headers: dict = None):
                self.path = path
                self.headers = headers or {}

        # 1. Direct path
        h1 = DummyHandler("/api/state")
        path1, _ = h1._resolve_request_path()
        self.assertEqual(path1, "/api/state")

        # 2. Vercel rewrite parameter
        h2 = DummyHandler("/api/index.py?__route__=/api/optimize&format=json")
        path2, query2 = h2._resolve_request_path()
        self.assertEqual(path2, "/api/optimize")
        self.assertEqual(query2.get("format"), ["json"])

        # 3. Vercel header fallback
        h3 = DummyHandler("/api/index.py", {"x-matched-path": "/api/chat"})
        path3, _ = h3._resolve_request_path()
        self.assertEqual(path3, "/api/chat")


if __name__ == "__main__":
    unittest.main()
