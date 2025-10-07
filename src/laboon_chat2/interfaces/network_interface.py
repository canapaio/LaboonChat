"""
Abstract interface for Network Modules in LaboonChat v2.0

Defines the contract that all network plugins must implement.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Tuple, Callable, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime
import asyncio


@dataclass
class NetworkPeer:
    """Informazioni su un peer di rete."""
    peer_id: str
    address: str
    port: int
    protocol: str  # "tcp", "udp", "websocket", etc.
    last_seen: datetime
    latency: Optional[float] = None  # in millisecondi
    bandwidth: Optional[float] = None  # in bytes/sec
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class NetworkPacket:
    """Pacchetto di rete."""
    packet_id: str
    source_peer: str
    destination_peer: Optional[str]  # None per broadcast
    data: bytes
    packet_type: str  # "message", "control", "discovery", etc.
    timestamp: datetime
    priority: int = 0  # 0 = normale, 1 = alta, -1 = bassa
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class NetworkStats:
    """Statistiche di rete."""
    packets_sent: int
    packets_received: int
    bytes_sent: int
    bytes_received: int
    connections_active: int
    connections_total: int
    uptime: float
    average_latency: Optional[float] = None
    packet_loss_rate: Optional[float] = None


class INetworkModule(ABC):
    """
    Interfaccia astratta per moduli di rete esclusivi.
    
    Ogni implementazione di rete deve fornire:
    - Gestione connessioni di basso livello
    - Routing e discovery di rete
    - Ottimizzazione del traffico
    - Monitoraggio delle prestazioni
    """
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Inizializza il modulo di rete.
        
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
    
    # === Network Lifecycle ===
    
    @abstractmethod
    async def start_network(self) -> bool:
        """
        Avvia il modulo di rete.
        
        Returns:
            bool: True se avvio riuscito
        """
        pass
    
    @abstractmethod
    async def stop_network(self) -> bool:
        """
        Ferma il modulo di rete.
        
        Returns:
            bool: True se fermata riuscita
        """
        pass
    
    @abstractmethod
    async def is_network_active(self) -> bool:
        """
        Verifica se la rete è attiva.
        
        Returns:
            bool: True se rete attiva
        """
        pass
    
    @abstractmethod
    async def get_network_info(self) -> Dict[str, Any]:
        """
        Ottiene informazioni sulla rete.
        
        Returns:
            Dict: {
                "network_type": str,  # "p2p", "hybrid", "centralized"
                "protocols": List[str],
                "local_address": str,
                "listening_ports": List[int],
                "status": str
            }
        """
        pass
    
    # === Connection Management ===
    
    @abstractmethod
    async def create_connection(
        self, 
        peer_address: str, 
        peer_port: int,
        protocol: str = "tcp",
        **kwargs
    ) -> Optional[str]:
        """
        Crea una connessione a un peer.
        
        Args:
            peer_address: Indirizzo del peer
            peer_port: Porta del peer
            protocol: Protocollo da usare
            **kwargs: Parametri aggiuntivi
            
        Returns:
            Optional[str]: ID della connessione se riuscita
        """
        pass
    
    @abstractmethod
    async def close_connection(self, connection_id: str) -> bool:
        """
        Chiude una connessione specifica.
        
        Args:
            connection_id: ID della connessione da chiudere
            
        Returns:
            bool: True se chiusura riuscita
        """
        pass
    
    @abstractmethod
    async def get_active_connections(self) -> List[Dict[str, Any]]:
        """
        Ottiene le connessioni attive.
        
        Returns:
            List[Dict]: Lista delle connessioni con dettagli
        """
        pass
    
    @abstractmethod
    async def listen_on_port(
        self, 
        port: int, 
        protocol: str = "tcp",
        **kwargs
    ) -> bool:
        """
        Inizia ad ascoltare su una porta specifica.
        
        Args:
            port: Porta su cui ascoltare
            protocol: Protocollo da usare
            **kwargs: Parametri aggiuntivi
            
        Returns:
            bool: True se ascolto avviato
        """
        pass
    
    @abstractmethod
    async def stop_listening(self, port: int, protocol: str = "tcp") -> bool:
        """
        Ferma l'ascolto su una porta.
        
        Args:
            port: Porta da cui smettere di ascoltare
            protocol: Protocollo
            
        Returns:
            bool: True se fermata riuscita
        """
        pass
    
    # === Packet Handling ===
    
    @abstractmethod
    async def send_packet(
        self, 
        packet: NetworkPacket,
        **kwargs
    ) -> bool:
        """
        Invia un pacchetto di rete.
        
        Args:
            packet: Pacchetto da inviare
            **kwargs: Parametri aggiuntivi (retry, timeout, etc.)
            
        Returns:
            bool: True se invio riuscito
        """
        pass
    
    @abstractmethod
    async def broadcast_packet(
        self, 
        data: bytes, 
        packet_type: str = "broadcast",
        **kwargs
    ) -> int:
        """
        Invia un pacchetto in broadcast.
        
        Args:
            data: Dati da inviare
            packet_type: Tipo di pacchetto
            **kwargs: Parametri aggiuntivi
            
        Returns:
            int: Numero di peer che hanno ricevuto il pacchetto
        """
        pass
    
    @abstractmethod
    async def set_packet_handler(
        self, 
        handler: Callable[[NetworkPacket], None]
    ) -> bool:
        """
        Imposta il gestore per i pacchetti in arrivo.
        
        Args:
            handler: Funzione da chiamare per ogni pacchetto ricevuto
            
        Returns:
            bool: True se handler impostato
        """
        pass
    
    @abstractmethod
    async def listen_for_packets(self) -> AsyncGenerator[NetworkPacket, None]:
        """
        Generator asincrono per ascoltare pacchetti in arrivo.
        
        Yields:
            NetworkPacket: Pacchetti ricevuti in tempo reale
        """
        pass
    
    # === Peer Discovery ===
    
    @abstractmethod
    async def discover_peers(
        self, 
        discovery_method: str = "auto",
        timeout: float = 30.0,
        **kwargs
    ) -> List[NetworkPeer]:
        """
        Scopre peer nella rete.
        
        Args:
            discovery_method: Metodo di discovery
            timeout: Timeout per la discovery
            **kwargs: Parametri specifici del metodo
            
        Returns:
            List[NetworkPeer]: Peer scoperti
        """
        pass
    
    @abstractmethod
    async def announce_presence(
        self, 
        announcement_data: Dict[str, Any],
        **kwargs
    ) -> bool:
        """
        Annuncia la propria presenza nella rete.
        
        Args:
            announcement_data: Dati da includere nell'annuncio
            **kwargs: Parametri aggiuntivi
            
        Returns:
            bool: True se annuncio riuscito
        """
        pass
    
    @abstractmethod
    async def get_peer_info(self, peer_id: str) -> Optional[NetworkPeer]:
        """
        Ottiene informazioni su un peer specifico.
        
        Args:
            peer_id: ID del peer
            
        Returns:
            Optional[NetworkPeer]: Informazioni del peer se trovato
        """
        pass
    
    @abstractmethod
    async def update_peer_info(
        self, 
        peer_id: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """
        Aggiorna le informazioni di un peer.
        
        Args:
            peer_id: ID del peer
            updates: Aggiornamenti da applicare
            
        Returns:
            bool: True se aggiornamento riuscito
        """
        pass
    
    # === Routing ===
    
    @abstractmethod
    async def find_route_to_peer(
        self, 
        target_peer_id: str
    ) -> Optional[List[str]]:
        """
        Trova un percorso verso un peer specifico.
        
        Args:
            target_peer_id: ID del peer di destinazione
            
        Returns:
            Optional[List[str]]: Lista di peer ID che formano il percorso
        """
        pass
    
    @abstractmethod
    async def route_packet(
        self, 
        packet: NetworkPacket, 
        route: List[str]
    ) -> bool:
        """
        Instrada un pacchetto attraverso un percorso specifico.
        
        Args:
            packet: Pacchetto da instradare
            route: Percorso da seguire
            
        Returns:
            bool: True se instradamento riuscito
        """
        pass
    
    @abstractmethod
    async def get_routing_table(self) -> Dict[str, List[str]]:
        """
        Ottiene la tabella di routing corrente.
        
        Returns:
            Dict[str, List[str]]: {peer_id: [route_to_peer]}
        """
        pass
    
    @abstractmethod
    async def update_routing_table(
        self, 
        updates: Dict[str, List[str]]
    ) -> bool:
        """
        Aggiorna la tabella di routing.
        
        Args:
            updates: Aggiornamenti alla tabella
            
        Returns:
            bool: True se aggiornamento riuscito
        """
        pass
    
    # === Quality of Service ===
    
    @abstractmethod
    async def measure_latency(self, peer_id: str) -> Optional[float]:
        """
        Misura la latenza verso un peer.
        
        Args:
            peer_id: ID del peer
            
        Returns:
            Optional[float]: Latenza in millisecondi
        """
        pass
    
    @abstractmethod
    async def measure_bandwidth(
        self, 
        peer_id: str, 
        test_duration: float = 5.0
    ) -> Optional[float]:
        """
        Misura la banda disponibile verso un peer.
        
        Args:
            peer_id: ID del peer
            test_duration: Durata del test in secondi
            
        Returns:
            Optional[float]: Banda in bytes/sec
        """
        pass
    
    @abstractmethod
    async def set_qos_policy(
        self, 
        policy: Dict[str, Any]
    ) -> bool:
        """
        Imposta una politica di Quality of Service.
        
        Args:
            policy: Configurazione della politica QoS
            
        Returns:
            bool: True se politica impostata
        """
        pass
    
    @abstractmethod
    async def get_network_stats(self) -> NetworkStats:
        """
        Ottiene statistiche di rete dettagliate.
        
        Returns:
            NetworkStats: Statistiche correnti
        """
        pass
    
    # === Security ===
    
    @abstractmethod
    async def validate_peer(
        self, 
        peer_id: str, 
        validation_data: Dict[str, Any]
    ) -> bool:
        """
        Valida l'identità di un peer.
        
        Args:
            peer_id: ID del peer da validare
            validation_data: Dati per la validazione
            
        Returns:
            bool: True se peer valido
        """
        pass
    
    @abstractmethod
    async def blacklist_peer(self, peer_id: str, reason: str) -> bool:
        """
        Aggiunge un peer alla blacklist.
        
        Args:
            peer_id: ID del peer da blacklistare
            reason: Motivo del blacklisting
            
        Returns:
            bool: True se aggiunta riuscita
        """
        pass
    
    @abstractmethod
    async def whitelist_peer(self, peer_id: str) -> bool:
        """
        Aggiunge un peer alla whitelist.
        
        Args:
            peer_id: ID del peer da whitelistare
            
        Returns:
            bool: True se aggiunta riuscita
        """
        pass
    
    @abstractmethod
    async def get_blacklisted_peers(self) -> List[Tuple[str, str]]:
        """
        Ottiene la lista dei peer blacklistati.
        
        Returns:
            List[Tuple[str, str]]: [(peer_id, reason), ...]
        """
        pass
    
    # === Configuration ===
    
    @abstractmethod
    async def get_supported_protocols(self) -> List[str]:
        """
        Ottiene i protocolli supportati dal modulo.
        
        Returns:
            List[str]: Lista dei protocolli supportati
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
    async def optimize_network(self, optimization_type: str = "auto") -> bool:
        """
        Ottimizza le prestazioni di rete.
        
        Args:
            optimization_type: Tipo di ottimizzazione ("latency", "bandwidth", "auto")
            
        Returns:
            bool: True se ottimizzazione applicata
        """
        pass


class NetworkModuleError(Exception):
    """Eccezione base per errori dei moduli di rete."""
    pass


class ConnectionError(NetworkModuleError):
    """Errore di connessione di rete."""
    pass


class PacketError(NetworkModuleError):
    """Errore nella gestione dei pacchetti."""
    pass


class DiscoveryError(NetworkModuleError):
    """Errore nel discovery dei peer."""
    pass


class RoutingError(NetworkModuleError):
    """Errore nel routing."""
    pass


class QoSError(NetworkModuleError):
    """Errore nella Quality of Service."""
    pass


class SecurityError(NetworkModuleError):
    """Errore di sicurezza di rete."""
    pass