"""
Messaging Core Plugins Package for LaboonChat v2.0

This package contains core messaging plugins that provide essential
messaging functionality for the LaboonChat application.
"""

from .simple_p2p_messaging import SimpleP2PMessaging, create_simple_p2p_messaging

__all__ = [
    "SimpleP2PMessaging",
    "create_simple_p2p_messaging"
]

# Plugin metadata
PLUGIN_INFO = {
    "name": "Messaging Core Plugins",
    "version": "1.0.0",
    "description": "Core messaging plugins for LaboonChat v2.0",
    "author": "LaboonChat Team",
    "plugins": {
        "SimpleP2PMessaging": {
            "class": SimpleP2PMessaging,
            "factory": create_simple_p2p_messaging,
            "type": "core",
            "category": "messaging",
            "description": "Simple P2P messaging with file transfer support"
        }
    }
}