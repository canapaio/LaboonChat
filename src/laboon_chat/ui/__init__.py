"""
P2P Messaging Web UI
===================

Modern web interface for decentralized P2P messaging with dark creamy theme.
Secure connections across digital networks through beautiful design.

🌐 UI Components:
- WebServer: Async HTTP server with security
- ChatInterface: Real-time messaging UI  
- SecurityIndicators: Visual security system
"""

from .web_server import WebServer
from .chat_interface import ChatInterface

__all__ = [
    "WebServer",
    "ChatInterface"
]