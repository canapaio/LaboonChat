"""
Core Interface Plugins for LaboonChat v2.0

This package contains core interface plugins that provide
user interface capabilities for LaboonChat.
"""

from .web_interface import WebInterface, create_web_interface

# Export delle classi principali
__all__ = [
    "WebInterface",
    "create_web_interface"
]

# Metadata del package
__version__ = "1.0.0"
__author__ = "LaboonChat Team"
__description__ = "Core interface plugins for LaboonChat v2.0"

# Plugin registry per il sistema modulare
PLUGIN_REGISTRY = {
    "WebInterface": {
        "class": WebInterface,
        "factory": create_web_interface,
        "type": "core",
        "category": "interface",
        "description": "Modern web-based interface with real-time messaging"
    }
}

# Configurazioni di default per i plugin
DEFAULT_CONFIGS = {
    "WebInterface": {
        "host": "localhost",
        "port": 8080,
        "auto_open": True,
        "theme": "default",
        "static_dir": "static",
        "templates_dir": "templates"
    }
}