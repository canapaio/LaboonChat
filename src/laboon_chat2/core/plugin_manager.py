"""
Modular Plugin Manager for LaboonChat v2.0

Manages exclusive core plugins and cumulative secondary plugins with hot-swapping capabilities.
"""

import asyncio
import importlib
import importlib.util
import inspect
import json
import logging
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Type, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum

from ..interfaces.security_interface import ISecurityModule
from ..interfaces.messaging_interface import IMessagingModule
from ..interfaces.interface_interface import IInterfaceModule
from ..interfaces.network_interface import INetworkModule
from ..interfaces.secondary_plugin_interface import (
    ISecondaryPlugin, 
    PluginCategory, 
    PluginPriority,
    PluginEvent
)


class PluginType(Enum):
    """Tipi di plugin supportati."""
    SECURITY = "security"
    MESSAGING = "messaging"
    INTERFACE = "interface"
    NETWORK = "network"
    SECONDARY = "secondary"


class PluginStatus(Enum):
    """Stati dei plugin."""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    ACTIVE = "active"
    ERROR = "error"
    UNLOADING = "unloading"


@dataclass
class PluginInfo:
    """Informazioni su un plugin."""
    name: str
    plugin_type: PluginType
    version: str
    description: str
    author: str
    file_path: str
    class_name: str
    status: PluginStatus = PluginStatus.UNLOADED
    instance: Optional[Any] = None
    config: Dict[str, Any] = None
    load_time: Optional[datetime] = None
    error_message: Optional[str] = None
    dependencies: List[str] = None
    conflicts: List[str] = None
    
    def __post_init__(self):
        if self.config is None:
            self.config = {}
        if self.dependencies is None:
            self.dependencies = []
        if self.conflicts is None:
            self.conflicts = []


