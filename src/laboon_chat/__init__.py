"""
Decentralized P2P Messaging Platform
====================================

A truly decentralized messaging system where every individual is responsible
for themselves. No central authority, no single point of failure.

🌐 Peer-to-peer connections across digital networks 🔗

Author: Torrent-MSG Team
License: GPL-3.0
Version: 0.1.0-alpha
"""

__version__ = "0.1.0-alpha"
__author__ = "Torrent-MSG Team"
__license__ = "GPL-3.0"
__description__ = "Decentralized P2P Messaging Platform - Individual responsibility, collective freedom"

# Core imports
from .core import P2PCore, P2PCoreAPI
from .core.crypto_core import LaboonCrypto
from .core.identity import IdentityManager
from .core.messaging import LaboonMessaging
from .core.plugin_manager import LaboonPluginManager

__all__ = [
    "P2PCore",
    "P2PCoreAPI", 
    "LaboonCrypto",
    "IdentityManager",
    "LaboonMessaging",
    "LaboonPluginManager",
    "__version__",
    "__author__",
    "__license__",
    "__description__"
]