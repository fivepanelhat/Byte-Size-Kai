"""
setup.py - Blue Moon Portal Package Configuration

Enables installation via 'pip install .' or 'pip install -e .'
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [
        line.strip() for line in fh if line.strip() and not line.startswith("#")
    ]

setup(
    name="blue-moon-portal",
    version="0.1.0",
    author="Coastal Alpine Tech Limited",
    author_email="info@coastalalpine.co.nz",
    description="Autonomous on-premise agritech crop tracker with edge AI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/blue-moon-portal",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/blue-moon-portal/issues",
        "Documentation": "https://github.com/yourusername/blue-moon-portal/wiki",
        "Source Code": "https://github.com/yourusername/blue-moon-portal",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: No Input/Output (Daemon)",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: System :: Monitoring",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4",
            "pytest-asyncio>=0.21",
            "pytest-cov>=4.1",
            "black>=23.12",
            "mypy>=1.7",
            "pylint>=3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "blue-moon-portal=main:main",
        ],
    },
    keywords="agriculture IoT edge-ai microgreens automation crop-tracking",
    include_package_data=True,
)
