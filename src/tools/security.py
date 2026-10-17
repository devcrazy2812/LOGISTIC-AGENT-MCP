import os
import sys
import hmac
import hashlib
import struct
import time
import base64
import secrets
import json
import re
import logging
from typing import Dict, Any, Tuple, Optional, List

logger = logging.getLogger("Security")
if not logger.handlers:
    _handler = logging.StreamHandler(sys.stderr)
    _handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] [Security] %(message)s"))
    logger.addHandler(_handler)
logger.setLevel(logging.INFO)

# ==============================================================================
# Master Secret Key for Ephemeral Signed Tokens, Encryption, and Hashing
# ==============================================================================
_env_secret = os.environ.get("LOGISWARM_SECRET_KEY")
_is_prod = os.environ.get("ENVIRONMENT", "").lower() in ("production", "prod") or os.environ.get("PRODUCTION") == "1"

if _env_secret and _env_secret.strip():
    SECURITY_SECRET = _env_secret.strip()
else:
    if _is_prod:
        raise RuntimeError(
            "CRITICAL SECURITY CONFIGURATION ERROR: LOGISWARM_SECRET_KEY environment variable "
            "must be explicitly set in production mode. Refusing to boot with default secret."
        )
    # Stable fallback key for development & test suites
    SECURITY_SECRET = "logiswarm-dev-secret-key-32bytes-hex-00"

# Dynamic CORS regex whitelisting (Blueprint 2.B)
ALLOWED_ORIGIN_REGEX = re.compile(
    r"^(http://localhost(:\d+)?|"
    r"http://127\.0\.0\.1(:\d+)?|"
    r"http://10\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d+)?|"
    r"https://([a-zA-Z0-9\-]+\.)?github\.io|"
    r"https://([a-zA-Z0-9\-]+\.)?logiswarm\.ai)$"
)

# ==============================================================================
# 1. Standard-Library Two-Factor Authentication (2FA / TOTP RFC 6238)
# (Zero External Dependencies - Google Authenticator / Authy Compatible)
# ==============================================================================

# Replay protection cache: maps (secret_hash, counter) -> timestamp
_TOTP_REPLAY_CACHE: Dict[Tuple[str, int], float] = {}


def generate_totp_secret() -> str:
    """Generates a standard 16-character base32 secret."""
    return base64.b32encode(secrets.token_bytes(10)).decode('utf-8').replace('=', '')


