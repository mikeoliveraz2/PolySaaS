# PolySaaS Source Code

This directory will contain the Python FastAPI application source code.

## Planned Structure

```
src/
└── polysaas/
    ├── __init__.py
    ├── main.py          # FastAPI app entry point
    ├── cli.py           # Command-line interface
    ├── api/             # API routes
    │   ├── __init__.py
    │   ├── v1/
    │   │   ├── __init__.py
    │   │   ├── users.py
    │   │   ├── auth.py
    │   │   └── tenants.py
    ├── core/            # Core functionality
    │   ├── __init__.py
    │   ├── config.py
    │   ├── security.py
    │   └── dependencies.py
    ├── db/              # Database models and migrations
    │   ├── __init__.py
    │   ├── base.py
    │   └── session.py
    ├── models/          # SQLAlchemy models
    │   ├── __init__.py
    │   ├── user.py
    │   └── tenant.py
    ├── schemas/         # Pydantic schemas
    │   ├── __init__.py
    │   ├── user.py
    │   └── tenant.py
    ├── services/        # Business logic
    │   ├── __init__.py
    │   ├── user_service.py
    │   └── tenant_service.py
    └── utils/           # Utility functions
        ├── __init__.py
        └── helpers.py
```

## Status

**Status**: Planned - Not yet implemented

The FastAPI application structure from the `copilot/import-project-to-github` branch
will be added in a future iteration. The current merge focuses on:

1. WordPress website (already present)
2. Documentation files (completed)
3. Configuration files (completed)
4. Repository structure (completed)

## Next Steps

To add the FastAPI application:

1. Review the `copilot/import-project-to-github` branch
2. Extract the Python application code
3. Test the application locally
4. Integrate with the WordPress frontend
5. Set up CI/CD for Python code

## Development

Once implemented, you can run the application with:

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn src.polysaas.main:app --reload

# Run with Docker
docker-compose up
```

## Documentation

See the main [README.md](../README.md) for overall project documentation.
