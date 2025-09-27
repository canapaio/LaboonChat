"""
LaboonChat Setup Configuration
=============================

🐋 Faithful connections across digital oceans 🌊

Setup script for LaboonChat - Secure P2P Messaging Platform
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    with open(requirements_path, "r", encoding="utf-8") as f:
        requirements = [
            line.strip() 
            for line in f 
            if line.strip() and not line.startswith("#") and not line.startswith("-")
        ]

setup(
    name="laboon-chat",
    version="0.1.0-alpha",
    author="Torrent-MSG Team",
    author_email="team@laboon-chat.org",
    description="Secure P2P Messaging Platform - Faithful connections across digital oceans",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/torrent-msg/LaboonChat",
    project_urls={
        "Bug Reports": "https://github.com/torrent-msg/LaboonChat/issues",
        "Source": "https://github.com/torrent-msg/LaboonChat",
        "Documentation": "https://laboon-chat.readthedocs.io/",
    },
    
    # Package configuration
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    
    # Python version requirement
    python_requires=">=3.9",
    
    # Dependencies
    install_requires=requirements,
    
    # Optional dependencies
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.9.0",
            "flake8>=6.1.0",
            "mypy>=1.6.0",
            "pre-commit>=3.5.0",
        ],
        "docs": [
            "sphinx>=7.2.0",
            "sphinx-rtd-theme>=1.3.0",
        ],
        "performance": [
            "uvloop>=0.19.0",
            "orjson>=3.9.0",
        ],
    },
    
    # Entry points
    entry_points={
        "console_scripts": [
            "laboon-chat=laboon_chat.launcher.laboon_launcher:main",
            "laboon=laboon_chat.launcher.laboon_launcher:main",
            "lc=laboon_chat.launcher.laboon_launcher:main",
        ],
    },
    
    # Package data
    package_data={
        "laboon_chat": [
            "ui/templates/*.html",
            "ui/static/css/*.css",
            "ui/static/js/*.js",
            "config/*.json",
            "config/*.yaml",
        ],
    },
    
    # Classifiers
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Communications :: Chat",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Security :: Cryptography",
        "Topic :: System :: Networking",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: Web Environment",
        "Natural Language :: English",
        "Natural Language :: Italian",
    ],
    
    # Keywords
    keywords=[
        "p2p", "messaging", "chat", "secure", "privacy", 
        "decentralized", "encryption", "torrent", "laboon",
        "one-piece", "whale", "ocean", "faithful", "connections"
    ],
    
    # License
    license="GPL-3.0",
    
    # Zip safe
    zip_safe=False,
)