"""
Configuration Loader for LaboonChat v2.0

Handles loading, validation, and management of application configurations.
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
import jsonschema
from jsonschema import validate, ValidationError


@dataclass
class LoggingConfig:
    """Configurazione logging."""
    level: str = "INFO"
    file: str = "logs/laboon_chat2.log"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    max_size_mb: int = 10
    backup_count: int = 5


@dataclass
class PluginConfig:
    """Configurazione plugin."""
    core_plugins_path: str = "plugins/core"
    secondary_plugins_path: str = "plugins/secondary"
    auto_load_core: bool = True
    auto_load_secondary: bool = False
    hot_swap_enabled: bool = True


@dataclass
class SecurityConfig:
    """Configurazione sicurezza."""
    encryption_algorithm: str = "AES-256-GCM"
    key_derivation: str = "PBKDF2"
    signature_algorithm: str = "Ed25519"
    hash_algorithm: str = "SHA-256"
    key_rotation_hours: int = 24
    max_message_size_mb: int = 100


@dataclass
class NetworkConfig:
    """Configurazione rete."""
    default_port: int = 8888
    max_connections: int = 100
    connection_timeout: int = 30
    discovery_interval: int = 60
    heartbeat_interval: int = 10
    buffer_size: int = 8192


@dataclass
class InterfaceConfig:
    """Configurazione interfaccia."""
    default_theme: str = "dark"
    auto_scroll: bool = True
    max_history_messages: int = 1000
    notification_enabled: bool = True
    sound_enabled: bool = True


@dataclass
class ApplicationConfig:
    """Configurazione completa dell'applicazione."""
    app_name: str = "LaboonChat v2.0"
    version: str = "2.0.0"
    debug: bool = False
    
    logging: LoggingConfig = None
    plugins: PluginConfig = None
    security: SecurityConfig = None
    network: NetworkConfig = None
    interface: InterfaceConfig = None
    
    default_core_plugins: Dict[str, str] = None
    default_secondary_plugins: list = None
    plugin_configurations: Dict[str, Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.logging is None:
            self.logging = LoggingConfig()
        if self.plugins is None:
            self.plugins = PluginConfig()
        if self.security is None:
            self.security = SecurityConfig()
        if self.network is None:
            self.network = NetworkConfig()
        if self.interface is None:
            self.interface = InterfaceConfig()
        if self.default_core_plugins is None:
            self.default_core_plugins = {
                "security": "basic_security",
                "messaging": "simple_p2p",
                "interface": "web_interface",
                "network": "basic_network"
            }
        if self.default_secondary_plugins is None:
            self.default_secondary_plugins = []
        if self.plugin_configurations is None:
            self.plugin_configurations = {}


class ConfigLoader:
    """
    Caricatore e gestore configurazioni per LaboonChat v2.0.
    
    Supporta:
    - Caricamento da file JSON
    - Validazione schema
    - Configurazioni di default
    - Merge configurazioni
    - Salvataggio configurazioni
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._config_schema = self._create_config_schema()
    
    async def load_config(
        self, 
        config_path: Union[str, Path],
        use_defaults: bool = True
    ) -> Dict[str, Any]:
        """
        Carica configurazione da file.
        
        Args:
            config_path: Percorso file configurazione
            use_defaults: Se usare valori di default per campi mancanti
            
        Returns:
            Dict: Configurazione caricata
            
        Raises:
            FileNotFoundError: Se file non trovato
            ValidationError: Se configurazione non valida
        """
        config_path = Path(config_path)
        
        try:
            # Carica configurazione base
            if use_defaults:
                config = asdict(ApplicationConfig())
            else:
                config = {}
            
            # Se file esiste, carica e merge
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                
                # Merge configurazioni
                config = self._merge_configs(config, file_config)
                
                self.logger.info(f"Configurazione caricata da {config_path}")
            else:
                self.logger.warning(f"File configurazione {config_path} non trovato, uso defaults")
                
                # Crea file con configurazione di default
                await self.save_config(config, config_path)
            
            # Valida configurazione
            self._validate_config(config)
            
            # Post-processing
            config = self._post_process_config(config)
            
            return config
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Errore parsing JSON: {e}")
        except ValidationError as e:
            raise ValueError(f"Configurazione non valida: {e.message}")
        except Exception as e:
            self.logger.error(f"Errore caricamento configurazione: {e}")
            raise
    
    async def save_config(
        self, 
        config: Dict[str, Any], 
        config_path: Union[str, Path]
    ) -> bool:
        """
        Salva configurazione su file.
        
        Args:
            config: Configurazione da salvare
            config_path: Percorso file di destinazione
            
        Returns:
            bool: True se salvataggio riuscito
        """
        config_path = Path(config_path)
        
        try:
            # Crea directory se non esiste
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Valida prima di salvare
            self._validate_config(config)
            
            # Salva con formattazione
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"Configurazione salvata in {config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Errore salvataggio configurazione: {e}")
            return False
    
    def create_default_config(self) -> Dict[str, Any]:
        """
        Crea configurazione di default.
        
        Returns:
            Dict: Configurazione di default
        """
        return asdict(ApplicationConfig())
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Valida una configurazione.
        
        Args:
            config: Configurazione da validare
            
        Returns:
            bool: True se valida
            
        Raises:
            ValidationError: Se configurazione non valida
        """
        try:
            self._validate_config(config)
            return True
        except ValidationError:
            return False
    
    def merge_configs(
        self, 
        base_config: Dict[str, Any], 
        override_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge due configurazioni.
        
        Args:
            base_config: Configurazione base
            override_config: Configurazione che sovrascrive
            
        Returns:
            Dict: Configurazione merged
        """
        return self._merge_configs(base_config, override_config)
    
    def get_plugin_config(
        self, 
        config: Dict[str, Any], 
        plugin_name: str
    ) -> Dict[str, Any]:
        """
        Estrae configurazione specifica di un plugin.
        
        Args:
            config: Configurazione completa
            plugin_name: Nome del plugin
            
        Returns:
            Dict: Configurazione del plugin
        """
        plugin_configs = config.get("plugin_configurations", {})
        return plugin_configs.get(plugin_name, {})
    
    def set_plugin_config(
        self, 
        config: Dict[str, Any], 
        plugin_name: str, 
        plugin_config: Dict[str, Any]
    ) -> None:
        """
        Imposta configurazione di un plugin.
        
        Args:
            config: Configurazione completa
            plugin_name: Nome del plugin
            plugin_config: Configurazione del plugin
        """
        if "plugin_configurations" not in config:
            config["plugin_configurations"] = {}
        
        config["plugin_configurations"][plugin_name] = plugin_config
    
    # === Private Methods ===
    
    def _merge_configs(
        self, 
        base: Dict[str, Any], 
        override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge ricorsivo di configurazioni."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """Valida configurazione contro schema."""
        try:
            validate(instance=config, schema=self._config_schema)
        except ValidationError as e:
            self.logger.error(f"Errore validazione configurazione: {e.message}")
            raise
    
    def _post_process_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Post-processing della configurazione."""
        # Espandi percorsi relativi
        if "plugins" in config:
            plugins_config = config["plugins"]
            if "core_plugins_path" in plugins_config:
                plugins_config["core_plugins_path"] = os.path.abspath(
                    plugins_config["core_plugins_path"]
                )
            if "secondary_plugins_path" in plugins_config:
                plugins_config["secondary_plugins_path"] = os.path.abspath(
                    plugins_config["secondary_plugins_path"]
                )
        
        # Crea directory logs se specificata
        if "logging" in config and "file" in config["logging"]:
            log_file = Path(config["logging"]["file"])
            log_file.parent.mkdir(parents=True, exist_ok=True)
        
        return config
    
    def _create_config_schema(self) -> Dict[str, Any]:
        """Crea schema JSON per validazione configurazione."""
        return {
            "type": "object",
            "properties": {
                "app_name": {"type": "string"},
                "version": {"type": "string"},
                "debug": {"type": "boolean"},
                
                "logging": {
                    "type": "object",
                    "properties": {
                        "level": {"type": "string", "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]},
                        "file": {"type": "string"},
                        "format": {"type": "string"},
                        "max_size_mb": {"type": "integer", "minimum": 1},
                        "backup_count": {"type": "integer", "minimum": 0}
                    }
                },
                
                "plugins": {
                    "type": "object",
                    "properties": {
                        "core_plugins_path": {"type": "string"},
                        "secondary_plugins_path": {"type": "string"},
                        "auto_load_core": {"type": "boolean"},
                        "auto_load_secondary": {"type": "boolean"},
                        "hot_swap_enabled": {"type": "boolean"}
                    }
                },
                
                "security": {
                    "type": "object",
                    "properties": {
                        "encryption_algorithm": {"type": "string"},
                        "key_derivation": {"type": "string"},
                        "signature_algorithm": {"type": "string"},
                        "hash_algorithm": {"type": "string"},
                        "key_rotation_hours": {"type": "integer", "minimum": 1},
                        "max_message_size_mb": {"type": "integer", "minimum": 1}
                    }
                },
                
                "network": {
                    "type": "object",
                    "properties": {
                        "default_port": {"type": "integer", "minimum": 1, "maximum": 65535},
                        "max_connections": {"type": "integer", "minimum": 1},
                        "connection_timeout": {"type": "integer", "minimum": 1},
                        "discovery_interval": {"type": "integer", "minimum": 1},
                        "heartbeat_interval": {"type": "integer", "minimum": 1},
                        "buffer_size": {"type": "integer", "minimum": 1024}
                    }
                },
                
                "interface": {
                    "type": "object",
                    "properties": {
                        "default_theme": {"type": "string"},
                        "auto_scroll": {"type": "boolean"},
                        "max_history_messages": {"type": "integer", "minimum": 1},
                        "notification_enabled": {"type": "boolean"},
                        "sound_enabled": {"type": "boolean"}
                    }
                },
                
                "default_core_plugins": {
                    "type": "object",
                    "properties": {
                        "security": {"type": "string"},
                        "messaging": {"type": "string"},
                        "interface": {"type": "string"},
                        "network": {"type": "string"}
                    }
                },
                
                "default_secondary_plugins": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                
                "plugin_configurations": {
                    "type": "object",
                    "additionalProperties": {"type": "object"}
                }
            }
        }


# === Utility Functions ===

async def load_config_file(config_path: str) -> Dict[str, Any]:
    """
    Utility per caricare rapidamente un file di configurazione.
    
    Args:
        config_path: Percorso file configurazione
        
    Returns:
        Dict: Configurazione caricata
    """
    loader = ConfigLoader()
    return await loader.load_config(config_path)


def create_default_config_file(config_path: str) -> bool:
    """
    Crea un file di configurazione di default.
    
    Args:
        config_path: Percorso dove creare il file
        
    Returns:
        bool: True se creazione riuscita
    """
    try:
        loader = ConfigLoader()
        config = loader.create_default_config()
        
        import asyncio
        return asyncio.run(loader.save_config(config, config_path))
        
    except Exception:
        return False