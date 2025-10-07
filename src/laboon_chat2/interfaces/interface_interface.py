"""
Abstract interface for Interface Modules in LaboonChat v2.0

Defines the contract that all interface plugins must implement.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Callable, Union
from dataclasses import dataclass
import asyncio


@dataclass
class UIEvent:
    """Evento dell'interfaccia utente."""
    event_type: str  # "message_send", "peer_connect", "file_select", etc.
    data: Dict[str, Any]
    timestamp: float
    source: str  # "user", "system", "plugin"


@dataclass
class UIComponent:
    """Componente dell'interfaccia utente."""
    component_id: str
    component_type: str  # "button", "input", "display", "menu", etc.
    properties: Dict[str, Any]
    visible: bool = True
    enabled: bool = True


class IInterfaceModule(ABC):
    """
    Interfaccia astratta per moduli di interfaccia esclusivi.
    
    Ogni implementazione di interfaccia deve fornire:
    - Rendering dell'interfaccia utente
    - Gestione eventi utente
    - Aggiornamento display in tempo reale
    - Integrazione con moduli core
    """
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Inizializza il modulo di interfaccia.
        
        Args:
            config: Configurazione specifica del modulo
            
        Returns:
            bool: True se inizializzazione riuscita
        """
        pass
    
    @abstractmethod
    async def cleanup(self) -> bool:
        """
        Cleanup graceful del modulo prima dello scaricamento.
        
        Returns:
            bool: True se cleanup riuscito
        """
        pass
    
    # === Interface Lifecycle ===
    
    @abstractmethod
    async def start_interface(self) -> bool:
        """
        Avvia l'interfaccia utente.
        
        Returns:
            bool: True se avvio riuscito
        """
        pass
    
    @abstractmethod
    async def stop_interface(self) -> bool:
        """
        Ferma l'interfaccia utente.
        
        Returns:
            bool: True se fermata con successo
        """
        pass
    
    @abstractmethod
    async def is_running(self) -> bool:
        """
        Verifica se l'interfaccia è in esecuzione.
        
        Returns:
            bool: True se in esecuzione
        """
        pass
    
    @abstractmethod
    async def get_interface_info(self) -> Dict[str, Any]:
        """
        Ottiene informazioni sull'interfaccia.
        
        Returns:
            Dict: {
                "interface_type": str,  # "web", "desktop", "cli", "mobile"
                "version": str,
                "port": Optional[int],  # per interfacce web
                "url": Optional[str],   # per interfacce web
                "status": str
            }
        """
        pass
    
    # === Display Management ===
    
    @abstractmethod
    async def display_message(
        self, 
        message: Dict[str, Any],
        **kwargs
    ) -> bool:
        """
        Visualizza un messaggio nell'interfaccia.
        
        Args:
            message: Dati del messaggio da visualizzare
            **kwargs: Parametri di visualizzazione
            
        Returns:
            bool: True se visualizzazione riuscita
        """
        pass
    
    @abstractmethod
    async def update_peer_list(self, peers: List[Dict[str, Any]]) -> bool:
        """
        Aggiorna la lista dei peer visualizzata.
        
        Args:
            peers: Lista dei peer connessi
            
        Returns:
            bool: True se aggiornamento riuscito
        """
        pass
    
    @abstractmethod
    async def update_connection_status(
        self, 
        status: str, 
        details: Dict[str, Any]
    ) -> bool:
        """
        Aggiorna lo stato della connessione visualizzato.
        
        Args:
            status: Stato connessione ("connected", "disconnected", "connecting")
            details: Dettagli aggiuntivi
            
        Returns:
            bool: True se aggiornamento riuscito
        """
        pass
    
    @abstractmethod
    async def show_notification(
        self, 
        message: str, 
        notification_type: str = "info",
        duration: Optional[float] = None
    ) -> bool:
        """
        Mostra una notifica all'utente.
        
        Args:
            message: Messaggio della notifica
            notification_type: Tipo ("info", "warning", "error", "success")
            duration: Durata in secondi (None per persistente)
            
        Returns:
            bool: True se notifica mostrata
        """
        pass
    
    @abstractmethod
    async def clear_display(self, component: Optional[str] = None) -> bool:
        """
        Pulisce il display o un componente specifico.
        
        Args:
            component: Componente da pulire (None per tutto)
            
        Returns:
            bool: True se pulizia riuscita
        """
        pass
    
    # === User Input Handling ===
    
    @abstractmethod
    async def set_input_handler(
        self, 
        handler: Callable[[UIEvent], None]
    ) -> bool:
        """
        Imposta il gestore per gli input utente.
        
        Args:
            handler: Funzione da chiamare per ogni input utente
            
        Returns:
            bool: True se handler impostato
        """
        pass
    
    @abstractmethod
    async def get_user_input(
        self, 
        prompt: str, 
        input_type: str = "text",
        **kwargs
    ) -> Optional[str]:
        """
        Richiede input all'utente.
        
        Args:
            prompt: Messaggio di richiesta
            input_type: Tipo di input ("text", "password", "file", "choice")
            **kwargs: Parametri aggiuntivi (choices per "choice", etc.)
            
        Returns:
            Optional[str]: Input dell'utente o None se cancellato
        """
        pass
    
    @abstractmethod
    async def confirm_action(
        self, 
        message: str, 
        default: bool = False
    ) -> bool:
        """
        Richiede conferma all'utente per un'azione.
        
        Args:
            message: Messaggio di conferma
            default: Valore predefinito
            
        Returns:
            bool: True se confermato, False altrimenti
        """
        pass
    
    # === Component Management ===
    
    @abstractmethod
    async def add_component(self, component: UIComponent) -> bool:
        """
        Aggiunge un componente all'interfaccia.
        
        Args:
            component: Componente da aggiungere
            
        Returns:
            bool: True se aggiunta riuscita
        """
        pass
    
    @abstractmethod
    async def remove_component(self, component_id: str) -> bool:
        """
        Rimuove un componente dall'interfaccia.
        
        Args:
            component_id: ID del componente da rimuovere
            
        Returns:
            bool: True se rimozione riuscita
        """
        pass
    
    @abstractmethod
    async def update_component(
        self, 
        component_id: str, 
        properties: Dict[str, Any]
    ) -> bool:
        """
        Aggiorna le proprietà di un componente.
        
        Args:
            component_id: ID del componente
            properties: Nuove proprietà
            
        Returns:
            bool: True se aggiornamento riuscito
        """
        pass
    
    @abstractmethod
    async def get_component(self, component_id: str) -> Optional[UIComponent]:
        """
        Ottiene un componente per ID.
        
        Args:
            component_id: ID del componente
            
        Returns:
            Optional[UIComponent]: Componente se trovato
        """
        pass
    
    # === Layout Management ===
    
    @abstractmethod
    async def set_layout(self, layout_config: Dict[str, Any]) -> bool:
        """
        Imposta il layout dell'interfaccia.
        
        Args:
            layout_config: Configurazione del layout
            
        Returns:
            bool: True se layout impostato
        """
        pass
    
    @abstractmethod
    async def get_layout(self) -> Dict[str, Any]:
        """
        Ottiene la configurazione del layout corrente.
        
        Returns:
            Dict: Configurazione del layout
        """
        pass
    
    @abstractmethod
    async def refresh_interface(self) -> bool:
        """
        Aggiorna completamente l'interfaccia.
        
        Returns:
            bool: True se aggiornamento riuscito
        """
        pass
    
    # === Theme and Styling ===
    
    @abstractmethod
    async def set_theme(self, theme_name: str) -> bool:
        """
        Imposta il tema dell'interfaccia.
        
        Args:
            theme_name: Nome del tema
            
        Returns:
            bool: True se tema impostato
        """
        pass
    
    @abstractmethod
    async def get_available_themes(self) -> List[str]:
        """
        Ottiene i temi disponibili.
        
        Returns:
            List[str]: Lista dei nomi dei temi
        """
        pass
    
    @abstractmethod
    async def customize_style(
        self, 
        component_id: str, 
        styles: Dict[str, Any]
    ) -> bool:
        """
        Personalizza lo stile di un componente.
        
        Args:
            component_id: ID del componente
            styles: Stili da applicare
            
        Returns:
            bool: True se personalizzazione riuscita
        """
        pass
    
    # === File Operations ===
    
    @abstractmethod
    async def select_file(
        self, 
        file_types: Optional[List[str]] = None,
        multiple: bool = False
    ) -> Optional[Union[str, List[str]]]:
        """
        Apre un dialog per selezionare file.
        
        Args:
            file_types: Tipi di file accettati
            multiple: Permette selezione multipla
            
        Returns:
            Optional[Union[str, List[str]]]: Percorso/i file selezionato/i
        """
        pass
    
    @abstractmethod
    async def save_file_dialog(
        self, 
        default_name: Optional[str] = None,
        file_types: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Apre un dialog per salvare file.
        
        Args:
            default_name: Nome predefinito del file
            file_types: Tipi di file supportati
            
        Returns:
            Optional[str]: Percorso dove salvare il file
        """
        pass
    
    # === Configuration ===
    
    @abstractmethod
    async def get_supported_features(self) -> List[str]:
        """
        Ottiene le funzionalità supportate dall'interfaccia.
        
        Returns:
            List[str]: ["notifications", "file_dialogs", "themes", etc.]
        """
        pass
    
    @abstractmethod
    async def update_config(self, new_config: Dict[str, Any]) -> bool:
        """
        Aggiorna la configurazione del modulo a runtime.
        
        Args:
            new_config: Nuova configurazione
            
        Returns:
            bool: True se aggiornamento riuscito
        """
        pass
    
    @abstractmethod
    async def export_interface_state(self) -> Dict[str, Any]:
        """
        Esporta lo stato corrente dell'interfaccia.
        
        Returns:
            Dict: Stato dell'interfaccia serializzabile
        """
        pass
    
    @abstractmethod
    async def import_interface_state(self, state: Dict[str, Any]) -> bool:
        """
        Importa uno stato dell'interfaccia.
        
        Args:
            state: Stato da importare
            
        Returns:
            bool: True se importazione riuscita
        """
        pass


class InterfaceModuleError(Exception):
    """Eccezione base per errori dei moduli di interfaccia."""
    pass


class UIRenderError(InterfaceModuleError):
    """Errore nel rendering dell'interfaccia."""
    pass


class UserInputError(InterfaceModuleError):
    """Errore nell'input utente."""
    pass


class ComponentError(InterfaceModuleError):
    """Errore nella gestione dei componenti."""
    pass


class LayoutError(InterfaceModuleError):
    """Errore nel layout."""
    pass


class ThemeError(InterfaceModuleError):
    """Errore nei temi."""
    pass