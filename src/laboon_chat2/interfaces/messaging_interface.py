"""
Abstract interface for Messaging Modules in LaboonChat v2.0

Defines the contract that all messaging plugins must implement.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Callable, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime
import asyncio


@dataclass
class Message:
    """Struttura dati per un messaggio."""
    id: str
    sender_id: str
    recipient_id: Optional[str]  # None per messaggi broadcast
    content: str
    timestamp: datetime
    message_type: str = "text"  # text, file, system, etc.
    metadata: Dict[str, Any] = None
    encrypted: bool = False
    signature: Optional[bytes] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class PeerInfo:
    """Informazioni su un peer connesso."""
    peer_id: str
    display_name: str
    public_key: str
    last_seen: datetime
    connection_status: str  # "connected", "disconnected", "connecting"
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class IMessagingModule(ABC):
    """
    Interfaccia astratta per moduli di messaging esclusivi.
    
    Ogni implementazione di messaging deve fornire:
    - Gestione connessioni P2P
    - Invio/ricezione messaggi
    - Discovery e gestione peer
    - Sincronizzazione messaggi
    """
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Inizializza il modulo di messaging.
        
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
    
    # === Connection Management ===
    
    @abstractmethod
    async def start_listening(self, port: Optional[int] = None) -> bool:
        """
        Avvia l'ascolto per connessioni in entrata.
        
        Args:
            port: Porta su cui ascoltare (None per porta automatica)
            
        Returns:
            bool: True se ascolto avviato con successo
        """
        pass
    
    @abstractmethod
    async def stop_listening(self) -> bool:
        """
        Ferma l'ascolto per connessioni in entrata.
        
        Returns:
            bool: True se fermato con successo
        """
        pass
    
    @abstractmethod
    async def connect_to_peer(
        self, 
        peer_address: str, 
        peer_port: int,
        **kwargs
    ) -> bool:
        """
        Connette a un peer specifico.
        
        Args:
            peer_address: Indirizzo IP o hostname del peer
            peer_port: Porta del peer
            **kwargs: Parametri aggiuntivi (timeout, retry, etc.)
            
        Returns:
            bool: True se connessione riuscita
        """
        pass
    
    @abstractmethod
    async def disconnect_from_peer(self, peer_id: str) -> bool:
        """
        Disconnette da un peer specifico.
        
        Args:
            peer_id: ID del peer da disconnettere
            
        Returns:
            bool: True se disconnessione riuscita
        """
        pass
    
    @abstractmethod
    async def get_connection_info(self) -> Dict[str, Any]:
        """
        Ottiene informazioni sulla connessione corrente.
        
        Returns:
            Dict: {
                "listening_port": int,
                "local_address": str,
                "is_listening": bool,
                "connected_peers": int
            }
        """
        pass
    
    # === Peer Discovery ===
    
    @abstractmethod
    async def discover_peers(
        self, 
        discovery_method: str = "auto",
        **kwargs
    ) -> List[PeerInfo]:
        """
        Scopre peer disponibili nella rete.
        
        Args:
            discovery_method: Metodo di discovery ("broadcast", "dht", "tracker", "auto")
            **kwargs: Parametri specifici del metodo
            
        Returns:
            List[PeerInfo]: Lista dei peer scoperti
        """
        pass
    
    @abstractmethod
    async def announce_presence(self, **kwargs) -> bool:
        """
        Annuncia la propria presenza nella rete.
        
        Args:
            **kwargs: Parametri per l'annuncio
            
        Returns:
            bool: True se annuncio riuscito
        """
        pass
    
    @abstractmethod
    async def get_connected_peers(self) -> List[PeerInfo]:
        """
        Ottiene la lista dei peer attualmente connessi.
        
        Returns:
            List[PeerInfo]: Lista dei peer connessi
        """
        pass
    
    # === Message Handling ===
    
    @abstractmethod
    async def send_message(
        self, 
        message: Message,
        **kwargs
    ) -> bool:
        """
        Invia un messaggio a un peer o in broadcast.
        
        Args:
            message: Messaggio da inviare
            **kwargs: Parametri aggiuntivi (priority, retry, etc.)
            
        Returns:
            bool: True se invio riuscito
        """
        pass
    
    @abstractmethod
    async def send_direct_message(
        self, 
        peer_id: str, 
        content: str,
        message_type: str = "text",
        **kwargs
    ) -> bool:
        """
        Invia un messaggio diretto a un peer specifico.
        
        Args:
            peer_id: ID del destinatario
            content: Contenuto del messaggio
            message_type: Tipo di messaggio
            **kwargs: Parametri aggiuntivi
            
        Returns:
            bool: True se invio riuscito
        """
        pass
    
    @abstractmethod
    async def broadcast_message(
        self, 
        content: str,
        message_type: str = "text",
        **kwargs
    ) -> int:
        """
        Invia un messaggio in broadcast a tutti i peer connessi.
        
        Args:
            content: Contenuto del messaggio
            message_type: Tipo di messaggio
            **kwargs: Parametri aggiuntivi
            
        Returns:
            int: Numero di peer che hanno ricevuto il messaggio
        """
        pass
    
    @abstractmethod
    async def get_message_history(
        self, 
        peer_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Message]:
        """
        Ottiene la cronologia dei messaggi.
        
        Args:
            peer_id: ID del peer (None per tutti i messaggi)
            limit: Numero massimo di messaggi da restituire
            offset: Offset per paginazione
            
        Returns:
            List[Message]: Lista dei messaggi
        """
        pass
    
    # === Event Handling ===
    
    @abstractmethod
    async def set_message_handler(
        self, 
        handler: Callable[[Message], None]
    ) -> bool:
        """
        Imposta il gestore per i messaggi in arrivo.
        
        Args:
            handler: Funzione da chiamare per ogni messaggio ricevuto
            
        Returns:
            bool: True se handler impostato con successo
        """
        pass
    
    @abstractmethod
    async def set_peer_event_handler(
        self, 
        handler: Callable[[str, PeerInfo, str], None]
    ) -> bool:
        """
        Imposta il gestore per eventi dei peer.
        
        Args:
            handler: Funzione da chiamare per eventi peer
                    (event_type, peer_info, additional_data)
                    event_type: "connected", "disconnected", "discovered"
            
        Returns:
            bool: True se handler impostato con successo
        """
        pass
    
    @abstractmethod
    async def listen_for_messages(self) -> AsyncGenerator[Message, None]:
        """
        Generator asincrono per ascoltare messaggi in arrivo.
        
        Yields:
            Message: Messaggi ricevuti in tempo reale
        """
        pass
    
    # === File Transfer ===
    
    @abstractmethod
    async def send_file(
        self, 
        peer_id: str, 
        file_path: str,
        **kwargs
    ) -> bool:
        """
        Invia un file a un peer.
        
        Args:
            peer_id: ID del destinatario
            file_path: Percorso del file da inviare
            **kwargs: Parametri aggiuntivi (chunk_size, compression, etc.)
            
        Returns:
            bool: True se invio riuscito
        """
        pass
    
    @abstractmethod
    async def receive_file(
        self, 
        message_id: str, 
        save_path: str,
        **kwargs
    ) -> bool:
        """
        Riceve un file da un messaggio.
        
        Args:
            message_id: ID del messaggio contenente il file
            save_path: Percorso dove salvare il file
            **kwargs: Parametri aggiuntivi
            
        Returns:
            bool: True se ricezione riuscita
        """
        pass
    
    # === Message Synchronization ===
    
    @abstractmethod
    async def sync_messages_with_peer(
        self, 
        peer_id: str,
        since: Optional[datetime] = None
    ) -> int:
        """
        Sincronizza i messaggi con un peer specifico.
        
        Args:
            peer_id: ID del peer con cui sincronizzare
            since: Timestamp da cui iniziare la sincronizzazione
            
        Returns:
            int: Numero di messaggi sincronizzati
        """
        pass
    
    @abstractmethod
    async def request_message_history(
        self, 
        peer_id: str,
        from_timestamp: datetime,
        to_timestamp: Optional[datetime] = None
    ) -> List[Message]:
        """
        Richiede la cronologia messaggi a un peer.
        
        Args:
            peer_id: ID del peer da cui richiedere
            from_timestamp: Timestamp di inizio
            to_timestamp: Timestamp di fine (None per ora corrente)
            
        Returns:
            List[Message]: Messaggi ricevuti dal peer
        """
        pass
    
    # === Configuration ===
    
    @abstractmethod
    async def get_supported_protocols(self) -> List[str]:
        """
        Ottiene i protocolli supportati dal modulo.
        
        Returns:
            List[str]: ["tcp", "udp", "websocket", "torrent", etc.]
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
    async def get_network_stats(self) -> Dict[str, Any]:
        """
        Ottiene statistiche di rete del modulo.
        
        Returns:
            Dict: {
                "messages_sent": int,
                "messages_received": int,
                "bytes_sent": int,
                "bytes_received": int,
                "active_connections": int,
                "uptime": float
            }
        """
        pass


class MessagingModuleError(Exception):
    """Eccezione base per errori dei moduli di messaging."""
    pass


class ConnectionError(MessagingModuleError):
    """Errore di connessione."""
    pass


class MessageDeliveryError(MessagingModuleError):
    """Errore nella consegna del messaggio."""
    pass


class PeerDiscoveryError(MessagingModuleError):
    """Errore nel discovery dei peer."""
    pass


class FileTransferError(MessagingModuleError):
    """Errore nel trasferimento file."""
    pass


class SynchronizationError(MessagingModuleError):
    """Errore nella sincronizzazione."""
    pass