"""
Abstract interfaces for LaboonChat v2.0 modular architecture
"""

from .security_interface import ISecurityModule
from .messaging_interface import IMessagingModule  
from .interface_interface import IInterfaceModule
from .network_interface import INetworkModule
from .secondary_plugin import ISecondaryPlugin

__all__ = [
    "ISecurityModule",
    "IMessagingModule",
    "IInterfaceModule", 
    "INetworkModule",
    "ISecondaryPlugin",
]