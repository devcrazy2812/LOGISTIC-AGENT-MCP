.PHONY: all test run mcp clean docker-build docker-run help

PYTHON ?= python

help:
	@echo "LogiSwarm AI - Developer Makefile"
	@echo "=================================="
	@echo "make test          Run full automated test suite (41 tests)"
	@echo "make run           Start Mission Control HTTP dashboard & API"
	@echo "make mcp           Start Model Context Protocol (MCP) stdio server"
	@echo "make clean         Remove bytecode, cache, and temporary artifacts"
	@echo "make docker-build  Build Docker production container"
	@echo "make docker-run    Run Docker container on port 8000"

test:
	$(PYTHON) -m unittest discover -s tests -v

run:
	$(PYTHON) run.py

mcp:
	$(PYTHON) mcp_server.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache build dist *.egg-info

docker-build:
	docker build -t logiswarm:latest .

docker-run:
	docker run -p 8000:8000 -it --rm --name logiswarm-app logiswarm:latest
