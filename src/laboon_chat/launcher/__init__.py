"""
P2P Messaging Launcher
=====================

Minimal browser launcher for decentralized P2P messaging.
Opens the web interface in the user's default browser with security optimizations.

🌐 Bringing decentralized communication to the surface 
   of your digital ocean with individual responsibility.
"""

from .laboon_launcher import P2PLauncher
from .browser_manager import BrowserManager

__all__ = [
    "P2PLauncher", 
    "BrowserManager"
]