# PolySaaS Documentation

Welcome to the PolySaaS (Dynamic Orchestration Service Engine) documentation.

## Overview

PolySaaS is a dynamic orchestration service engine designed to manage and orchestrate complex workflows and services.

## Features

- **RESTful API**: FastAPI-based REST API for service management
- **Async Operations**: Built on async/await for high performance
- **Task Orchestration**: Create, monitor, and manage orchestration tasks
- **Scalable Architecture**: Designed for horizontal scaling
- **Database Support**: PostgreSQL with async support
- **Caching**: Redis integration for high-performance caching
- **Background Tasks**: Celery integration for async task processing
- **Security**: JWT-based authentication and authorization

## Getting Started

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

Create a `.env` file in the project root:

```env
# Application
PROJECT_NAME=PolySaaS
DEBUG=true

# Server
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/polysaas

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-here
```

### Running the Application

```bash
# Using the CLI
polysaas start

# Or directly with Python
python -m polysaas.main

# Or with uvicorn
uvicorn polysaas.main:app --reload
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=polysaas

# Run specific test file
pytest tests/test_main.py
```

## API Documentation

Once the application is running, visit:

- **Swagger UI**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc
- **OpenAPI JSON**: http://localhost:8000/api/v1/openapi.json

## Architecture

### Project Structure

```
PolySaaS/
├── src/polysaas/
│   ├── api/              # API routes and endpoints
│   ├── core/             # Core configuration and utilities
│   ├── db/               # Database models and session
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic services
│   └── utils/            # Utility functions
├── tests/                # Test files
├── docs/                 # Documentation
├── requirements.txt      # Python dependencies
└── setup.py             # Package setup
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.
