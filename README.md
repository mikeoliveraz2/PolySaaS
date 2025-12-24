# PolySaaS

A comprehensive multi-tenant SaaS platform combining a FastAPI backend with WordPress frontend capabilities.

## Project Structure

This repository contains:

### WordPress Website
- Location: `website/` directory
- Multi-environment setup (sandbox, staging)
- Custom PolySaaS Pro theme
- Development and staging configurations

### FastAPI Backend (Planned/In Progress)
- Python-based SaaS application
- Multi-tenant architecture
- RESTful API design
- Authentication and authorization system

## Documentation

This project includes comprehensive documentation:

- **[VS Code to GitHub Guide](VSCODE_TO_GITHUB_GUIDE.md)** - Guide for importing VS Code projects to GitHub
- **[Branch Promotion Guide](BRANCH_PROMOTION_GUIDE.md)** - Guide for promoting branches through environments
- **[Quick Start Promotion](QUICK_START_PROMOTION.md)** - Quick reference for branch promotion workflows
- **[Workflow Diagram](WORKFLOW_DIAGRAM.md)** - Visual diagrams of development workflows
- **[Import Summary](IMPORT_SUMMARY.md)** - Summary of project import process
- **[Contributing Guidelines](CONTRIBUTING.md)** - How to contribute to this project

## Getting Started

### Prerequisites
- Python 3.8+
- Node.js (for WordPress tooling)
- Docker (for containerized deployments)
- Git

### Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/PolySaaS.git
cd PolySaaS
```

2. Set up Python environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Copy environment configuration:
```bash
cp .env.example .env
# Edit .env with your configuration
```

### Development

For WordPress development, see the WordPress setup documentation in `website/`.

For FastAPI backend development (once implemented):
```bash
# Run development server
python -m uvicorn src.polysaas.main:app --reload

# Run tests
pytest

# Run linting
make lint
```

**Note**: The FastAPI application is documented but not yet implemented. See `src/README.md` for planned structure.

## Repository Structure

```
PolySaaS/
├── website/              # WordPress website files
│   ├── sandbox/          # Development environment
│   ├── staging/          # Staging environment
│   └── PolySaaS-WordPress/  # WordPress configurations
├── src/                  # Python source code (FastAPI)
│   └── polysaas/        # Main application package
├── tests/                # Test files
├── docs/                 # Additional documentation
├── .github/              # GitHub Actions workflows
├── docker-compose.yml    # Docker configuration
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Branch Strategy

This project uses a multi-branch strategy:
- `main` - Production-ready code
- `staging` - Pre-production testing
- `develop` - Active development
- Feature branches - For individual features

See [Branch Promotion Guide](BRANCH_PROMOTION_GUIDE.md) for more details.

## Deployment

### Docker Deployment
```bash
docker-compose up -d
```

### Production Deployment
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Security

- SFTP credentials are excluded from version control
- Sensitive configuration is managed through environment variables
- WordPress uploads and cache directories are gitignored
- See `.gitignore` for complete list of excluded files

## Support

For issues, questions, or contributions, please open an issue on GitHub.

## Project Status

This project is under active development. The repository consolidates multiple development branches:
- WordPress website (completed)
- Documentation and guides (completed)
- FastAPI backend implementation (in progress)

## Merged Branches

This main branch represents the merged state of:
1. `copilot/import-project-to-github` - FastAPI application structure
2. `copilot/import-vscode-project-github` - VS Code import documentation
3. `copilot/promote-subset-clean-branch` - Branch promotion guides
4. `copilot/push-branch-to-main` - Security improvements and configuration
5. `copilot/merge-all-branches-into-main` - Integration planning
6. `copilot/refactor-multiple-classes-into-one` - Code refactoring
7. `subset-clean` - Clean WordPress subset

All branch-specific content has been integrated into this unified codebase.