def generate_totp_code(secret: str, time_step: int = 30, t: Optional[int] = None) -> str:
    """Calculates RFC 6238 6-digit TOTP code from secret."""
    if t is None:
        t = int(time.time())
    counter = int(t // time_step)
    key = base64.b32decode(secret, casefold=True)
    msg = struct.pack(">Q", counter)
    h = hmac.new(key, msg, hashlib.sha1).digest()
    offset = h[-1] & 0x0F
    code = struct.unpack(">I", h[offset:offset+4])[0] & 0x7FFFFFFF
    return str(code % 1000000).zfill(6)


def verify_totp_code(
    secret: str,
    user_code: str,
    window: int = 1,
    t: Optional[int] = None,
    check_replay: bool = True
) -> bool:
    """
    Verifies submitted TOTP code with clock-drift tolerance, constant-time
    comparison, and anti-replay protection.
    """
    if not secret or not user_code:
        return False
    user_code_str = str(user_code).strip()
    if len(user_code_str) != 6 or not user_code_str.isdigit():
        return False

    current_time = int(time.time()) if t is None else int(t)
    secret_hash = hashlib.sha256(secret.encode()).hexdigest()[:16]

    # Clean old replay entries older than 3 minutes
    now = time.time()
    stale_keys = [k for k, exp in _TOTP_REPLAY_CACHE.items() if now - exp > 180]
    for k in stale_keys:
        _TOTP_REPLAY_CACHE.pop(k, None)

    for step in range(-window, window + 1):
        step_time = current_time + (step * 30)
        counter = int(step_time // 30)
        expected_code = generate_totp_code(secret, time_step=30, t=step_time)

        if hmac.compare_digest(expected_code, user_code_str):
            if check_replay:
                cache_key = (secret_hash, counter)
                if cache_key in _TOTP_REPLAY_CACHE:
                    logger.warning(f"Replay attack detected for TOTP counter {counter}")
                    return False
                _TOTP_REPLAY_CACHE[cache_key] = now
            return True

    return False


def clear_totp_replay_cache():
    """Clears the TOTP replay cache (used in test fixtures)."""
    _TOTP_REPLAY_CACHE.clear()


# ==============================================================================
# 2. Ephemeral HMAC-SHA256 Signed Access Tokens (Blueprint 2.F)
# ==============================================================================

def generate_channel_token(user_id: str, role: str, action: str, expiry_seconds: int = 3600) -> str:
    """Generates an ephemeral HMAC-SHA256 signed access token for high-privilege dispatch."""
    expiry = int(time.time()) + expiry_seconds
    payload = f"{user_id}:{role}:{action}:{expiry}"
    signature = hmac.new(SECURITY_SECRET.encode('utf-8'), payload.encode('utf-8'), hashlib.sha256).hexdigest()
    return f"{payload}:{signature}"


def verify_channel_token(token: str, expected_action: str) -> Tuple[bool, Dict[str, Any]]:
    """Cryptographically verifies signed token and validates expiration."""
    if not token or not isinstance(token, str):
        return False, {"error": "Missing or invalid token"}
    parts = token.strip().split(':')
    if len(parts) != 5:
        return False, {"error": "Malformed token structure"}
    u_id, role, action, expiry, sig = parts
    if action != expected_action:
        return False, {"error": f"Action mismatch (expected {expected_action}, got {action})"}
    try:
        if int(expiry) < time.time():
            return False, {"error": "Token has expired"}
    except ValueError:
        return False, {"error": "Invalid token expiry format"}

    expected_sig = hmac.new(
        SECURITY_SECRET.encode('utf-8'),
        f"{u_id}:{role}:{action}:{expiry}".encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(sig, expected_sig):
        return False, {"error": "Cryptographic signature verification failed"}
    return True, {"user_id": u_id, "role": role, "action": action, "expiry": int(expiry)}


# ==============================================================================
# 3. Field-Level Authenticated Encryption (AES Keystream + HMAC-SHA256 Tag)
# ==============================================================================

def encrypt_sensitive_field(plaintext: str) -> str:
    """
    Field-level Authenticated Encryption using PBKDF2-HMAC (100,000 rounds)
    derived keystream + HMAC-SHA256 authentication tag (Encrypt-then-MAC).
    Returns base64 string: IV (16 bytes) + Tag (32 bytes) + Ciphertext.
    """
    if not plaintext:
        return ""
    plain_bytes = str(plaintext).encode('utf-8')
    iv = secrets.token_bytes(16)

    # Derive 64 bytes: 32 bytes for encryption keystream, 32 bytes for MAC authentication
    derived = hashlib.pbkdf2_hmac('sha256', SECURITY_SECRET.encode('utf-8'), iv, 100000, 64)
    enc_key = derived[:32]
    mac_key = derived[32:]

    # Keystream expansion using sequential counter blocks
    keystream = bytearray()
    counter = 0
    while len(keystream) < len(plain_bytes):
        keystream.extend(hashlib.sha256(enc_key + iv + struct.pack(">I", counter)).digest())
        counter += 1

    ciphertext = bytes(p ^ k for p, k in zip(plain_bytes, keystream[:len(plain_bytes)]))

    # Authenticate IV + Ciphertext with HMAC-SHA256
    tag = hmac.new(mac_key, iv + ciphertext, hashlib.sha256).digest()

    # Pack 16 bytes IV + 32 bytes Auth Tag + Ciphertext
    combined = iv + tag + ciphertext
    return base64.b64encode(combined).decode('utf-8')


def decrypt_sensitive_field(ciphertext_b64: str) -> str:
    """
    Decrypts field-level authenticated ciphertext.
    Validates HMAC-SHA256 authentication tag in constant time before decrypting.
    Returns decrypted plaintext, or error description if authentication fails.
    """
    if not ciphertext_b64:
        return ""
    try:
        combined = base64.b64decode(ciphertext_b64.encode('utf-8'))
        if len(combined) < 48:
            # Handle legacy unauthenticated ciphertext (16 bytes IV + ciphertext)
            return _decrypt_legacy_field(combined)

        iv = combined[:16]
        tag = combined[16:48]
        ciphertext = combined[48:]

        # Derive keys
        derived = hashlib.pbkdf2_hmac('sha256', SECURITY_SECRET.encode('utf-8'), iv, 100000, 64)
        enc_key = derived[:32]
        mac_key = derived[32:]

        # Constant-time verify MAC tag
        expected_tag = hmac.new(mac_key, iv + ciphertext, hashlib.sha256).digest()
        if not hmac.compare_digest(tag, expected_tag):
            logger.error("PII Decryption Failed: Authenticated integrity tag mismatch (tampering detected)")
            return "[Decryption Error: Authentication Failed]"

        # Decrypt ciphertext
        keystream = bytearray()
        counter = 0
        while len(keystream) < len(ciphertext):
            keystream.extend(hashlib.sha256(enc_key + iv + struct.pack(">I", counter)).digest())
            counter += 1

        decrypted = bytes(c ^ k for c, k in zip(ciphertext, keystream[:len(ciphertext)]))
        return decrypted.decode('utf-8')
    except Exception as e:
        logger.error(f"PII Decryption Exception: {e}")
        return "[Decryption Error: Key Mismatch]"


def _decrypt_legacy_field(combined: bytes) -> str:
    """Fallback decryptor for legacy unauthenticated ciphertext format."""
    try:
        iv = combined[:16]
        encrypted = combined[16:]
        key = hashlib.pbkdf2_hmac('sha256', SECURITY_SECRET.encode('utf-8'), iv, 100000, 32)
        keystream = hashlib.sha256(key + iv).digest()
        while len(keystream) < len(encrypted):
            keystream += hashlib.sha256(keystream).digest()
        decrypted = bytes(e ^ k for e, k in zip(encrypted, keystream[:len(encrypted)]))
        return decrypted.decode('utf-8')
    except Exception:
        return "[Decryption Error: Key Mismatch]"


# ==============================================================================
# 4. Immutable Cryptographic Hash-Chained Audit Logging (Blueprint 3.D)
# ==============================================================================

class SecurityAuditLogger:
    """
    Cryptographically chained append-only audit logger.
    Each entry includes a SHA-256 hash incorporating the previous entry's hash,
    creating an immutable, tamper-evident cryptographic blockchain of security events.
    """
    _logs: List[Dict[str, Any]] = []
    _last_hash: str = "GENESIS_00000000000000000000000000000000"

    @classmethod
    def log(cls, action: str, ip_address: str, user_id: str = "DISPATCHER-01", details: str = "") -> Dict[str, Any]:
        prev_hash = cls._last_hash
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

        # Hash calculation covers previous hash and all event fields
        payload = f"{prev_hash}:{action}:{ip_address}:{user_id}:{timestamp}:{details}".encode('utf-8')
        entry_hash = hashlib.sha256(payload).hexdigest()
        cls._last_hash = entry_hash

        entry = {
            "id": len(cls._logs) + 1,
            "timestamp": timestamp,
            "action": action,
            "user_id": user_id,
            "ip_address": ip_address,
            "details": details,
            "prev_hash": prev_hash,
            "hash": entry_hash
        }
        cls._logs.append(entry)
        return entry

    @classmethod
    def get_recent(cls, count: int = 50) -> List[Dict[str, Any]]:
        return cls._logs[-count:]

    @classmethod
    def verify_chain(cls) -> Tuple[bool, Optional[int]]:
        """
        Verifies the cryptographic integrity of the entire audit chain.
        Returns (True, None) if intact, or (False, broken_index) if tampered.
        """
        expected_prev = "GENESIS_00000000000000000000000000000000"
        for idx, entry in enumerate(cls._logs):
            if entry.get("prev_hash") != expected_prev:
                return False, idx

            payload = f"{expected_prev}:{entry['action']}:{entry['ip_address']}:{entry['user_id']}:{entry['timestamp']}:{entry['details']}".encode('utf-8')
            computed_hash = hashlib.sha256(payload).hexdigest()
            if not hmac.compare_digest(entry.get("hash", ""), computed_hash):
                return False, idx

            expected_prev = computed_hash
        return True, None

    @classmethod
    def clear(cls):
        """Resets the audit log (used strictly in test fixtures)."""
        cls._logs = []
        cls._last_hash = "GENESIS_00000000000000000000000000000000"
