"""
Security Core Plugins Package for LaboonChat v2.0

This package contains core security plugins that provide essential
security functionality for the LaboonChat application.
"""

from .basic_security import BasicSecurityModule, create_basic_security_module

__all__ = [
    "BasicSecurityModule",
    "create_basic_security_module"
]

# Plugin metadata
PLUGIN_INFO = {
    "name": "Security Core Plugins",
    "version": "1.0.0",
    "description": "Core security plugins for LaboonChat v2.0",
    "author": "LaboonChat Team",
    "plugins": {
        "BasicSecurityModule": {
            "class": BasicSecurityModule,
            "factory": create_basic_security_module,
            "type": "core",
            "category": "security",
            "description": "Basic security module with Ed25519/AES-GCM encryption"
        }
    }
}