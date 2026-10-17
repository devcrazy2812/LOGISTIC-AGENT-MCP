# ==============================================================================
# Production Dockerfile for LogiSwarm AI
# Multi-platform, lean footprint, non-root security isolation
# ==============================================================================
FROM python:3.11-slim as runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Create unprivileged system user
RUN groupadd -g 1001 appgroup && \
    useradd -u 1001 -g appgroup -s /bin/bash -m appuser

# Copy application sources
COPY src/ /app/src/
COPY data/ /app/data/
COPY web/ /app/web/
COPY run.py mcp_server.py requirements.txt pyproject.toml /app/

# Set ownership to unprivileged user
RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/state').read()" || exit 1

ENTRYPOINT ["python", "run.py"]
