# WeatherAI Backend Makefile
# Development targets for the modularized backend

.PHONY: help install test lint format api clean

# Default target
help:
	@echo "WeatherAI Backend Development Commands"
	@echo ""
	@echo "  install     Install dependencies"
	@echo "  test        Run all tests"
	@echo "  test-unit   Run unit tests only"
	@echo "  test-domain Run domain layer tests"
	@echo "  test-app    Run application layer tests"
	@echo "  lint        Run linters (ruff, mypy)"
	@echo "  format      Format code (black, ruff)"
	@echo "  api         Start the API server (development)"
	@echo "  clean       Clean cache and temporary files"

# Install dependencies
install:
	pip install -e .
	pip install pytest pytest-asyncio mypy ruff black

# Run all tests
test:
	PYTHONPATH=. python -m pytest tests/ -v

# Run unit tests only
test-unit:
	PYTHONPATH=. python -m pytest tests/unit/ -v

# Run domain layer tests
test-domain:
	PYTHONPATH=. python -m pytest tests/unit/test_domain.py -v

# Run application layer tests
test-app:
	PYTHONPATH=. python -m pytest tests/unit/test_application.py -v

# Run linters
lint:
	ruff check app/ tests/
	mypy app/ --strict

# Format code
format:
	black app/ tests/
	ruff check --fix app/ tests/

# Start API server
api:
	PYTHONPATH=. uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Clean temporary files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +