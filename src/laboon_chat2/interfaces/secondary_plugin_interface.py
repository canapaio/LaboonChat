"""
Abstract interface for Secondary Plugins in LaboonChat v2.0

Defines the contract that all secondary (cumulative) plugins must implement.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Callable, Union
from dataclasses import dataclass
from enum import Enum
import asyncio


class PluginCategory(Enum):
    """Categorie dei plugin secondari."""
    UI_ENHANCEMENT = "ui_enhancement"
    PROTECTION = "protection"
    FILE_MANAGEMENT = "file_management"
    ADVANCED_FEATURES = "advanced_features"
    CUSTOM = "custom"


class PluginPriority(Enum):
    """Priorità di esecuzione dei plugin."""
    CRITICAL = 100
    HIGH = 75
    NORMAL = 50
    LOW = 25
    BACKGROUND = 10


@dataclass
class PluginCapability:
    """Capacità fornita da un plugin."""
    name: str
    description: str
    version: str
    dependencies: List[str] = None
    conflicts: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.conflicts is None:
            self.conflicts = []


@dataclass
class PluginEvent:
    """Evento del plugin."""
    event_type: str
    source_plugin: str
    data: Dict[str, Any]
    timestamp: float
    priority: PluginPriority = PluginPriority.NORMAL


class ISecondaryPlugin(ABC):
    """
    Interfaccia astratta per plugin secondari cumulativi.
    
    I plugin secondari possono essere caricati simultaneamente e forniscono:
    - Funzionalità aggiuntive non essenziali
    - Miglioramenti dell'interfaccia utente
    - Protezioni e sicurezza avanzata
    - Gestione file e media
    - Funzionalità avanzate personalizzate
    """
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Inizializza il plugin secondario.
        
        Args:
            config: Configurazione specifica del plugin
            
        Returns:
            bool: True se inizializzazione riuscita
        """
        pass
    
    @abstractmethod
    async def cleanup(self) -> bool:
        """
        Cleanup graceful del plugin prima dello scaricamento.
        
        Returns:
            bool: True se cleanup riuscito
        """
        pass
    
    # === Plugin Metadata ===
    
    @abstractmethod
    def get_plugin_info(self) -> Dict[str, Any]:
        """
        Ottiene informazioni sul plugin.
        
        Returns:
            Dict: {
                "name": str,
                "version": str,
                "description": str,
                "author": str,
                "category": PluginCategory,
                "priority": PluginPriority,
                "capabilities": List[PluginCapability],
                "dependencies": List[str],
                "conflicts": List[str]
            }
        """
        pass
    
    @abstractmethod
    def get_plugin_category(self) -> PluginCategory:
        """
        Ottiene la categoria del plugin.
        
        Returns:
            PluginCategory: Categoria del plugin
        """
        pass
    
    @abstractmethod
    def get_plugin_priority(self) -> PluginPriority:
        """
        Ottiene la priorità di esecuzione del plugin.
        
        Returns:
            PluginPriority: Priorità del plugin
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[PluginCapability]:
        """
        Ottiene le capacità fornite dal plugin.
        
        Returns:
            List[PluginCapability]: Lista delle capacità
        """
        pass
    
    # === Plugin Lifecycle ===
    
    @abstractmethod
    async def activate(self) -> bool:
        """
        Attiva il plugin.
        
        Returns:
            bool: True se attivazione riuscita
        """
        pass
    
    @abstractmethod
    async def deactivate(self) -> bool:
        """
        Disattiva il plugin temporaneamente.
        
        Returns:
            bool: True se disattivazione riuscita
        """
        pass
    
    @abstractmethod
    async def is_active(self) -> bool:
        """
        Verifica se il plugin è attivo.
        
        Returns:
            bool: True se attivo
        """
        pass
    
    @abstractmethod
    async def reload(self) -> bool:
        """
        Ricarica il plugin con nuove configurazioni.
        
        Returns:
            bool: True se ricarica riuscita
        """
        pass
    
    # === Event Handling ===
    
    @abstractmethod
    async def handle_event(self, event: PluginEvent) -> Optional[Any]:
        """
        Gestisce un evento del sistema.
        
        Args:
            event: Evento da gestire
            
        Returns:
            Optional[Any]: Risultato della gestione (se applicabile)
        """
        pass
    
    @abstractmethod
    async def register_event_handler(
        self, 
        event_type: str, 
        handler: Callable[[PluginEvent], Any]
    ) -> bool:
        """
        Registra un gestore per un tipo di evento.
        
        Args:
            event_type: Tipo di evento da gestire
            handler: Funzione gestore
            
        Returns:
            bool: True se registrazione riuscita
        """
        pass
    
    @abstractmethod
    async def emit_event(self, event: PluginEvent) -> bool:
        """
        Emette un evento verso altri plugin o il sistema.
        
        Args:
            event: Evento da emettere
            
        Returns:
            bool: True se emissione riuscita
        """
        pass
    
    @abstractmethod
    async def get_supported_events(self) -> List[str]:
        """
        Ottiene i tipi di evento supportati dal plugin.
        
        Returns:
            List[str]: Lista dei tipi di evento
        """
        pass
    
    # === Inter-Plugin Communication ===
    
    @abstractmethod
    async def call_plugin_method(
        self, 
        plugin_name: str, 
        method_name: str, 
        *args, 
        **kwargs
    ) -> Optional[Any]:
        """
        Chiama un metodo di un altro plugin.
        
        Args:
            plugin_name: Nome del plugin target
            method_name: Nome del metodo da chiamare
            *args: Argomenti posizionali
            **kwargs: Argomenti nominali
            
        Returns:
            Optional[Any]: Risultato della chiamata
        """
        pass
    
    @abstractmethod
    async def get_plugin_api(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """
        Ottiene l'API pubblica di un altro plugin.
        
        Args:
            plugin_name: Nome del plugin
            
        Returns:
            Optional[Dict]: API del plugin se disponibile
        """
        pass
    
    @abstractmethod
    async def share_data(
        self, 
        data_key: str, 
        data_value: Any, 
        scope: str = "global"
    ) -> bool:
        """
        Condivide dati con altri plugin.
        
        Args:
            data_key: Chiave dei dati
            data_value: Valore da condividere
            scope: Ambito di condivisione ("global", "category", "specific")
            
        Returns:
            bool: True se condivisione riuscita
        """
        pass
    
    @abstractmethod
    async def get_shared_data(
        self, 
        data_key: str, 
        default: Any = None
    ) -> Any:
        """
        Ottiene dati condivisi da altri plugin.
        
        Args:
            data_key: Chiave dei dati
            default: Valore predefinito se non trovato
            
        Returns:
            Any: Valore dei dati condivisi
        """
        pass
    
    # === Configuration Management ===
    
    @abstractmethod
    async def get_config_schema(self) -> Dict[str, Any]:
        """
        Ottiene lo schema di configurazione del plugin.
        
        Returns:
            Dict: Schema JSON della configurazione
        """
        pass
    
    @abstractmethod
    async def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Valida una configurazione del plugin.
        
        Args:
            config: Configurazione da validare
            
        Returns:
            bool: True se configurazione valida
        """
        pass
    
    @abstractmethod
    async def update_config(self, new_config: Dict[str, Any]) -> bool:
        """
        Aggiorna la configurazione del plugin a runtime.
        
        Args:
            new_config: Nuova configurazione
            
        Returns:
            bool: True se aggiornamento riuscito
        """
        pass
    
    @abstractmethod
    async def get_current_config(self) -> Dict[str, Any]:
        """
        Ottiene la configurazione corrente del plugin.
        
        Returns:
            Dict: Configurazione corrente
        """
        pass
    
    # === Resource Management ===
    
    @abstractmethod
    async def get_resource_usage(self) -> Dict[str, Any]:
        """
        Ottiene l'utilizzo delle risorse del plugin.
        
        Returns:
            Dict: {
                "memory_mb": float,
                "cpu_percent": float,
                "disk_mb": float,
                "network_kb": float
            }
        """
        pass
    
    @abstractmethod
    async def set_resource_limits(self, limits: Dict[str, Any]) -> bool:
        """
        Imposta limiti di utilizzo delle risorse.
        
        Args:
            limits: Limiti da applicare
            
        Returns:
            bool: True se limiti impostati
        """
        pass
    
    @abstractmethod
    async def optimize_resources(self) -> bool:
        """
        Ottimizza l'utilizzo delle risorse del plugin.
        
        Returns:
            bool: True se ottimizzazione applicata
        """
        pass
    
    # === Health and Monitoring ===
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Esegue un controllo dello stato del plugin.
        
        Returns:
            Dict: {
                "status": str,  # "healthy", "warning", "error"
                "details": str,
                "last_check": float,
                "metrics": Dict[str, Any]
            }
        """
        pass
    
    @abstractmethod
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Ottiene metriche di performance del plugin.
        
        Returns:
            Dict: Metriche di performance
        """
        pass
    
    @abstractmethod
    async def reset_metrics(self) -> bool:
        """
        Resetta le metriche di performance.
        
        Returns:
            bool: True se reset riuscito
        """
        pass
    
    # === Plugin-Specific Features ===
    
    @abstractmethod
    async def execute_feature(
        self, 
        feature_name: str, 
        parameters: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Esegue una funzionalità specifica del plugin.
        
        Args:
            feature_name: Nome della funzionalità
            parameters: Parametri per l'esecuzione
            
        Returns:
            Optional[Any]: Risultato dell'esecuzione
        """
        pass
    
    @abstractmethod
    async def get_available_features(self) -> List[Dict[str, Any]]:
        """
        Ottiene le funzionalità disponibili del plugin.
        
        Returns:
            List[Dict]: Lista delle funzionalità con descrizioni
        """
        pass
    
    @abstractmethod
    async def schedule_task(
        self, 
        task_name: str, 
        task_function: Callable,
        schedule: str,
        **kwargs
    ) -> bool:
        """
        Programma un task periodico.
        
        Args:
            task_name: Nome del task
            task_function: Funzione da eseguire
            schedule: Programmazione (cron-like o interval)
            **kwargs: Parametri aggiuntivi
            
        Returns:
            bool: True se programmazione riuscita
        """
        pass
    
    @abstractmethod
    async def cancel_task(self, task_name: str) -> bool:
        """
        Cancella un task programmato.
        
        Args:
            task_name: Nome del task da cancellare
            
        Returns:
            bool: True se cancellazione riuscita
        """
        pass


class SecondaryPluginError(Exception):
    """Eccezione base per errori dei plugin secondari."""
    pass


class PluginInitializationError(SecondaryPluginError):
    """Errore nell'inizializzazione del plugin."""
    pass


class PluginConfigurationError(SecondaryPluginError):
    """Errore nella configurazione del plugin."""
    pass


class PluginCommunicationError(SecondaryPluginError):
    """Errore nella comunicazione tra plugin."""
    pass


class PluginResourceError(SecondaryPluginError):
    """Errore nelle risorse del plugin."""
    pass


class PluginFeatureError(SecondaryPluginError):
    """Errore nell'esecuzione di una funzionalità del plugin."""
    pass