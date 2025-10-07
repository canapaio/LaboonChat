"""
LaboonChat v2.0 - Modular P2P Secure Messaging

La nuova generazione di LaboonChat con architettura modulare avanzata.
"""

__version__ = "2.0.0"
__author__ = "LaboonChat Team"
__email__ = "team@laboonchat.org"
__license__ = "MIT"

from .core.plugin_manager import ModularPluginManager, PluginType, PluginStatus
from .core.application import LaboonChat2Application

__all__ = [
    "ModularPluginManager",
    "PluginType", 
    "PluginCategory",
    "LaboonChat2Application",
    "__version__",
]