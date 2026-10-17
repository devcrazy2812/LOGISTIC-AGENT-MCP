# Contributing to LogiSwarm AI

Thank you for your interest in contributing to **LogiSwarm AI**! This document provides instructions for contributing code, tests, and documentation to this project.

---

## 🧭 Code of Conduct

All contributors are expected to uphold our [Code of Conduct](CODE_OF_CONDUCT.md). Please be welcoming, constructive, and respectful.

---

## 🛠️ Development Setup

### 1. Prerequisites
- Python 3.9+ (Python 3.10 to 3.13 tested)
- Git

### 2. Fork & Clone
```bash
git clone https://github.com/devcrazy2812/LOGISTIC-AGENT-MCP.git
cd LOGISTIC-AGENT-MCP
```

### 3. Create a Virtual Environment (Optional)
LogiSwarm AI uses the Python standard library for its core runtime with zero external runtime dependencies. If installing optional developer tools:
```bash
python -m venv .venv

# On Linux / macOS:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

---

## 🧪 Running the Test Suite

Before submitting any changes, ensure all tests pass cleanly:

```bash
# Run the complete test suite
python -m unittest discover -s tests -v

# Run a specific test file
python -m unittest tests/test_swarm.py
python -m unittest tests/test_mcp_server.py
python -m unittest tests/test_mcp_protocol.py
python -m unittest tests/test_gemini_client.py
python -m unittest tests/test_security.py
```

All 41 tests must pass with zero regressions.

---

## 🌿 Branching & Git Workflow

We follow standard GitHub Flow:

1. Always create a focused feature or fix branch from `main`:
   - `fix/mcp-...` for bug fixes
   - `feat/routing-...` for new features
   - `docs/readme-...` for documentation
   - `ci/actions-...` for CI/CD updates
2. Commit messages should follow the **Conventional Commits** specification:
   - `feat(mcp): add resources/read support`
   - `fix(security): resolve TOTP replay vulnerability`
   - `docs(readme): update test count and architecture diagrams`
   - `test(gemini): add backoff retry test cases`
3. Push your branch to your fork and submit a Pull Request to `main`.

---

## 🛡️ Security Vulnerabilities

Please do **not** report security vulnerabilities via public GitHub issues. Refer to [`SECURITY.md`](SECURITY.md) for our coordinated vulnerability disclosure policy.

---

## 📋 PR Submission Checklist

- [ ] All tests pass (`python -m unittest discover -s tests -v`).
- [ ] No hardcoded API keys, secrets, or absolute local paths are committed.
- [ ] Documentation and comments are updated where relevant.
- [ ] Conventional commit message used.