class ModularPluginManager:
    """
    Gestore modulare dei plugin per LaboonChat v2.0.
    
    Caratteristiche:
    - Plugin core esclusivi (solo uno per tipo attivo)
    - Plugin secondari cumulativi (multipli simultanei)
    - Hot-swapping senza interruzioni
    - Gestione dipendenze e conflitti
    - Monitoraggio performance e salute
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Plugin registrati e attivi
        self._registered_plugins: Dict[str, PluginInfo] = {}
        self._active_core_plugins: Dict[PluginType, PluginInfo] = {}
        self._active_secondary_plugins: Dict[str, PluginInfo] = {}
        
        # Event system
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._plugin_apis: Dict[str, Dict[str, Any]] = {}
        self._shared_data: Dict[str, Any] = {}
        
        # Paths
        self.core_plugins_path = Path(self.config.get("core_plugins_path", "plugins/core"))
        self.secondary_plugins_path = Path(self.config.get("secondary_plugins_path", "plugins/secondary"))
        
        # Performance tracking
        self._performance_metrics: Dict[str, Dict[str, Any]] = {}
        
        # Lock per operazioni thread-safe
        self._lock = asyncio.Lock()
        
    async def initialize(self) -> bool:
        """
        Inizializza il plugin manager.
        
        Returns:
            bool: True se inizializzazione riuscita
        """
        try:
            self.logger.info("Inizializzazione ModularPluginManager...")
            
            # Crea directory se non esistono
            self.core_plugins_path.mkdir(parents=True, exist_ok=True)
            self.secondary_plugins_path.mkdir(parents=True, exist_ok=True)
            
            # Scansiona plugin disponibili
            await self._scan_plugins()
            
            # Carica configurazioni plugin
            await self._load_plugin_configs()
            
            self.logger.info("ModularPluginManager inizializzato con successo")
            return True
            
        except Exception as e:
            self.logger.error(f"Errore inizializzazione plugin manager: {e}")
            return False
    
    async def cleanup(self) -> bool:
        """
        Cleanup graceful del plugin manager.
        
        Returns:
            bool: True se cleanup riuscito
        """
        try:
            self.logger.info("Cleanup ModularPluginManager...")
            
            # Disattiva tutti i plugin secondari
            for plugin_name in list(self._active_secondary_plugins.keys()):
                await self.deactivate_secondary_plugin(plugin_name)
            
            # Disattiva tutti i plugin core
            for plugin_type in list(self._active_core_plugins.keys()):
                await self.unload_core_plugin(plugin_type)
            
            # Pulisci dati condivisi
            self._shared_data.clear()
            self._plugin_apis.clear()
            self._event_handlers.clear()
            
            self.logger.info("Cleanup completato")
            return True
            
        except Exception as e:
            self.logger.error(f"Errore durante cleanup: {e}")
            return False
    
    # === Core Plugin Management (Exclusive) ===
    
    async def load_core_plugin(
        self, 
        plugin_type: PluginType, 
        plugin_name: str,
        config: Dict[str, Any] = None
    ) -> bool:
        """
        Carica un plugin core esclusivo.
        
        Args:
            plugin_type: Tipo di plugin core
            plugin_name: Nome del plugin da caricare
            config: Configurazione specifica del plugin
            
        Returns:
            bool: True se caricamento riuscito
        """
        async with self._lock:
            try:
                # Verifica se esiste un plugin attivo dello stesso tipo
                if plugin_type in self._active_core_plugins:
                    current_plugin = self._active_core_plugins[plugin_type]
                    self.logger.info(f"Sostituendo plugin {plugin_type.value}: {current_plugin.name} -> {plugin_name}")
                    await self._unload_core_plugin_internal(plugin_type)
                
                # Trova il plugin richiesto
                if plugin_name not in self._registered_plugins:
                    self.logger.error(f"Plugin {plugin_name} non trovato")
                    return False
                
                plugin_info = self._registered_plugins[plugin_name]
                
                # Verifica che sia del tipo corretto
                if plugin_info.plugin_type != plugin_type:
                    self.logger.error(f"Plugin {plugin_name} non è di tipo {plugin_type.value}")
                    return False
                
                # Carica il plugin
                success = await self._load_plugin_instance(plugin_info, config)
                if success:
                    self._active_core_plugins[plugin_type] = plugin_info
                    await self._emit_event("core_plugin_loaded", {
                        "plugin_type": plugin_type.value,
                        "plugin_name": plugin_name
                    })
                    self.logger.info(f"Plugin core {plugin_name} caricato con successo")
                
                return success
                
            except Exception as e:
                self.logger.error(f"Errore caricamento plugin core {plugin_name}: {e}")
                return False
    
    async def unload_core_plugin(self, plugin_type: PluginType) -> bool:
        """
        Scarica un plugin core.
        
        Args:
            plugin_type: Tipo di plugin da scaricare
            
        Returns:
            bool: True se scaricamento riuscito
        """
        async with self._lock:
            return await self._unload_core_plugin_internal(plugin_type)
    
    async def _unload_core_plugin_internal(self, plugin_type: PluginType) -> bool:
        """Implementazione interna per scaricare plugin core."""
        try:
            if plugin_type not in self._active_core_plugins:
                return True
            
            plugin_info = self._active_core_plugins[plugin_type]
            
            # Cleanup del plugin
            if plugin_info.instance and hasattr(plugin_info.instance, 'cleanup'):
                await plugin_info.instance.cleanup()
            
            # Rimuovi dalle strutture attive
            del self._active_core_plugins[plugin_type]
            plugin_info.status = PluginStatus.UNLOADED
            plugin_info.instance = None
            
            await self._emit_event("core_plugin_unloaded", {
                "plugin_type": plugin_type.value,
                "plugin_name": plugin_info.name
            })
            
            self.logger.info(f"Plugin core {plugin_info.name} scaricato")
            return True
            
        except Exception as e:
            self.logger.error(f"Errore scaricamento plugin core {plugin_type.value}: {e}")
            return False
    
    async def get_active_core_plugin(self, plugin_type: PluginType) -> Optional[Any]:
        """
        Ottiene l'istanza del plugin core attivo.
        
        Args:
            plugin_type: Tipo di plugin
            
        Returns:
            Optional[Any]: Istanza del plugin se attivo
        """
        if plugin_type in self._active_core_plugins:
            return self._active_core_plugins[plugin_type].instance
        return None
    
    # === Secondary Plugin Management (Cumulative) ===
    
    async def load_secondary_plugin(
        self, 
        plugin_name: str,
        config: Dict[str, Any] = None
    ) -> bool:
        """
        Carica un plugin secondario cumulativo.
        
        Args:
            plugin_name: Nome del plugin da caricare
            config: Configurazione specifica del plugin
            
        Returns:
            bool: True se caricamento riuscito
        """
        async with self._lock:
            try:
                # Verifica se già attivo
                if plugin_name in self._active_secondary_plugins:
                    self.logger.warning(f"Plugin secondario {plugin_name} già attivo")
                    return True
                
                # Trova il plugin richiesto
                if plugin_name not in self._registered_plugins:
                    self.logger.error(f"Plugin {plugin_name} non trovato")
                    return False
                
                plugin_info = self._registered_plugins[plugin_name]
                
                # Verifica che sia un plugin secondario
                if plugin_info.plugin_type != PluginType.SECONDARY:
                    self.logger.error(f"Plugin {plugin_name} non è un plugin secondario")
                    return False
                
                # Verifica dipendenze e conflitti
                if not await self._check_plugin_compatibility(plugin_info):
                    return False
                
                # Carica il plugin
                success = await self._load_plugin_instance(plugin_info, config)
                if success:
                    self._active_secondary_plugins[plugin_name] = plugin_info
                    await self._emit_event("secondary_plugin_loaded", {
                        "plugin_name": plugin_name
                    })
                    self.logger.info(f"Plugin secondario {plugin_name} caricato con successo")
                
                return success
                
            except Exception as e:
                self.logger.error(f"Errore caricamento plugin secondario {plugin_name}: {e}")
                return False
    
    async def unload_secondary_plugin(self, plugin_name: str) -> bool:
        """
        Scarica un plugin secondario.
        
        Args:
            plugin_name: Nome del plugin da scaricare
            
        Returns:
            bool: True se scaricamento riuscito
        """
        async with self._lock:
            try:
                if plugin_name not in self._active_secondary_plugins:
                    return True
                
                plugin_info = self._active_secondary_plugins[plugin_name]
                
                # Cleanup del plugin
                if plugin_info.instance and hasattr(plugin_info.instance, 'cleanup'):
                    await plugin_info.instance.cleanup()
                
                # Rimuovi dalle strutture attive
                del self._active_secondary_plugins[plugin_name]
                plugin_info.status = PluginStatus.UNLOADED
                plugin_info.instance = None
                
                await self._emit_event("secondary_plugin_unloaded", {
                    "plugin_name": plugin_name
                })
                
                self.logger.info(f"Plugin secondario {plugin_name} scaricato")
                return True
                
            except Exception as e:
                self.logger.error(f"Errore scaricamento plugin secondario {plugin_name}: {e}")
                return False
    
    async def activate_secondary_plugin(self, plugin_name: str) -> bool:
        """
        Attiva un plugin secondario già caricato.
        
        Args:
            plugin_name: Nome del plugin da attivare
            
        Returns:
            bool: True se attivazione riuscita
        """
        try:
            if plugin_name not in self._active_secondary_plugins:
                self.logger.error(f"Plugin {plugin_name} non caricato")
                return False
            
            plugin_info = self._active_secondary_plugins[plugin_name]
            
            if plugin_info.instance and hasattr(plugin_info.instance, 'activate'):
                success = await plugin_info.instance.activate()
                if success:
                    plugin_info.status = PluginStatus.ACTIVE
                    await self._emit_event("secondary_plugin_activated", {
                        "plugin_name": plugin_name
                    })
                return success
            
            return True
            
        except Exception as e:
            self.logger.error(f"Errore attivazione plugin {plugin_name}: {e}")
            return False
    
    async def deactivate_secondary_plugin(self, plugin_name: str) -> bool:
        """
        Disattiva un plugin secondario.
        
        Args:
            plugin_name: Nome del plugin da disattivare
            
        Returns:
            bool: True se disattivazione riuscita
        """
        try:
            if plugin_name not in self._active_secondary_plugins:
                return True
            
            plugin_info = self._active_secondary_plugins[plugin_name]
            
            if plugin_info.instance and hasattr(plugin_info.instance, 'deactivate'):
                success = await plugin_info.instance.deactivate()
                if success:
                    plugin_info.status = PluginStatus.LOADED
                    await self._emit_event("secondary_plugin_deactivated", {
                        "plugin_name": plugin_name
                    })
                return success
            
            return True
            
        except Exception as e:
            self.logger.error(f"Errore disattivazione plugin {plugin_name}: {e}")
            return False
    
    # === Plugin Discovery and Loading ===
    
    async def _scan_plugins(self) -> None:
        """Scansiona le directory per trovare plugin disponibili."""
        try:
            # Scansiona plugin core
            await self._scan_core_plugins()
            
            # Scansiona plugin secondari
            await self._scan_secondary_plugins()
            
            self.logger.info(f"Trovati {len(self._registered_plugins)} plugin totali")
            
        except Exception as e:
            self.logger.error(f"Errore scansione plugin: {e}")
    
    async def _scan_core_plugins(self) -> None:
        """Scansiona plugin core."""
        for plugin_type_dir in self.core_plugins_path.iterdir():
            if plugin_type_dir.is_dir():
                plugin_type_name = plugin_type_dir.name
                try:
                    plugin_type = PluginType(plugin_type_name)
                except ValueError:
                    continue
                
                for plugin_file in plugin_type_dir.glob("*.py"):
                    if plugin_file.name.startswith("__"):
                        continue
                    
                    await self._register_plugin_from_file(plugin_file, plugin_type)
    
    async def _scan_secondary_plugins(self) -> None:
        """Scansiona plugin secondari."""
        for category_dir in self.secondary_plugins_path.iterdir():
            if category_dir.is_dir():
                for plugin_file in category_dir.glob("*.py"):
                    if plugin_file.name.startswith("__"):
                        continue
                    
                    await self._register_plugin_from_file(plugin_file, PluginType.SECONDARY)
    
    async def _register_plugin_from_file(self, plugin_file: Path, plugin_type: PluginType) -> None:
        """Registra un plugin da file."""
        try:
            # Carica il modulo
            spec = importlib.util.spec_from_file_location(plugin_file.stem, plugin_file)
            if not spec or not spec.loader:
                return
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Trova la classe del plugin
            plugin_class = None
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if self._is_valid_plugin_class(obj, plugin_type):
                    plugin_class = obj
                    break
            
            if not plugin_class:
                self.logger.warning(f"Nessuna classe plugin valida trovata in {plugin_file}")
                return
            
            # Crea info plugin
            plugin_info = PluginInfo(
                name=plugin_file.stem,
                plugin_type=plugin_type,
                version=getattr(plugin_class, '__version__', '1.0.0'),
                description=getattr(plugin_class, '__description__', ''),
                author=getattr(plugin_class, '__author__', 'Unknown'),
                file_path=str(plugin_file),
                class_name=plugin_class.__name__
            )
            
            self._registered_plugins[plugin_info.name] = plugin_info
            self.logger.debug(f"Plugin registrato: {plugin_info.name}")
            
        except Exception as e:
            self.logger.error(f"Errore registrazione plugin {plugin_file}: {e}")
    
    def _is_valid_plugin_class(self, cls: Type, plugin_type: PluginType) -> bool:
        """Verifica se una classe è un plugin valido."""
        if plugin_type == PluginType.SECURITY:
            return issubclass(cls, ISecurityModule) and cls != ISecurityModule
        elif plugin_type == PluginType.MESSAGING:
            return issubclass(cls, IMessagingModule) and cls != IMessagingModule
        elif plugin_type == PluginType.INTERFACE:
            return issubclass(cls, IInterfaceModule) and cls != IInterfaceModule
        elif plugin_type == PluginType.NETWORK:
            return issubclass(cls, INetworkModule) and cls != INetworkModule
        elif plugin_type == PluginType.SECONDARY:
            return issubclass(cls, ISecondaryPlugin) and cls != ISecondaryPlugin
        
        return False
    
    async def _load_plugin_instance(
        self, 
        plugin_info: PluginInfo, 
        config: Dict[str, Any] = None
    ) -> bool:
        """Carica un'istanza del plugin."""
        try:
            plugin_info.status = PluginStatus.LOADING
            
            # Carica il modulo
            spec = importlib.util.spec_from_file_location(
                plugin_info.name, 
                plugin_info.file_path
            )
            if not spec or not spec.loader:
                raise Exception("Impossibile caricare il modulo")
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Ottieni la classe
            plugin_class = getattr(module, plugin_info.class_name)
            
            # Crea istanza
            plugin_info.instance = plugin_class()
            
            # Inizializza con configurazione
            plugin_config = config or plugin_info.config
            success = await plugin_info.instance.initialize(plugin_config)
            
            if success:
                plugin_info.status = PluginStatus.LOADED
                plugin_info.load_time = datetime.now()
                plugin_info.config = plugin_config
                plugin_info.error_message = None
                
                # Registra API se disponibile
                if hasattr(plugin_info.instance, 'get_api'):
                    self._plugin_apis[plugin_info.name] = plugin_info.instance.get_api()
                
                return True
            else:
                plugin_info.status = PluginStatus.ERROR
                plugin_info.error_message = "Inizializzazione fallita"
                return False
                
        except Exception as e:
            plugin_info.status = PluginStatus.ERROR
            plugin_info.error_message = str(e)
            self.logger.error(f"Errore caricamento istanza plugin {plugin_info.name}: {e}")
            return False
    
    # === Plugin Information and Status ===
    
    def get_registered_plugins(self) -> Dict[str, Dict[str, Any]]:
        """
        Ottiene tutti i plugin registrati.
        
        Returns:
            Dict: Informazioni sui plugin registrati
        """
        return {
            name: {
                "name": info.name,
                "type": info.plugin_type.value,
                "version": info.version,
                "description": info.description,
                "author": info.author,
                "status": info.status.value,
                "load_time": info.load_time.isoformat() if info.load_time else None,
                "error_message": info.error_message
            }
            for name, info in self._registered_plugins.items()
        }
    
    def get_active_plugins(self) -> Dict[str, Any]:
        """
        Ottiene i plugin attualmente attivi.
        
        Returns:
            Dict: Plugin attivi divisi per tipo
        """
        return {
            "core": {
                plugin_type.value: info.name 
                for plugin_type, info in self._active_core_plugins.items()
            },
            "secondary": list(self._active_secondary_plugins.keys())
        }
    
    async def get_plugin_status(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """
        Ottiene lo stato dettagliato di un plugin.
        
        Args:
            plugin_name: Nome del plugin
            
        Returns:
            Optional[Dict]: Stato del plugin se trovato
        """
        if plugin_name not in self._registered_plugins:
            return None
        
        info = self._registered_plugins[plugin_name]
        status = {
            "name": info.name,
            "type": info.plugin_type.value,
            "status": info.status.value,
            "version": info.version,
            "load_time": info.load_time.isoformat() if info.load_time else None,
            "error_message": info.error_message
        }
        
        # Aggiungi health check se plugin attivo
        if info.instance and hasattr(info.instance, 'health_check'):
            try:
                health = await info.instance.health_check()
                status["health"] = health
            except Exception as e:
                status["health"] = {"status": "error", "details": str(e)}
        
        return status
    
    # === Event System ===
    
    async def _emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Emette un evento verso i plugin."""
        event = PluginEvent(
            event_type=event_type,
            source_plugin="plugin_manager",
            data=data,
            timestamp=datetime.now().timestamp()
        )
        
        # Invia a handler registrati
        if event_type in self._event_handlers:
            for handler in self._event_handlers[event_type]:
                try:
                    await handler(event)
                except Exception as e:
                    self.logger.error(f"Errore handler evento {event_type}: {e}")
        
        # Invia a plugin secondari attivi
        for plugin_info in self._active_secondary_plugins.values():
            if plugin_info.instance and hasattr(plugin_info.instance, 'handle_event'):
                try:
                    await plugin_info.instance.handle_event(event)
                except Exception as e:
                    self.logger.error(f"Errore gestione evento in {plugin_info.name}: {e}")
    
    # === Utility Methods ===
    
    async def _check_plugin_compatibility(self, plugin_info: PluginInfo) -> bool:
        """Verifica compatibilità dipendenze e conflitti."""
        # Verifica dipendenze
        for dependency in plugin_info.dependencies:
            if dependency not in self._active_secondary_plugins:
                self.logger.error(f"Dipendenza {dependency} non soddisfatta per {plugin_info.name}")
                return False
        
        # Verifica conflitti
        for conflict in plugin_info.conflicts:
            if conflict in self._active_secondary_plugins:
                self.logger.error(f"Conflitto con {conflict} per {plugin_info.name}")
                return False
        
        return True
    
    async def _load_plugin_configs(self) -> None:
        """Carica configurazioni dei plugin."""
        config_file = Path("config/plugin_configs.json")
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    configs = json.load(f)
                
                for plugin_name, config in configs.items():
                    if plugin_name in self._registered_plugins:
                        self._registered_plugins[plugin_name].config = config
                        
            except Exception as e:
                self.logger.error(f"Errore caricamento configurazioni plugin: {e}")