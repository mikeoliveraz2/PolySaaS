"""Setup configuration for PolySaaS."""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="polysaas",
    version="0.1.0",
    author="PolySaaS Team",
    description="Dynamic Orchestration Service Engine (DOSE)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mikeoliveraz2/PolySaaS",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "fastapi>=0.100.0",
        "uvicorn[standard]>=0.23.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "sqlalchemy>=2.0.0",
        "alembic>=1.11.0",
        "asyncpg>=0.28.0",
        "redis>=4.6.0",
        "celery>=5.3.0",
        "python-jose[cryptography]>=3.3.0",
        "passlib[bcrypt]>=1.7.4",
        "python-multipart>=0.0.6",
        "aiofiles>=23.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "ruff>=0.0.280",
            "mypy>=1.4.0",
            "pre-commit>=3.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "polysaas=polysaas.cli:main",
        ],
    },
)
