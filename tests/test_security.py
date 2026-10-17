import unittest
import sys
import os
import base64
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.security import (
    generate_totp_secret,
    generate_totp_code,
    verify_totp_code,
    clear_totp_replay_cache,
    generate_channel_token,
    verify_channel_token,
    encrypt_sensitive_field,
    decrypt_sensitive_field,
    SecurityAuditLogger
)


class TestSecurityHardening(unittest.TestCase):
    def setUp(self):
        clear_totp_replay_cache()
        SecurityAuditLogger.clear()

    def test_01_rfc6238_official_test_vectors(self):
        """
        Verify implementation against RFC 6238 Appendix B Table 1 standard test vectors.
        Secret: '12345678901234567890' (in Base32: 'GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ')
        Algorithm: SHA-1, Step: 30s, Digits: 6
        """
        rfc_secret = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
        vectors = [
            (59, "287082"),
            (1111111109, "081804"),
            (1111111111, "050471"),
            (1234567890, "005924"),
            (2000000000, "279037")
        ]
        for timestamp, expected_code in vectors:
            computed_code = generate_totp_code(rfc_secret, time_step=30, t=timestamp)
            self.assertEqual(
                computed_code, expected_code,
                f"RFC 6238 vector mismatch at T={timestamp}: expected {expected_code}, got {computed_code}"
            )
            self.assertTrue(
                verify_totp_code(rfc_secret, expected_code, window=0, t=timestamp, check_replay=False),
                f"Failed to verify valid code {expected_code} at T={timestamp}"
            )

    def test_02_totp_replay_prevention(self):
        """Test that replaying the same TOTP code in the same window is rejected."""
        secret = generate_totp_secret()
        now = int(time.time())
        code = generate_totp_code(secret, t=now)

        # First verification must succeed
        self.assertTrue(verify_totp_code(secret, code, t=now, check_replay=True))

        # Replay in same window must be rejected
        self.assertFalse(
            verify_totp_code(secret, code, t=now, check_replay=True),
            "Replayed TOTP code was erroneously accepted"
        )

        # Next window code must succeed
        next_code = generate_totp_code(secret, t=now + 35)
        self.assertTrue(verify_totp_code(secret, next_code, t=now + 35, check_replay=True))

    def test_03_pii_authenticated_encryption_and_tamper_detection(self):
        """Test Encrypt-then-MAC authenticated encryption and tamper resistance."""
        plain = "Patient #8492: Controlled Vaccine Dispatch, Cold-Chain Unit #3"
        ciphertext = encrypt_sensitive_field(plain)
        self.assertNotEqual(plain, ciphertext)

        # Clean decryption succeeds
        decrypted = decrypt_sensitive_field(ciphertext)
        self.assertEqual(plain, decrypted)

        # Tampering with ciphertext bits must fail authentication
        raw_combined = bytearray(base64.b64decode(ciphertext.encode("utf-8")))
        # Flip a bit in the encrypted payload (after IV and MAC tag)
        raw_combined[-1] ^= 0x01
        tampered_ciphertext = base64.b64encode(raw_combined).decode("utf-8")

        tamper_result = decrypt_sensitive_field(tampered_ciphertext)
        self.assertIn("Authentication Failed", tamper_result)

    def test_04_ephemeral_hmac_tokens(self):
        """Test signed token lifecycle: issuance, verification, tampering, expiration."""
        token = generate_channel_token("DISPATCHER-09", "SENIOR_LEAD", "REROUTE_CONFIRM", expiry_seconds=300)
        valid, meta = verify_channel_token(token, "REROUTE_CONFIRM")
        self.assertTrue(valid)
        self.assertEqual(meta["user_id"], "DISPATCHER-09")
        self.assertEqual(meta["role"], "SENIOR_LEAD")

        # Wrong action rejected
        invalid_action, err = verify_channel_token(token, "UNAUTHORIZED_ADMIN_DRAIN")
        self.assertFalse(invalid_action)
        self.assertIn("mismatch", err.get("error", "").lower())

        # Tampered signature rejected
        tampered_token = token[:-4] + "dead"
        invalid_sig, err = verify_channel_token(tampered_token, "REROUTE_CONFIRM")
        self.assertFalse(invalid_sig)

        # Expired token rejected
        expired_token = generate_channel_token("DISPATCHER-09", "LEAD", "REROUTE_CONFIRM", expiry_seconds=-10)
        invalid_exp, err = verify_channel_token(expired_token, "REROUTE_CONFIRM")
        self.assertFalse(invalid_exp)
        self.assertIn("expired", err.get("error", "").lower())

    def test_05_audit_log_cryptographic_hash_chain(self):
        """Test append-only cryptographic hash chaining and tampering detection."""
        # Log several events
        SecurityAuditLogger.log("SYSTEM_BOOT", "127.0.0.1", "SYSTEM", "Cluster initialized")
        SecurityAuditLogger.log("DISPATCH_PLANNED", "10.0.0.4", "DISPATCHER-01", "Routes assigned to fleet")
        SecurityAuditLogger.log("DISRUPTION_RESOLVED", "10.0.0.4", "AUTONOMOUS_SWARM", "Rerouted vehicle V-02")

        # Chain verification must pass
        is_valid, broken_idx = SecurityAuditLogger.verify_chain()
        self.assertTrue(is_valid, f"Audit chain verification failed at index {broken_idx}")

        # Tampering with any log entry must break chain verification
        logs = SecurityAuditLogger._logs
        original_details = logs[1]["details"]
        logs[1]["details"] = "FORGED DETAILS: Rerouted to unauthorized destination"

        is_valid_after_tamper, broken_idx = SecurityAuditLogger.verify_chain()
        self.assertFalse(is_valid_after_tamper, "Tampered audit entry went undetected")
        self.assertEqual(broken_idx, 1)

        # Restore
        logs[1]["details"] = original_details
        self.assertTrue(SecurityAuditLogger.verify_chain()[0])


if __name__ == "__main__":
    unittest.main()
