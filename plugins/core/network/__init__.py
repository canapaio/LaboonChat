"""
Network Plugins Package per LaboonChat2

Questo package contiene i plugin di rete core per LaboonChat2.
"""

from .basic_network import (
    BasicNetworkModule,
    NetworkPeer,
    NetworkConnection,
    NetworkMessage,
    NetworkStats,
    ConnectionStatus,
    PeerType,
    MessagePriority,
    DEFAULT_CONFIG,
    create_basic_network_module
)

__all__ = [
    "BasicNetworkModule",
    "NetworkPeer", 
    "NetworkConnection",
    "NetworkMessage",
    "NetworkStats",
    "ConnectionStatus",
    "PeerType",
    "MessagePriority",
    "DEFAULT_CONFIG",
    "create_basic_network_module"
]