# 🛡️ Security Policy & Architecture

## Supported Versions

| Version | Supported          | Security Maintenance Status |
| ------- | ------------------ | --------------------------- |
| 1.0.x   | :white_check_mark: | Active Security Hardening   |
| < 1.0   | :x:                | Deprecated                  |

---

## Reporting a Vulnerability

We prioritize the security and cryptographic integrity of **LogiSwarm AI**. If you discover a vulnerability or security flaw, please do **not** open a public issue.

1. Email a detailed report to **security@logiswarm.ai** or maintainer private email.
2. Include:
   - Type of vulnerability (e.g. Authentication bypass, PII integrity failure, Prompt injection, Replay attack).
   - Clear reproduction steps or proof-of-concept script.
   - Potential impact on logistics fleet control or consignment PII.
3. We will acknowledge receipt within **24 hours** and provide a patch timeline within **72 hours**.

---

## Defensive Architecture & Cryptographic Specifications

LogiSwarm AI incorporates defensive cybersecurity patterns based on the Universal Master Blueprint:

### 1. Two-Factor Authentication (RFC 6238 TOTP)
- **Zero External Dependencies**: Standard library `hmac`, `hashlib`, `struct`, `time`.
- **Constant-Time Verification**: Uses `hmac.compare_digest` across all token comparisons to eliminate timing side-channel analysis.
- **Replay Protection**: Time-step counter cache (`_TOTP_REPLAY_CACHE`) rejects reused one-time passwords within active drift windows.
- **Clock Drift Tolerance**: Configurable `±1` step (30 seconds) tolerance for client synchronization.

### 2. Field-Level Authenticated Encryption (AEAD)
- **Encrypt-then-MAC Scheme**: Consignment addresses, recipient names, and hazardous cargo data are encrypted with PBKDF2-HMAC (100,000 iterations, 64-byte key material derivation) and authenticated with an HMAC-SHA256 signature tag.
- **Tamper Evident**: Modifying even a single bit in the ciphertext triggers an integrity authentication mismatch error (`"[Decryption Error: Authentication Failed]"`), preventing ciphertext malleability and bit-flipping attacks.

### 3. Ephemeral HMAC-SHA256 Signed Access Tokens
- **Format**: `<user_id>:<role>:<action>:<expiry_epoch>:<hmac_signature>`
- **Fail-Closed Secret Management**: Reads `LOGISWARM_SECRET_KEY` from the environment. In production mode (`ENVIRONMENT=production` or `PRODUCTION=1`), the server refuses to boot if the master key is missing.
- **Action Scoping**: Tokens are cryptographically bound to specific actions (`FLEET_COMMAND`, `ADMIN_BACKUP`, etc.) to prevent privilege escalation.

### 4. Cryptographic Hash-Chained Audit Logging
- **Immutable Blockchain Structure**: Each audit log entry calculates:
  $$\text{hash}_i = \text{SHA-256}(\text{hash}_{i-1} \parallel \text{action} \parallel \text{ip} \parallel \text{user} \parallel \text{timestamp} \parallel \text{details})$$
- **Verification Engine**: `SecurityAuditLogger.verify_chain()` programmatically verifies the entire audit sequence from the genesis block, instantly pinpointing any unauthorized log alteration.

### 5. HTTP & API Defenses
- **Dynamic CORS Whitelisting**: Strictly validates browser `Origin` headers against explicit regex (`localhost`, `127.0.0.1`, `logiswarm.ai`).
- **Defensive JSON Parsing**: Rejects non-JSON or oversized request payloads (>2MB) to prevent Denial of Service.
- **Anti-Bot Honeypot**: Hidden trap field (`hp_field`) traps automated bot submission scrapers and rejects them.
- **Prompt Injection Delimiters**: User dialogue inputs are sanitized and isolated within `<user_dispatch_query>` boundaries to safeguard AI agent prompt fidelity.
- **Rate Limiting**: In-memory sliding-window throttle (90 req/min general, 30 req/min chat) per client IP.
- **Defensive Headers**: HSTS, CSP (`frame-ancestors 'none'`), `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`.
