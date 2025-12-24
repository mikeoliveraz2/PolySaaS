# PolySaaS

> The final product that had the code name `/dose/` for Dynamic Orchestration Service Engine

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## Overview

PolySaaS is a powerful Dynamic Orchestration Service Engine (DOSE) designed to manage, orchestrate, and coordinate complex workflows and services in a scalable, production-ready environment.

## Features

✨ **Modern Python Stack**
- Built with FastAPI for high performance
- Async/await throughout for efficient I/O operations
- Type hints and Pydantic validation

🚀 **Production Ready**
- RESTful API with automatic OpenAPI documentation
- Database integration with SQLAlchemy and PostgreSQL
- Redis caching for performance
- Celery for background task processing
- JWT-based authentication and security

🔧 **Developer Friendly**
- Comprehensive test suite with pytest
- Code quality tools (Black, Ruff, MyPy)
- Docker support (coming soon)
- Extensive documentation

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/mikeoliveraz2/PolySaaS.git
cd PolySaaS

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Configuration

Copy the example environment file and configure:

```bash
cp .env.example .env
# Edit .env with your configuration
```

### Run the Application

```bash
# Using the CLI
polysaas start

# Or directly
python -m polysaas.main

# Development mode with auto-reload
polysaas start --reload
```

### Access the API

Once running, access:
- API Documentation: http://localhost:8000/api/v1/docs
- Alternative Docs: http://localhost:8000/api/v1/redoc
- Health Check: http://localhost:8000/health

## Development

### Install Development Dependencies

```bash
pip install -r requirements-dev.txt
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=polysaas --cov-report=html

# Run specific tests
pytest tests/test_main.py -v
```

### Code Quality

```bash
# Format code with Black
black src/

# Lint with Ruff
ruff check src/

# Type check with MyPy
mypy src/
```

## Project Structure

```
PolySaaS/
├── src/polysaas/          # Main application code
│   ├── api/               # API routes and endpoints
│   │   └── v1/           # API version 1
│   ├── core/             # Core configuration
│   ├── db/               # Database configuration
│   ├── models/           # Database models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   └── utils/            # Utility functions
├── tests/                # Test suite
├── docs/                 # Documentation
├── requirements.txt      # Production dependencies
├── requirements-dev.txt  # Development dependencies
├── setup.py             # Package configuration
└── pyproject.toml       # Build configuration
```

## API Endpoints

### Health Checks
- `GET /health` - Main health check
- `GET /api/v1/health/` - API health status
- `GET /api/v1/health/readiness` - Readiness probe
- `GET /api/v1/health/liveness` - Liveness probe

### Orchestration
- `POST /api/v1/orchestration/tasks` - Create orchestration task
- `GET /api/v1/orchestration/tasks` - List all tasks
- `GET /api/v1/orchestration/tasks/{task_id}` - Get task details
- `DELETE /api/v1/orchestration/tasks/{task_id}` - Cancel task

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Documentation

For detailed documentation, see the [docs](docs/) directory.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues and questions, please use the GitHub issues tracker.
