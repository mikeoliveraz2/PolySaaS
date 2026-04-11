# Contributing to PolySaaS

First off, thank you for considering contributing to PolySaaS! It's people like you that make PolySaaS such a great tool.

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the issue list as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

* **Use a clear and descriptive title**
* **Describe the exact steps which reproduce the problem**
* **Provide specific examples to demonstrate the steps**
* **Describe the behavior you observed after following the steps**
* **Explain which behavior you expected to see instead and why**
* **Include screenshots if relevant**

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

* **Use a clear and descriptive title**
* **Provide a step-by-step description of the suggested enhancement**
* **Provide specific examples to demonstrate the steps**
* **Describe the current behavior and explain which behavior you expected to see instead**
* **Explain why this enhancement would be useful**

### Pull Requests

* Fill in the required template
* Do not include issue numbers in the PR title
* Follow the Python style guide (PEP 8)
* Include thoughtfully-worded, well-structured tests
* Document new code
* End all files with a newline

## Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR-USERNAME/PolySaaS.git
   cd PolySaaS
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install development dependencies:
   ```bash
   make install-dev
   # or
   pip install -r requirements-dev.txt
   pip install -e .
   ```

5. Create a branch:
   ```bash
   git checkout -b feature/my-new-feature
   ```

## Development Workflow

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test
pytest tests/test_main.py -v
```

### Code Quality

```bash
# Format code
make format

# Run linters
make lint

# Or manually:
black src/ tests/
ruff check src/
mypy src/
```

### Running the Application

```bash
# Run locally
make run

# Or with Docker
make docker-up
```

## Style Guidelines

### Python Style Guide

* Follow PEP 8
* Use type hints
* Write docstrings for all public modules, functions, classes, and methods
* Keep functions focused and small
* Use meaningful variable names

### Git Commit Messages

* Use the present tense ("Add feature" not "Added feature")
* Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
* Limit the first line to 72 characters or less
* Reference issues and pull requests liberally after the first line

Example:
```
Add user authentication endpoints

- Implement JWT token generation
- Add login and logout endpoints
- Include password hashing utilities

Fixes #123
```

### Documentation

* Keep README.md up to date
* Comment your code where necessary
* Update API documentation
* Add docstrings to new functions/classes

## Testing

* Write tests for new features
* Ensure all tests pass before submitting PR
* Aim for high code coverage
* Use meaningful test names

## Project Structure

Please maintain the existing project structure:

```
src/polysaas/
├── api/              # API routes
├── core/             # Core functionality
├── db/               # Database
├── models/           # Data models
├── schemas/          # Pydantic schemas
├── services/         # Business logic
└── utils/            # Utilities
```

## Questions?

Feel free to open an issue with your question or reach out to the maintainers.

Thank you for contributing! 🎉
