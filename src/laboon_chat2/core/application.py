"""
LaboonChat v2.0 - Main Application

Orchestrates the modular plugin system with hot-swapping capabilities.
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from .plugin_manager import ModularPluginManager, PluginType, PluginStatus
from ..utils.config_loader import ConfigLoader
from ..utils.logger import setup_logger


@dataclass
class ApplicationState:
    """Stato dell'applicazione."""
    started: bool = False
    start_time: Optional[datetime] = None
    core_plugins_loaded: Dict[str, str] = None
    secondary_plugins_loaded: List[str] = None
    last_error: Optional[str] = None
    
    def __post_init__(self):
        if self.core_plugins_loaded is None:
            self.core_plugins_loaded = {}
        if self.secondary_plugins_loaded is None:
            self.secondary_plugins_loaded = []


class LaboonChat2Application:
    """
    Applicazione principale LaboonChat v2.0.
    
    Gestisce:
    - Inizializzazione sistema modulare
    - Caricamento plugin core e secondari
    - Lifecycle dell'applicazione
    - Gestione configurazioni
    - Monitoring e health checks
    """
    
    def __init__(self, config_path: str = "config/app_config.json"):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.logger: Optional[logging.Logger] = None
        self.plugin_manager: Optional[ModularPluginManager] = None
        self.state = ApplicationState()
        
        # Gestione shutdown graceful
        self._shutdown_event = asyncio.Event()
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """Configura gestori per shutdown graceful."""
        def signal_handler(signum, frame):
            self.logger.info(f"Ricevuto segnale {signum}, avvio shutdown...")
            asyncio.create_task(self.shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def initialize(self) -> bool:
        """
        Inizializza l'applicazione.
        
        Returns:
            bool: True se inizializzazione riuscita
        """
        try:
            # Carica configurazione
            success = await self._load_configuration()
            if not success:
                return False
            
            # Setup logging
            self._setup_logging()
            self.logger.info("=== LaboonChat v2.0 - Inizializzazione ===")
            
            # Inizializza plugin manager
            success = await self._initialize_plugin_manager()
            if not success:
                return False
            
            # Carica plugin core di default
            success = await self._load_default_core_plugins()
            if not success:
                return False
            
            # Carica plugin secondari configurati
            success = await self._load_configured_secondary_plugins()
            if not success:
                self.logger.warning("Alcuni plugin secondari non sono stati caricati")
            
            self.state.started = True
            self.state.start_time = datetime.now()
            
            self.logger.info("LaboonChat v2.0 inizializzato con successo")
            return True
            
        except Exception as e:
            error_msg = f"Errore inizializzazione applicazione: {e}"
            if self.logger:
                self.logger.error(error_msg)
            else:
                print(error_msg)
            self.state.last_error = str(e)
            return False
    
    async def run(self) -> None:
        """
        Avvia l'applicazione e mantiene il loop principale.
        """
        if not self.state.started:
            success = await self.initialize()
            if not success:
                self.logger.error("Impossibile avviare l'applicazione")
                return
        
        self.logger.info("LaboonChat v2.0 in esecuzione...")
        
        try:
            # Avvia servizi core
            await self._start_core_services()
            
            # Loop principale
            await self._main_loop()
            
        except Exception as e:
            self.logger.error(f"Errore nel loop principale: {e}")
            self.state.last_error = str(e)
        finally:
            await self.shutdown()
    
    async def shutdown(self) -> None:
        """
        Shutdown graceful dell'applicazione.
        """
        if not self.state.started:
            return
        
        self.logger.info("=== LaboonChat v2.0 - Shutdown ===")
        
        try:
            # Ferma servizi core
            await self._stop_core_services()
            
            # Cleanup plugin manager
            if self.plugin_manager:
                await self.plugin_manager.cleanup()
            
            self.state.started = False
            self.logger.info("Shutdown completato")
            
        except Exception as e:
            self.logger.error(f"Errore durante shutdown: {e}")
        
        # Segnala shutdown completato
        self._shutdown_event.set()
    
    # === Core Plugin Management ===
    
    async def load_core_plugin(
        self, 
        plugin_type: PluginType, 
        plugin_name: str,
        config: Dict[str, Any] = None
    ) -> bool:
        """
        Carica un plugin core con hot-swapping.
        
        Args:
            plugin_type: Tipo di plugin core
            plugin_name: Nome del plugin
            config: Configurazione specifica
            
        Returns:
            bool: True se caricamento riuscito
        """
        if not self.plugin_manager:
            self.logger.error("Plugin manager non inizializzato")
            return False
        
        self.logger.info(f"Caricamento plugin core {plugin_type.value}: {plugin_name}")
        
        success = await self.plugin_manager.load_core_plugin(plugin_type, plugin_name, config)
        
        if success:
            self.state.core_plugins_loaded[plugin_type.value] = plugin_name
            self.logger.info(f"Plugin core {plugin_name} caricato con successo")
        else:
            self.logger.error(f"Errore caricamento plugin core {plugin_name}")
        
        return success
    
    async def unload_core_plugin(self, plugin_type: PluginType) -> bool:
        """
        Scarica un plugin core.
        
        Args:
            plugin_type: Tipo di plugin da scaricare
            
        Returns:
            bool: True se scaricamento riuscito
        """
        if not self.plugin_manager:
            return False
        
        success = await self.plugin_manager.unload_core_plugin(plugin_type)
        
        if success and plugin_type.value in self.state.core_plugins_loaded:
            del self.state.core_plugins_loaded[plugin_type.value]
        
        return success
    
    async def get_core_plugin(self, plugin_type: PluginType) -> Optional[Any]:
        """
        Ottiene l'istanza di un plugin core attivo.
        
        Args:
            plugin_type: Tipo di plugin
            
        Returns:
            Optional[Any]: Istanza del plugin se attivo
        """
        if not self.plugin_manager:
            return None
        
        return await self.plugin_manager.get_active_core_plugin(plugin_type)
    
    # === Secondary Plugin Management ===
    
    async def load_secondary_plugin(
        self, 
        plugin_name: str,
        config: Dict[str, Any] = None
    ) -> bool:
        """
        Carica un plugin secondario.
        
        Args:
            plugin_name: Nome del plugin
            config: Configurazione specifica
            
        Returns:
            bool: True se caricamento riuscito
        """
        if not self.plugin_manager:
            return False
        
        success = await self.plugin_manager.load_secondary_plugin(plugin_name, config)
        
        if success and plugin_name not in self.state.secondary_plugins_loaded:
            self.state.secondary_plugins_loaded.append(plugin_name)
        
        return success
    
    async def unload_secondary_plugin(self, plugin_name: str) -> bool:
        """
        Scarica un plugin secondario.
        
        Args:
            plugin_name: Nome del plugin
            
        Returns:
            bool: True se scaricamento riuscito
        """
        if not self.plugin_manager:
            return False
        
        success = await self.plugin_manager.unload_secondary_plugin(plugin_name)
        
        if success and plugin_name in self.state.secondary_plugins_loaded:
            self.state.secondary_plugins_loaded.remove(plugin_name)
        
        return success
    
    # === Application Status and Information ===
    
    def get_application_status(self) -> Dict[str, Any]:
        """
        Ottiene lo stato dell'applicazione.
        
        Returns:
            Dict: Stato completo dell'applicazione
        """
        status = {
            "started": self.state.started,
            "start_time": self.state.start_time.isoformat() if self.state.start_time else None,
            "uptime_seconds": (
                (datetime.now() - self.state.start_time).total_seconds() 
                if self.state.start_time else 0
            ),
            "core_plugins": self.state.core_plugins_loaded.copy(),
            "secondary_plugins": self.state.secondary_plugins_loaded.copy(),
            "last_error": self.state.last_error
        }
        
        # Aggiungi informazioni plugin manager
        if self.plugin_manager:
            status["plugin_manager"] = {
                "registered_plugins": len(self.plugin_manager._registered_plugins),
                "active_core_plugins": len(self.plugin_manager._active_core_plugins),
                "active_secondary_plugins": len(self.plugin_manager._active_secondary_plugins)
            }
        
        return status
    
    async def get_detailed_status(self) -> Dict[str, Any]:
        """
        Ottiene stato dettagliato con health checks.
        
        Returns:
            Dict: Stato dettagliato dell'applicazione
        """
        status = self.get_application_status()
        
        if self.plugin_manager:
            # Aggiungi dettagli plugin
            status["plugins"] = {
                "registered": self.plugin_manager.get_registered_plugins(),
                "active": self.plugin_manager.get_active_plugins()
            }
            
            # Health check plugin attivi
            health_checks = {}
            for plugin_type, plugin_info in self.plugin_manager._active_core_plugins.items():
                plugin_status = await self.plugin_manager.get_plugin_status(plugin_info.name)
                if plugin_status:
                    health_checks[f"core_{plugin_type.value}"] = plugin_status
            
            for plugin_name in self.plugin_manager._active_secondary_plugins:
                plugin_status = await self.plugin_manager.get_plugin_status(plugin_name)
                if plugin_status:
                    health_checks[f"secondary_{plugin_name}"] = plugin_status
            
            status["health_checks"] = health_checks
        
        return status
    
    # === Configuration Management ===
    
    async def reload_configuration(self) -> bool:
        """
        Ricarica la configurazione dell'applicazione.
        
        Returns:
            bool: True se ricaricamento riuscito
        """
        try:
            success = await self._load_configuration()
            if success:
                self.logger.info("Configurazione ricaricata con successo")
                
                # Aggiorna configurazioni plugin se necessario
                await self._update_plugin_configurations()
            
            return success
            
        except Exception as e:
            self.logger.error(f"Errore ricaricamento configurazione: {e}")
            return False
    
    async def update_plugin_configuration(
        self, 
        plugin_name: str, 
        config: Dict[str, Any]
    ) -> bool:
        """
        Aggiorna la configurazione di un plugin specifico.
        
        Args:
            plugin_name: Nome del plugin
            config: Nuova configurazione
            
        Returns:
            bool: True se aggiornamento riuscito
        """
        if not self.plugin_manager:
            return False
        
        try:
            # Trova il plugin
            if plugin_name not in self.plugin_manager._registered_plugins:
                self.logger.error(f"Plugin {plugin_name} non trovato")
                return False
            
            plugin_info = self.plugin_manager._registered_plugins[plugin_name]
            
            # Aggiorna configurazione se plugin attivo
            if plugin_info.instance and hasattr(plugin_info.instance, 'update_config'):
                success = await plugin_info.instance.update_config(config)
                if success:
                    plugin_info.config = config
                    self.logger.info(f"Configurazione plugin {plugin_name} aggiornata")
                return success
            
            # Altrimenti aggiorna solo la configurazione memorizzata
            plugin_info.config = config
            return True
            
        except Exception as e:
            self.logger.error(f"Errore aggiornamento configurazione plugin {plugin_name}: {e}")
            return False
    
    # === Private Methods ===
    
    async def _load_configuration(self) -> bool:
        """Carica la configurazione dell'applicazione."""
        try:
            config_loader = ConfigLoader()
            self.config = await config_loader.load_config(self.config_path)
            return True
            
        except Exception as e:
            error_msg = f"Errore caricamento configurazione: {e}"
            if self.logger:
                self.logger.error(error_msg)
            else:
                print(error_msg)
            return False
    
    def _setup_logging(self) -> None:
        """Configura il sistema di logging."""
        log_config = self.config.get("logging", {})
        self.logger = setup_logger(
            name="laboon_chat2",
            level=log_config.get("level", "INFO"),
            log_file=log_config.get("file", "logs/laboon_chat2.log")
        )
    
    async def _initialize_plugin_manager(self) -> bool:
        """Inizializza il plugin manager."""
        try:
            plugin_config = self.config.get("plugins", {})
            self.plugin_manager = ModularPluginManager(plugin_config)
            return await self.plugin_manager.initialize()
            
        except Exception as e:
            self.logger.error(f"Errore inizializzazione plugin manager: {e}")
            return False
    
    async def _load_default_core_plugins(self) -> bool:
        """Carica i plugin core di default."""
        try:
            default_plugins = self.config.get("default_core_plugins", {})
            
            for plugin_type_str, plugin_name in default_plugins.items():
                try:
                    plugin_type = PluginType(plugin_type_str)
                    success = await self.load_core_plugin(plugin_type, plugin_name)
                    if not success:
                        self.logger.error(f"Errore caricamento plugin core default {plugin_name}")
                        return False
                except ValueError:
                    self.logger.error(f"Tipo plugin non valido: {plugin_type_str}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Errore caricamento plugin core default: {e}")
            return False
    
    async def _load_configured_secondary_plugins(self) -> bool:
        """Carica i plugin secondari configurati."""
        try:
            secondary_plugins = self.config.get("default_secondary_plugins", [])
            
            success_count = 0
            for plugin_name in secondary_plugins:
                success = await self.load_secondary_plugin(plugin_name)
                if success:
                    success_count += 1
                else:
                    self.logger.warning(f"Errore caricamento plugin secondario {plugin_name}")
            
            self.logger.info(f"Caricati {success_count}/{len(secondary_plugins)} plugin secondari")
            return success_count > 0 or len(secondary_plugins) == 0
            
        except Exception as e:
            self.logger.error(f"Errore caricamento plugin secondari: {e}")
            return False
    
    async def _start_core_services(self) -> None:
        """Avvia i servizi core."""
        # Avvia servizi dei plugin core attivi
        if self.plugin_manager:
            for plugin_type, plugin_info in self.plugin_manager._active_core_plugins.items():
                if plugin_info.instance and hasattr(plugin_info.instance, 'start'):
                    try:
                        await plugin_info.instance.start()
                        self.logger.info(f"Servizio {plugin_type.value} avviato")
                    except Exception as e:
                        self.logger.error(f"Errore avvio servizio {plugin_type.value}: {e}")
    
    async def _stop_core_services(self) -> None:
        """Ferma i servizi core."""
        if self.plugin_manager:
            for plugin_type, plugin_info in self.plugin_manager._active_core_plugins.items():
                if plugin_info.instance and hasattr(plugin_info.instance, 'stop'):
                    try:
                        await plugin_info.instance.stop()
                        self.logger.info(f"Servizio {plugin_type.value} fermato")
                    except Exception as e:
                        self.logger.error(f"Errore stop servizio {plugin_type.value}: {e}")
    
    async def _main_loop(self) -> None:
        """Loop principale dell'applicazione."""
        try:
            # Attendi segnale di shutdown
            await self._shutdown_event.wait()
            
        except asyncio.CancelledError:
            self.logger.info("Loop principale cancellato")
        except Exception as e:
            self.logger.error(f"Errore nel loop principale: {e}")
            raise
    
    async def _update_plugin_configurations(self) -> None:
        """Aggiorna configurazioni plugin dopo reload."""
        if not self.plugin_manager:
            return
        
        plugin_configs = self.config.get("plugin_configurations", {})
        
        for plugin_name, config in plugin_configs.items():
            await self.update_plugin_configuration(plugin_name, config)


# === Utility Functions ===

async def create_application(config_path: str = "config/app_config.json") -> LaboonChat2Application:
    """
    Factory function per creare l'applicazione.
    
    Args:
        config_path: Percorso file configurazione
        
    Returns:
        LaboonChat2Application: Istanza dell'applicazione
    """
    app = LaboonChat2Application(config_path)
    return app


async def run_application(config_path: str = "config/app_config.json") -> None:
    """
    Utility per avviare l'applicazione.
    
    Args:
        config_path: Percorso file configurazione
    """
    app = await create_application(config_path)
    await app.run()


if __name__ == "__main__":
    # Avvio diretto dell'applicazione
    asyncio.run(run_application())