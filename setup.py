"""Setuptools metadata only. The PolySaaS app is Django; install deps with requirements.txt."""
from setuptools import setup

setup(
    name="polysaas",
    version="0.1.0",
    description="PolySaaS / DOSE — Django platform (see README.md).",
    long_description="Install with: pip install -r requirements.txt",
    long_description_content_type="text/plain",
    url="https://github.com/mikeoliveraz2/PolySaaS",
    packages=[],
    python_requires=">=3.11",
)
