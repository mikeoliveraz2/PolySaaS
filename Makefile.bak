.PHONY: help install install-dev test lint format clean run docker-build docker-up docker-down

help:
	@echo "PolySaaS Makefile Commands"
	@echo "=========================="
	@echo "install          - Install production dependencies"
	@echo "install-dev      - Install development dependencies"
	@echo "test             - Run tests"
	@echo "test-cov         - Run tests with coverage"
	@echo "lint             - Run linters (ruff, mypy)"
	@echo "format           - Format code with black"
	@echo "clean            - Remove build artifacts and cache"
	@echo "run              - Run the application"
	@echo "docker-build     - Build Docker image"
	@echo "docker-up        - Start Docker containers"
	@echo "docker-down      - Stop Docker containers"

install:
	pip install -r requirements.txt
	pip install -e .

install-dev:
	pip install -r requirements-dev.txt
	pip install -e .

test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=polysaas --cov-report=html --cov-report=term-missing

lint:
	ruff check src/
	mypy src/

format:
	black src/ tests/
	ruff check --fix src/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ htmlcov/ .coverage

run:
	uvicorn polysaas.main:app --reload

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-clean:
	docker-compose down -v
