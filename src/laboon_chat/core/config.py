"""
🌐 P2P Messaging Configuration Manager
=====================================

Gestione configurazione leggera e sicura per messaggistica P2P decentralizzata.
Supporta file JSON, variabili ambiente e valori di default.

🌊 "La configurazione è la bussola che guida ogni nodo" 🌐
"""

import json
import os
from typing import Any, Dict, Optional, Union
from pathlib import Path


class Config:
    """
    🌊 Gestore configurazione LaboonChat
    
    Carica configurazione da:
    1. File JSON specificato
    2. Variabili ambiente (LABOON_*)
    3. Valori di default
    """
    
    # Configurazione di default
    DEFAULT_CONFIG = {
        "network": {
            "dht_port": 6881,
            "max_peers": 50,
            "connection_timeout": 30
        },
        "plugins": {
            "directory": "plugins",
            "auto_load_essential": True,
            "security_level": "high"
        },
        "identity": {
            "directory": "identities",
            "auto_create": True
        },
        "logging": {
            "level": "INFO",
            "file": "laboon.log",
            "max_size_mb": 10,
            "backup_count": 3
        },
        "security": {
            "encryption_algorithm": "ChaCha20-Poly1305",
            "key_derivation_iterations": 100000,
            "secure_delete": True
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Inizializza configurazione
        
        Args:
            config_path: Percorso file configurazione JSON
        """
        self.config_path = config_path
        self.config_data = self.DEFAULT_CONFIG.copy()
        
        # Carica configurazione
        self._load_config()
        self._load_environment()
    
    def _load_config(self):
        """Carica configurazione da file JSON"""
        if not self.config_path:
            return
        
        config_file = Path(self.config_path)
        if not config_file.exists():
            return
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
            
            # Merge ricorsivo con default
            self._merge_config(self.config_data, file_config)
            
        except Exception as e:
            print(f"⚠️ Errore caricamento config {config_file}: {e}")
    
    def _load_environment(self):
        """Carica configurazione da variabili ambiente"""
        env_mappings = {
            'LABOON_DHT_PORT': ('network', 'dht_port'),
            'LABOON_PLUGINS_DIR': ('plugins', 'directory'),
            'LABOON_IDENTITY_DIR': ('identity', 'directory'),
            'LABOON_LOG_LEVEL': ('logging', 'level'),
            'LABOON_LOG_FILE': ('logging', 'file'),
            'LABOON_SECURITY_LEVEL': ('plugins', 'security_level')
        }
        
        for env_var, (section, key) in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                # Converti tipo se necessario
                if key.endswith('_port') or key.endswith('_count') or key.endswith('_mb'):
                    try:
                        value = int(value)
                    except ValueError:
                        continue
                elif key.endswith('_timeout'):
                    try:
                        value = float(value)
                    except ValueError:
                        continue
                elif value.lower() in ('true', 'false'):
                    value = value.lower() == 'true'
                
                self.config_data[section][key] = value
    
    def _merge_config(self, base: Dict, override: Dict):
        """Merge ricorsivo configurazioni"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Ottiene valore configurazione
        
        Args:
            key: Chiave configurazione (formato: "section.key")
            default: Valore di default se non trovato
            
        Returns:
            Any: Valore configurazione
        """
        try:
            keys = key.split('.')
            value = self.config_data
            
            for k in keys:
                value = value[k]
            
            return value
            
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """
        Imposta valore configurazione
        
        Args:
            key: Chiave configurazione (formato: "section.key")
            value: Valore da impostare
        """
        keys = key.split('.')
        config = self.config_data
        
        # Naviga fino al penultimo livello
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Imposta valore finale
        config[keys[-1]] = value
    
    def save(self, config_path: Optional[str] = None) -> bool:
        """
        Salva configurazione su file
        
        Args:
            config_path: Percorso file (usa self.config_path se None)
            
        Returns:
            bool: True se salvato con successo
        """
        save_path = config_path or self.config_path
        if not save_path:
            return False
        
        try:
            config_file = Path(save_path)
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"❌ Errore salvataggio config {save_path}: {e}")
            return False
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Ottiene intera sezione configurazione
        
        Args:
            section: Nome sezione
            
        Returns:
            Dict[str, Any]: Dati sezione
        """
        return self.config_data.get(section, {}).copy()
    
    def update_section(self, section: str, data: Dict[str, Any]):
        """
        Aggiorna intera sezione configurazione
        
        Args:
            section: Nome sezione
            data: Nuovi dati sezione
        """
        if section not in self.config_data:
            self.config_data[section] = {}
        
        self.config_data[section].update(data)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Ottiene configurazione completa come dizionario
        
        Returns:
            Dict[str, Any]: Configurazione completa
        """
        return self.config_data.copy()
    
    def __str__(self) -> str:
        """Rappresentazione stringa configurazione"""
        return f"LaboonConfig(path={self.config_path}, sections={list(self.config_data.keys())})"
    
    def __repr__(self) -> str:
        """Rappresentazione debug configurazione"""
        return self.__str__()


# Istanza globale configurazione (lazy loading)
_global_config: Optional[Config] = None


def get_config(config_path: Optional[str] = None) -> Config:
    """
    Ottiene istanza globale configurazione
    
    Args:
        config_path: Percorso configurazione (solo al primo accesso)
        
    Returns:
        Config: Istanza configurazione
    """
    global _global_config
    
    if _global_config is None:
        _global_config = Config(config_path)
    
    return _global_config


def reset_config():
    """Reset istanza globale configurazione (per test)"""
    global _global_config
    _global_config = None


# Export
__all__ = ['Config', 'get_config', 'reset_config']