import unittest
import sys
import os
import json
import base64
import urllib.error
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.gemini_client import (
    GoogleGeminiClient, CargoAnalysis, detect_image_mime, validate_and_decode_base64
)

# 1x1 transparent PNG
SAMPLE_PNG_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="

class TestGeminiClient(unittest.TestCase):
    def setUp(self):
        # Sample structured vision response
        self.mock_vision_data = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": json.dumps({
                            "damage_severity": "MINOR_TEAR",
                            "compromised_items": ["medical_kits"],
                            "box_integrity": "Corner seal punctured",
                            "root_cause": "Handling abrasion",
                            "recommended_action": "REPACKAGE_AND_RELEASE",
                            "insurance_claim_estimate_usd": 120.50,
                            "replacement_priority": "LOW",
                            "directive": "Inspect items inside and replace outer box."
                        })
                    }]
                }
            }]
        }

    def test_01_no_api_key_fallback(self):
        """When no API key is provided, client must safely return simulated fallback."""
        client = GoogleGeminiClient(api_key="")
        self.assertFalse(client.is_configured())
        res = client.analyze_multimodal_cargo(image_base64=SAMPLE_PNG_B64)
        self.assertEqual(res["mode"], "EMBEDDED_MULTIMODAL_ENGINE")
        self.assertTrue(res.get("is_simulated"))
        self.assertIn("fallback_reason", res)
        self.assertEqual(res["fallback_reason"], "API key not configured")

    def test_02_detect_image_mime_and_base64_validation(self):
        """Test magic byte detection and base64 size/format validation."""
        raw_png = base64.b64decode(SAMPLE_PNG_B64)
        self.assertEqual(detect_image_mime(raw_png), "image/png")

        # JPEG magic bytes \xff\xd8\xff
        raw_jpeg = b"\xff\xd8\xff\xe0\x00\x10JFIF"
        self.assertEqual(detect_image_mime(raw_jpeg), "image/jpeg")

        # WebP magic bytes RIFF....WEBP
        raw_webp = b"RIFF\x1a\x00\x00\x00WEBPVP8 "
        self.assertEqual(detect_image_mime(raw_webp), "image/webp")

        # Invalid base64
        with self.assertRaises(ValueError):
            validate_and_decode_base64("not_valid_b64!!!")

        # Valid decode
        decoded, mime = validate_and_decode_base64(SAMPLE_PNG_B64)
        self.assertEqual(mime, "image/png")
        self.assertEqual(len(decoded), len(raw_png))

    @patch("urllib.request.urlopen")
    def test_03_success_call(self, mock_urlopen):
        """Test successful Gemini API call with header authentication and structured output."""
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(self.mock_vision_data).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        client = GoogleGeminiClient(api_key="test_key_12345")
        res = client.analyze_multimodal_cargo(image_base64=SAMPLE_PNG_B64)

        self.assertEqual(res["mode"], "LIVE_GEMINI_API")
        self.assertFalse(res.get("is_simulated", False))
        self.assertEqual(res["analysis"]["damage_severity"], "MINOR_TEAR")
        self.assertEqual(res["analysis"]["insurance_claim_estimate_usd"], 120.50)

        # Verify request parameters
        req_sent = mock_urlopen.call_args[0][0]
        self.assertNotIn("key=", req_sent.full_url)
        self.assertEqual(req_sent.headers.get("X-goog-api-key"), "test_key_12345")

    @patch("urllib.request.urlopen")
    def test_04_404_model_gone(self, mock_urlopen):
        """Test handling of HTTP 404 (model deprecated / shut down)."""
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://generativelanguage.googleapis.com",
            code=404,
            msg="Not Found: Model gemini-2.5-flash deprecated",
            hdrs={},
            fp=None
        )

        client = GoogleGeminiClient(api_key="test_key_12345")
        res = client.analyze_multimodal_cargo(image_base64=SAMPLE_PNG_B64)

        self.assertEqual(res["mode"], "EMBEDDED_MULTIMODAL_ENGINE")
        self.assertTrue(res.get("is_simulated"))
        self.assertIn("404", res["fallback_reason"])

    @patch("urllib.request.urlopen")
    def test_05_429_retry_then_success(self, mock_urlopen):
        """Test HTTP 429 rate limit triggers bounded retry with backoff, then succeeds."""
        mock_429 = urllib.error.HTTPError(
            url="https://generativelanguage.googleapis.com",
            code=429,
            msg="Too Many Requests",
            hdrs={},
            fp=None
        )
        mock_success = MagicMock()
        mock_success.read.return_value = json.dumps(self.mock_vision_data).encode("utf-8")
        mock_success.__enter__.return_value = mock_success

        mock_urlopen.side_effect = [mock_429, mock_success]

        client = GoogleGeminiClient(api_key="test_key_12345")
        res = client.analyze_multimodal_cargo(image_base64=SAMPLE_PNG_B64)

        self.assertEqual(mock_urlopen.call_count, 2)
        self.assertEqual(res["mode"], "LIVE_GEMINI_API")

    @patch("urllib.request.urlopen")
    def test_06_malformed_json_response(self, mock_urlopen):
        """Test response with malformed JSON falls back gracefully."""
        mock_resp = MagicMock()
        mock_resp.read.return_value = b"{not-valid-json"
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        client = GoogleGeminiClient(api_key="test_key_12345")
        res = client.analyze_multimodal_cargo(image_base64=SAMPLE_PNG_B64)

        self.assertEqual(res["mode"], "EMBEDDED_MULTIMODAL_ENGINE")
        self.assertTrue(res.get("is_simulated"))
        self.assertIn("fallback_reason", res)

    @patch("urllib.request.urlopen")
    def test_07_timeout_handling(self, mock_urlopen):
        """Test network timeout triggers fallback with explicit reason."""
        mock_urlopen.side_effect = urllib.error.URLError("timed out")

        client = GoogleGeminiClient(api_key="test_key_12345")
        res = client.analyze_multimodal_cargo(image_base64=SAMPLE_PNG_B64)

        self.assertEqual(res["mode"], "EMBEDDED_MULTIMODAL_ENGINE")
        self.assertTrue(res.get("is_simulated"))
        self.assertIn("timed out", res["fallback_reason"].lower())

    def test_08_dynamic_state_chat_fallback(self):
        """Test chat fallback dynamically interpolates real controller state."""
        client = GoogleGeminiClient(api_key="")
        mock_state = {
            "vehicles": [
                {"name": "VoltAlpha", "type": "EV Van", "status": "en_route"},
                {"name": "TitanMover", "type": "Diesel", "status": "idle"}
            ],
            "depots": [
                {"name": "Hub Alpha", "inventory": {"medical_kits": 450, "vaccines": 200}}
            ],
            "orders": [{"id": "ORD-1"}, {"id": "ORD-2"}],
            "disruptions": [],
            "metrics": {"fleet_utilization_rate": 80.0, "sla_compliance_rate": 98.5, "co2_saved_vs_baseline_kg": 42.0}
        }

        # 1. Fleet question
        reply_fleet = client.generate_chat_response("What is the fleet status?", "system", state=mock_state)
        self.assertIn("VoltAlpha", reply_fleet)
        self.assertIn("TitanMover", reply_fleet)
        self.assertIn("2 vehicles", reply_fleet)

        # 2. Inventory question
        reply_inv = client.generate_chat_response("Check warehouse inventory", "system", state=mock_state)
        self.assertIn("650 total units", reply_inv)
        self.assertIn("1 regional distribution hubs", reply_inv)

if __name__ == "__main__":
    unittest.main()
