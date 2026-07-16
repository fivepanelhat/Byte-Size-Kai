"""
setup.py - Byte Size Kai Package Configuration

Enables installation via 'pip install .' or 'pip install -e .'
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
 long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
 requirements = [
 line.strip()
 for line in fh
 if line.strip() and not line.startswith("#")
 ]

setup(
 name="byte_size_kai",
 version="1.3.0",
 author="Coastal Alpine Tech Limited",
 author_email="info@coastalalpine.co.nz",
 description="Byte Size Kai - sovereign multi-modal edge agritech for microgreens / Mana Kai",
 long_description=long_description,
 long_description_content_type="text/markdown",
 url="https://github.com/fivepanelhat/Byte-Size-Kai",
 project_urls={
 "Bug Tracker": "https://github.com/fivepanelhat/Byte-Size-Kai/issues",
 "Documentation": "https://github.com/fivepanelhat/Byte-Size-Kai/wiki",
 "Source Code": "https://github.com/fivepanelhat/Byte-Size-Kai",
 },
 packages=find_packages(),
 classifiers=[
 "Development Status :: 3 - Alpha",
 "Environment :: No Input/Output (Daemon)",
 "Intended Audience :: Developers",
 "Intended Audience :: Science/Research",
 "License :: Other/Proprietary License",
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
 "byte-size-kai=main:main",
 "blue-moon-portal=main:main", # back-compat
 ],
 },
 keywords="byte-size-kai agriculture IoT edge-ai microgreens automation crop-tracking mana-kai",
 include_package_data=True,
)
