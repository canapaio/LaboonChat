"""
Advanced Features Package - Plugin Secondari Avanzati per LaboonChat2

Questo package contiene plugin secondari che forniscono funzionalità avanzate:
- ChatBot: Assistente AI conversazionale intelligente
- AdvancedFileSharing: Condivisione file P2P con funzionalità avanzate
- AdvancedEncryption: Sistema crittografico avanzato con algoritmi multipli

Tutti i plugin implementano l'interfaccia ISecondaryPlugin e possono essere
utilizzati per estendere le funzionalità base di LaboonChat2.
"""

# Import plugin principali
from .chatbot_plugin import (
    ChatBotPlugin,
    BotPersonality,
    ResponseType,
    BotCommand,
    BotResponse,
    ConversationContext,
    BotStats,
    create_chatbot_plugin,
    DEFAULT_CONFIG as CHATBOT_DEFAULT_CONFIG
)

from .advanced_file_sharing import (
    AdvancedFileSharing,
    TransferStatus,
    ChunkStatus,
    CompressionType,
    FileChunk,
    FileMetadata,
    TransferProgress,
    PeerInfo,
    TransferStats,
    create_advanced_file_sharing,
    DEFAULT_CONFIG as FILE_SHARING_DEFAULT_CONFIG
)

from .advanced_encryption import (
    AdvancedEncryption,
    EncryptionAlgorithm,
    KeyType,
    OperationType,
    CryptoKey,
    EncryptionResult,
    CryptoOperation,
    SteganographyResult,
    CryptoStats,
    create_advanced_encryption,
    DEFAULT_CONFIG as ENCRYPTION_DEFAULT_CONFIG
)

# Export pubblici
__all__ = [
    # ChatBot Plugin
    "ChatBotPlugin",
    "BotPersonality",
    "ResponseType", 
    "BotCommand",
    "BotResponse",
    "ConversationContext",
    "BotStats",
    "create_chatbot_plugin",
    "CHATBOT_DEFAULT_CONFIG",
    
    # Advanced File Sharing Plugin
    "AdvancedFileSharing",
    "TransferStatus",
    "ChunkStatus",
    "CompressionType",
    "FileChunk",
    "FileMetadata",
    "TransferProgress",
    "PeerInfo",
    "TransferStats",
    "create_advanced_file_sharing",
    "FILE_SHARING_DEFAULT_CONFIG",
    
    # Advanced Encryption Plugin
    "AdvancedEncryption",
    "EncryptionAlgorithm",
    "KeyType",
    "OperationType",
    "CryptoKey",
    "EncryptionResult",
    "CryptoOperation",
    "SteganographyResult",
    "CryptoStats",
    "create_advanced_encryption",
    "ENCRYPTION_DEFAULT_CONFIG"
]

# Informazioni package
__version__ = "1.0.0"
__author__ = "LaboonChat2 Team"
__description__ = "Plugin secondari avanzati per LaboonChat2"

# Registry dei plugin disponibili
AVAILABLE_PLUGINS = {
    "chatbot": {
        "class": ChatBotPlugin,
        "factory": create_chatbot_plugin,
        "config": CHATBOT_DEFAULT_CONFIG,
        "description": "Assistente AI conversazionale intelligente",
        "category": "ai_assistant",
        "dependencies": ["messaging"],
        "optional_dependencies": ["network", "interface"]
    },
    "advanced_file_sharing": {
        "class": AdvancedFileSharing,
        "factory": create_advanced_file_sharing,
        "config": FILE_SHARING_DEFAULT_CONFIG,
        "description": "Condivisione file P2P con funzionalità avanzate",
        "category": "file_transfer",
        "dependencies": ["messaging", "network"],
        "optional_dependencies": ["security", "interface"]
    },
    "advanced_encryption": {
        "class": AdvancedEncryption,
        "factory": create_advanced_encryption,
        "config": ENCRYPTION_DEFAULT_CONFIG,
        "description": "Sistema crittografico avanzato con algoritmi multipli",
        "category": "security",
        "dependencies": ["security"],
        "optional_dependencies": ["messaging", "network", "interface"]
    }
}


def get_available_plugins():
    """
    Restituisce lista dei plugin disponibili
    
    Returns:
        Dict con informazioni sui plugin disponibili
    """
    return AVAILABLE_PLUGINS.copy()


def create_plugin(plugin_name: str, config: dict = None):
    """
    Factory function generica per creare plugin
    
    Args:
        plugin_name: Nome del plugin da creare
        config: Configurazione personalizzata (opzionale)
    
    Returns:
        Istanza del plugin richiesto
    
    Raises:
        ValueError: Se il plugin non è disponibile
    """
    if plugin_name not in AVAILABLE_PLUGINS:
        available = ", ".join(AVAILABLE_PLUGINS.keys())
        raise ValueError(f"Plugin '{plugin_name}' non disponibile. Disponibili: {available}")
    
    plugin_info = AVAILABLE_PLUGINS[plugin_name]
    factory_func = plugin_info["factory"]
    
    if config is None:
        config = plugin_info["config"].copy()
    
    return factory_func(config)


def get_plugin_info(plugin_name: str):
    """
    Restituisce informazioni su un plugin specifico
    
    Args:
        plugin_name: Nome del plugin
    
    Returns:
        Dict con informazioni del plugin o None se non trovato
    """
    return AVAILABLE_PLUGINS.get(plugin_name)


def list_plugins_by_category(category: str = None):
    """
    Lista plugin filtrati per categoria
    
    Args:
        category: Categoria da filtrare (opzionale)
    
    Returns:
        Dict con plugin della categoria specificata
    """
    if category is None:
        return AVAILABLE_PLUGINS.copy()
    
    filtered_plugins = {
        name: info for name, info in AVAILABLE_PLUGINS.items()
        if info.get("category") == category
    }
    
    return filtered_plugins


def validate_plugin_dependencies(plugin_name: str, available_modules: list):
    """
    Valida se le dipendenze di un plugin sono soddisfatte
    
    Args:
        plugin_name: Nome del plugin
        available_modules: Lista dei moduli disponibili
    
    Returns:
        Tuple (is_valid, missing_dependencies, missing_optional)
    """
    if plugin_name not in AVAILABLE_PLUGINS:
        return False, [], []
    
    plugin_info = AVAILABLE_PLUGINS[plugin_name]
    
    # Verifica dipendenze obbligatorie
    required_deps = plugin_info.get("dependencies", [])
    missing_required = [dep for dep in required_deps if dep not in available_modules]
    
    # Verifica dipendenze opzionali
    optional_deps = plugin_info.get("optional_dependencies", [])
    missing_optional = [dep for dep in optional_deps if dep not in available_modules]
    
    is_valid = len(missing_required) == 0
    
    return is_valid, missing_required, missing_optional