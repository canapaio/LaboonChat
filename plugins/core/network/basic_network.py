"""
BasicNetworkModule - Plugin Network Core per LaboonChat2

Fornisce funzionalità di rete di base per comunicazioni P2P:
- Gestione connessioni P2P
- Discovery automatico dei peer
- Routing intelligente dei messaggi
- Gestione della topologia di rete
- Monitoraggio stato connessioni
- Bilanciamento del carico
- Gestione della latenza
- Recupero automatico da disconnessioni
"""

import asyncio
import socket
import json
import time
import hashlib
import random
from typing import Dict, List, Optional, Set, Tuple, Any, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
from enum import Enum
import ipaddress
import struct

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from laboon_chat2.core.interfaces import INetworkModule


class ConnectionStatus(Enum):
    """Stati delle connessioni"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


class PeerType(Enum):
    """Tipi di peer"""
    REGULAR = "regular"
    BOOTSTRAP = "bootstrap"
    RELAY = "relay"
    BRIDGE = "bridge"


class MessagePriority(Enum):
    """Priorità dei messaggi"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class NetworkPeer:
    """Informazioni su un peer di rete"""
    id: str
    address: str
    port: int
    peer_type: PeerType = PeerType.REGULAR
    status: ConnectionStatus = ConnectionStatus.DISCONNECTED
    last_seen: float = 0.0
    latency: float = 0.0
    reliability: float = 1.0
    bandwidth: int = 0
    connection_count: int = 0
    version: str = "1.0.0"
    capabilities: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []
        if self.metadata is None:
            self.metadata = {}
        if self.last_seen == 0.0:
            self.last_seen = time.time()


@dataclass
class NetworkConnection:
    """Informazioni su una connessione di rete"""
    id: str
    peer_id: str
    local_address: str
    local_port: int
    remote_address: str
    remote_port: int
    status: ConnectionStatus = ConnectionStatus.DISCONNECTED
    established_at: float = 0.0
    last_activity: float = 0.0
    bytes_sent: int = 0
    bytes_received: int = 0
    messages_sent: int = 0
    messages_received: int = 0
    latency: float = 0.0
    quality: float = 1.0
    reader: Optional[asyncio.StreamReader] = None
    writer: Optional[asyncio.StreamWriter] = None
    
    def __post_init__(self):
        if self.established_at == 0.0:
            self.established_at = time.time()
        if self.last_activity == 0.0:
            self.last_activity = time.time()


@dataclass
class NetworkMessage:
    """Messaggio di rete"""
    id: str
    source_id: str
    destination_id: str
    message_type: str
    payload: bytes
    priority: MessagePriority = MessagePriority.NORMAL
    ttl: int = 10
    timestamp: float = 0.0
    route: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()
        if self.route is None:
            self.route = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class NetworkStats:
    """Statistiche di rete"""
    total_peers: int = 0
    connected_peers: int = 0
    active_connections: int = 0
    total_messages_sent: int = 0
    total_messages_received: int = 0
    total_bytes_sent: int = 0
    total_bytes_received: int = 0
    average_latency: float = 0.0
    network_quality: float = 1.0
    uptime: float = 0.0
    last_updated: float = 0.0
    
    def __post_init__(self):
        if self.last_updated == 0.0:
            self.last_updated = time.time()


class BasicNetworkModule(INetworkModule):
    """
    Modulo di rete di base per LaboonChat2
    
    Implementa funzionalità di rete P2P con:
    - Gestione connessioni automatica
    - Discovery peer intelligente
    - Routing ottimizzato
    - Monitoraggio qualità rete
    """
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.peers: Dict[str, NetworkPeer] = {}
        self.connections: Dict[str, NetworkConnection] = {}
        self.routing_table: Dict[str, str] = {}  # destination_id -> next_hop_id
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.stats = NetworkStats()
        
        # Server e task asincroni
        self.server: Optional[asyncio.Server] = None
        self.discovery_server: Optional[asyncio.Server] = None
        self.message_processor_task: Optional[asyncio.Task] = None
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.discovery_task: Optional[asyncio.Task] = None
        self.maintenance_task: Optional[asyncio.Task] = None
        
        # Handler eventi
        self.peer_handler: Optional[Callable] = None
        self.connection_handler: Optional[Callable] = None
        self.message_handler: Optional[Callable] = None
        
        # Stato interno
        self.node_id: str = ""
        self.running = False
        self.bootstrap_peers: List[Tuple[str, int]] = []
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Inizializza il modulo di rete"""
        self.config = config.copy()
        
        # Genera ID nodo univoco
        self.node_id = self._generate_node_id()
        
        # Carica configurazione
        self.bootstrap_peers = config.get("bootstrap_peers", [])
        
        # Crea directory per dati persistenti
        data_dir = Path(config.get("data_dir", "data/network"))
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Carica dati persistenti
        await self._load_persistent_data()
        
        # Avvia server di rete
        await self._start_network_server()
        
        # Avvia server di discovery
        if config.get("enable_discovery", True):
            await self._start_discovery_server()
        
        # Avvia task asincroni
        await self._start_background_tasks()
        
        self.running = True
        self.stats.uptime = time.time()
        
        self.logger.info(f"BasicNetworkModule inizializzato - Node ID: {self.node_id}")
    
    async def cleanup(self) -> None:
        """Pulisce le risorse del modulo"""
        self.running = False
        
        # Ferma task asincroni
        await self._stop_background_tasks()
        
        # Chiudi tutte le connessioni
        await self._close_all_connections()
        
        # Ferma server
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.server = None
        
        if self.discovery_server:
            self.discovery_server.close()
            await self.discovery_server.wait_closed()
            self.discovery_server = None
        
        # Salva dati persistenti
        await self._save_persistent_data()
        
        self.logger.info("BasicNetworkModule terminato")
    
    def get_module_info(self) -> Dict[str, Any]:
        """Restituisce informazioni sul modulo"""
        return {
            "name": "BasicNetworkModule",
            "version": "1.0.0",
            "type": "network",
            "description": "Modulo di rete P2P di base con discovery automatico e routing intelligente",
            "author": "LaboonChat2 Team",
            "capabilities": [
                "p2p_connections",
                "peer_discovery",
                "message_routing",
                "network_monitoring",
                "auto_recovery",
                "load_balancing"
            ]
        }
    
    # Implementazione INetworkModule
    
    async def connect_to_peer(self, address: str, port: int, peer_id: str = None) -> bool:
        """Connette a un peer specifico"""
        try:
            # Genera ID peer se non fornito
            if peer_id is None:
                peer_id = f"{address}:{port}"
            
            # Verifica se già connesso
            if peer_id in self.connections:
                connection = self.connections[peer_id]
                if connection.status == ConnectionStatus.CONNECTED:
                    return True
            
            # Crea connessione
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(address, port),
                timeout=self.config.get("connection_timeout", 10.0)
            )
            
            # Crea oggetti peer e connessione
            peer = NetworkPeer(
                id=peer_id,
                address=address,
                port=port,
                status=ConnectionStatus.CONNECTED,
                last_seen=time.time()
            )
            
            connection = NetworkConnection(
                id=f"conn_{peer_id}_{int(time.time())}",
                peer_id=peer_id,
                local_address=writer.get_extra_info('sockname')[0],
                local_port=writer.get_extra_info('sockname')[1],
                remote_address=address,
                remote_port=port,
                status=ConnectionStatus.CONNECTED,
                reader=reader,
                writer=writer
            )
            
            # Salva peer e connessione
            self.peers[peer_id] = peer
            self.connections[peer_id] = connection
            
            # Avvia gestione connessione
            asyncio.create_task(self._handle_connection(connection))
            
            # Invia handshake
            await self._send_handshake(connection)
            
            # Notifica evento
            await self._notify_peer_event(peer_id, "connected")
            
            self.stats.connected_peers += 1
            self.stats.active_connections += 1
            
            self.logger.info(f"Connesso a peer {peer_id} ({address}:{port})")
            return True
            
        except Exception as e:
            self.logger.error(f"Errore connessione a {address}:{port}: {e}")
            return False
    
    async def disconnect_from_peer(self, peer_id: str) -> bool:
        """Disconnette da un peer specifico"""
        try:
            if peer_id not in self.connections:
                return False
            
            connection = self.connections[peer_id]
            
            # Chiudi connessione
            if connection.writer:
                connection.writer.close()
                await connection.writer.wait_closed()
            
            # Aggiorna stato
            connection.status = ConnectionStatus.DISCONNECTED
            if peer_id in self.peers:
                self.peers[peer_id].status = ConnectionStatus.DISCONNECTED
            
            # Rimuovi dalla routing table
            self._update_routing_table_on_disconnect(peer_id)
            
            # Notifica evento
            await self._notify_peer_event(peer_id, "disconnected")
            
            self.stats.connected_peers = max(0, self.stats.connected_peers - 1)
            self.stats.active_connections = max(0, self.stats.active_connections - 1)
            
            self.logger.info(f"Disconnesso da peer {peer_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Errore disconnessione da {peer_id}: {e}")
            return False
    
    async def send_message(self, destination_id: str, message_type: str, payload: bytes, priority: str = "normal") -> bool:
        """Invia un messaggio a un peer"""
        try:
            # Converti priorità
            priority_enum = MessagePriority.NORMAL
            if priority == "low":
                priority_enum = MessagePriority.LOW
            elif priority == "high":
                priority_enum = MessagePriority.HIGH
            elif priority == "urgent":
                priority_enum = MessagePriority.URGENT
            
            # Crea messaggio
            message = NetworkMessage(
                id=self._generate_message_id(),
                source_id=self.node_id,
                destination_id=destination_id,
                message_type=message_type,
                payload=payload,
                priority=priority_enum
            )
            
            # Aggiungi alla coda
            await self.message_queue.put(message)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Errore invio messaggio a {destination_id}: {e}")
            return False
    
    async def broadcast_message(self, message_type: str, payload: bytes, exclude_peers: List[str] = None) -> int:
        """Invia un messaggio a tutti i peer connessi"""
        if exclude_peers is None:
            exclude_peers = []
        
        sent_count = 0
        
        for peer_id in self.connections:
            if peer_id not in exclude_peers:
                connection = self.connections[peer_id]
                if connection.status == ConnectionStatus.CONNECTED:
                    success = await self.send_message(peer_id, message_type, payload)
                    if success:
                        sent_count += 1
        
        return sent_count
    
    async def discover_peers(self, timeout: float = 5.0) -> List[str]:
        """Scopre peer nella rete locale"""
        discovered_peers = []
        
        try:
            # Broadcast discovery su rete locale
            discovery_message = {
                "type": "discovery_request",
                "node_id": self.node_id,
                "timestamp": time.time(),
                "capabilities": self.get_module_info()["capabilities"]
            }
            
            # Invia su porta discovery
            discovery_port = self.config.get("discovery_port", 8889)
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(timeout)
            
            try:
                # Broadcast
                message_data = json.dumps(discovery_message).encode()
                sock.sendto(message_data, ('<broadcast>', discovery_port))
                
                # Ascolta risposte
                start_time = time.time()
                while time.time() - start_time < timeout:
                    try:
                        data, addr = sock.recvfrom(1024)
                        response = json.loads(data.decode())
                        
                        if (response.get("type") == "discovery_response" and 
                            response.get("node_id") != self.node_id):
                            
                            peer_id = response["node_id"]
                            peer_address = addr[0]
                            peer_port = response.get("port", 8888)
                            
                            if peer_id not in discovered_peers:
                                discovered_peers.append(peer_id)
                                
                                # Aggiungi peer se non esiste
                                if peer_id not in self.peers:
                                    peer = NetworkPeer(
                                        id=peer_id,
                                        address=peer_address,
                                        port=peer_port,
                                        capabilities=response.get("capabilities", [])
                                    )
                                    self.peers[peer_id] = peer
                    
                    except socket.timeout:
                        break
                    except Exception as e:
                        self.logger.debug(f"Errore ricezione discovery: {e}")
                        break
            
            finally:
                sock.close()
        
        except Exception as e:
            self.logger.error(f"Errore discovery peer: {e}")
        
        return discovered_peers
    
    async def get_connected_peers(self) -> List[str]:
        """Restituisce lista dei peer connessi"""
        connected = []
        
        for peer_id, connection in self.connections.items():
            if connection.status == ConnectionStatus.CONNECTED:
                connected.append(peer_id)
        
        return connected
    
    async def get_peer_info(self, peer_id: str) -> Optional[Dict[str, Any]]:
        """Restituisce informazioni su un peer"""
        if peer_id not in self.peers:
            return None
        
        peer = self.peers[peer_id]
        connection = self.connections.get(peer_id)
        
        info = asdict(peer)
        
        if connection:
            info.update({
                "connection_id": connection.id,
                "connection_status": connection.status.value,
                "bytes_sent": connection.bytes_sent,
                "bytes_received": connection.bytes_received,
                "messages_sent": connection.messages_sent,
                "messages_received": connection.messages_received,
                "connection_quality": connection.quality
            })
        
        return info
    
    async def get_network_stats(self) -> Dict[str, Any]:
        """Restituisce statistiche di rete"""
        # Aggiorna statistiche
        self.stats.total_peers = len(self.peers)
        self.stats.connected_peers = len([c for c in self.connections.values() 
                                         if c.status == ConnectionStatus.CONNECTED])
        self.stats.active_connections = self.stats.connected_peers
        
        # Calcola latenza media
        latencies = [c.latency for c in self.connections.values() 
                    if c.status == ConnectionStatus.CONNECTED and c.latency > 0]
        self.stats.average_latency = sum(latencies) / len(latencies) if latencies else 0.0
        
        # Calcola qualità rete
        qualities = [c.quality for c in self.connections.values() 
                    if c.status == ConnectionStatus.CONNECTED]
        self.stats.network_quality = sum(qualities) / len(qualities) if qualities else 1.0
        
        self.stats.last_updated = time.time()
        
        return asdict(self.stats)
    
    async def set_peer_handler(self, handler: Callable) -> None:
        """Imposta handler per eventi peer"""
        self.peer_handler = handler
    
    async def set_connection_handler(self, handler: Callable) -> None:
        """Imposta handler per eventi connessione"""
        self.connection_handler = handler
    
    async def set_message_handler(self, handler: Callable) -> None:
        """Imposta handler per messaggi ricevuti"""
        self.message_handler = handler
    
    async def update_config(self, new_config: Dict[str, Any]) -> None:
        """Aggiorna configurazione del modulo"""
        self.config.update(new_config)
        
        # Applica modifiche se necessario
        if "bootstrap_peers" in new_config:
            self.bootstrap_peers = new_config["bootstrap_peers"]
    
    # Metodi privati
    
    def _generate_node_id(self) -> str:
        """Genera ID univoco per il nodo"""
        hostname = socket.gethostname()
        timestamp = str(time.time())
        random_data = str(random.randint(1000, 9999))
        
        data = f"{hostname}_{timestamp}_{random_data}".encode()
        return hashlib.sha256(data).hexdigest()[:16]
    
    def _generate_message_id(self) -> str:
        """Genera ID univoco per un messaggio"""
        timestamp = str(time.time())
        random_data = str(random.randint(1000, 9999))
        
        data = f"{self.node_id}_{timestamp}_{random_data}".encode()
        return hashlib.sha256(data).hexdigest()[:12]
    
    async def _start_network_server(self) -> None:
        """Avvia server di rete principale"""
        host = self.config.get("listen_host", "0.0.0.0")
        port = self.config.get("listen_port", 8888)
        
        self.server = await asyncio.start_server(
            self._handle_incoming_connection,
            host,
            port
        )
        
        # Ottieni porta effettiva se era 0
        if port == 0:
            actual_port = self.server.sockets[0].getsockname()[1]
            self.config["listen_port"] = actual_port
        
        self.logger.info(f"Server di rete avviato su {host}:{self.config['listen_port']}")
    
    async def _start_discovery_server(self) -> None:
        """Avvia server di discovery UDP"""
        host = self.config.get("discovery_host", "0.0.0.0")
        port = self.config.get("discovery_port", 8889)
        
        # Crea socket UDP per discovery
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
        
        # Avvia task per gestire discovery
        asyncio.create_task(self._handle_discovery_requests(sock))
        
        self.logger.info(f"Server discovery avviato su {host}:{port}")
    
    async def _start_background_tasks(self) -> None:
        """Avvia task asincroni in background"""
        self.message_processor_task = asyncio.create_task(self._process_message_queue())
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self.discovery_task = asyncio.create_task(self._discovery_loop())
        self.maintenance_task = asyncio.create_task(self._maintenance_loop())
    
    async def _stop_background_tasks(self) -> None:
        """Ferma task asincroni in background"""
        tasks = [
            self.message_processor_task,
            self.heartbeat_task,
            self.discovery_task,
            self.maintenance_task
        ]
        
        for task in tasks:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
    
    async def _handle_incoming_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """Gestisce connessione in entrata"""
        remote_addr = writer.get_extra_info('peername')
        
        try:
            # Ricevi handshake
            handshake_data = await asyncio.wait_for(reader.read(1024), timeout=10.0)
            handshake = json.loads(handshake_data.decode())
            
            if handshake.get("type") != "handshake":
                writer.close()
                return
            
            peer_id = handshake["node_id"]
            
            # Crea peer e connessione
            peer = NetworkPeer(
                id=peer_id,
                address=remote_addr[0],
                port=handshake.get("port", remote_addr[1]),
                status=ConnectionStatus.CONNECTED,
                capabilities=handshake.get("capabilities", [])
            )
            
            connection = NetworkConnection(
                id=f"conn_{peer_id}_{int(time.time())}",
                peer_id=peer_id,
                local_address=writer.get_extra_info('sockname')[0],
                local_port=writer.get_extra_info('sockname')[1],
                remote_address=remote_addr[0],
                remote_port=remote_addr[1],
                status=ConnectionStatus.CONNECTED,
                reader=reader,
                writer=writer
            )
            
            # Salva peer e connessione
            self.peers[peer_id] = peer
            self.connections[peer_id] = connection
            
            # Invia risposta handshake
            await self._send_handshake_response(connection)
            
            # Gestisci connessione
            await self._handle_connection(connection)
            
        except Exception as e:
            self.logger.error(f"Errore gestione connessione da {remote_addr}: {e}")
            writer.close()
    
    async def _handle_connection(self, connection: NetworkConnection) -> None:
        """Gestisce una connessione attiva"""
        peer_id = connection.peer_id
        
        try:
            while self.running and connection.status == ConnectionStatus.CONNECTED:
                # Leggi messaggio
                try:
                    length_data = await asyncio.wait_for(
                        connection.reader.read(4), 
                        timeout=self.config.get("read_timeout", 30.0)
                    )
                    
                    if not length_data:
                        break
                    
                    message_length = struct.unpack('>I', length_data)[0]
                    
                    if message_length > self.config.get("max_message_size", 1024 * 1024):
                        self.logger.warning(f"Messaggio troppo grande da {peer_id}: {message_length}")
                        break
                    
                    message_data = await asyncio.wait_for(
                        connection.reader.read(message_length),
                        timeout=self.config.get("read_timeout", 30.0)
                    )
                    
                    if len(message_data) != message_length:
                        break
                    
                    # Processa messaggio
                    await self._process_received_message(connection, message_data)
                    
                    # Aggiorna statistiche
                    connection.bytes_received += len(message_data) + 4
                    connection.messages_received += 1
                    connection.last_activity = time.time()
                    
                except asyncio.TimeoutError:
                    # Timeout lettura - invia ping
                    await self._send_ping(connection)
                    continue
                
        except Exception as e:
            self.logger.error(f"Errore gestione connessione {peer_id}: {e}")
        
        finally:
            # Cleanup connessione
            await self.disconnect_from_peer(peer_id)
    
    async def _send_handshake(self, connection: NetworkConnection) -> None:
        """Invia handshake a un peer"""
        handshake = {
            "type": "handshake",
            "node_id": self.node_id,
            "port": self.config.get("listen_port", 8888),
            "version": "1.0.0",
            "capabilities": self.get_module_info()["capabilities"],
            "timestamp": time.time()
        }
        
        await self._send_raw_message(connection, json.dumps(handshake).encode())
    
    async def _send_handshake_response(self, connection: NetworkConnection) -> None:
        """Invia risposta handshake"""
        response = {
            "type": "handshake_response",
            "node_id": self.node_id,
            "status": "accepted",
            "timestamp": time.time()
        }
        
        await self._send_raw_message(connection, json.dumps(response).encode())
    
    async def _send_raw_message(self, connection: NetworkConnection, data: bytes) -> None:
        """Invia dati raw su una connessione"""
        if not connection.writer or connection.status != ConnectionStatus.CONNECTED:
            return
        
        try:
            # Invia lunghezza + dati
            length_data = struct.pack('>I', len(data))
            connection.writer.write(length_data + data)
            await connection.writer.drain()
            
            # Aggiorna statistiche
            connection.bytes_sent += len(data) + 4
            connection.messages_sent += 1
            connection.last_activity = time.time()
            
        except Exception as e:
            self.logger.error(f"Errore invio messaggio a {connection.peer_id}: {e}")
            await self.disconnect_from_peer(connection.peer_id)
    
    async def _process_received_message(self, connection: NetworkConnection, data: bytes) -> None:
        """Processa messaggio ricevuto"""
        try:
            message_dict = json.loads(data.decode())
            message_type = message_dict.get("type")
            
            if message_type == "ping":
                await self._handle_ping(connection, message_dict)
            elif message_type == "pong":
                await self._handle_pong(connection, message_dict)
            elif message_type == "network_message":
                await self._handle_network_message(connection, message_dict)
            elif message_type == "routing_update":
                await self._handle_routing_update(connection, message_dict)
            else:
                # Messaggio applicativo
                if self.message_handler:
                    await self.message_handler(connection.peer_id, message_type, data)
        
        except Exception as e:
            self.logger.error(f"Errore processamento messaggio da {connection.peer_id}: {e}")
    
    async def _process_message_queue(self) -> None:
        """Processa coda messaggi in uscita"""
        while self.running:
            try:
                # Prendi messaggio dalla coda
                message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                
                # Trova route per destinazione
                next_hop = self._find_route(message.destination_id)
                
                if next_hop and next_hop in self.connections:
                    connection = self.connections[next_hop]
                    
                    if connection.status == ConnectionStatus.CONNECTED:
                        # Prepara messaggio di rete
                        network_message = {
                            "type": "network_message",
                            "id": message.id,
                            "source_id": message.source_id,
                            "destination_id": message.destination_id,
                            "message_type": message.message_type,
                            "payload": message.payload.hex(),
                            "priority": message.priority.value,
                            "ttl": message.ttl,
                            "timestamp": message.timestamp,
                            "route": message.route + [self.node_id]
                        }
                        
                        await self._send_raw_message(connection, json.dumps(network_message).encode())
                        self.stats.total_messages_sent += 1
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Errore processamento coda messaggi: {e}")
    
    def _find_route(self, destination_id: str) -> Optional[str]:
        """Trova route per una destinazione"""
        # Connessione diretta
        if destination_id in self.connections:
            connection = self.connections[destination_id]
            if connection.status == ConnectionStatus.CONNECTED:
                return destination_id
        
        # Usa routing table
        if destination_id in self.routing_table:
            next_hop = self.routing_table[destination_id]
            if next_hop in self.connections:
                connection = self.connections[next_hop]
                if connection.status == ConnectionStatus.CONNECTED:
                    return next_hop
        
        # Fallback: usa peer con migliore qualità
        best_peer = None
        best_quality = 0.0
        
        for peer_id, connection in self.connections.items():
            if (connection.status == ConnectionStatus.CONNECTED and 
                connection.quality > best_quality):
                best_peer = peer_id
                best_quality = connection.quality
        
        return best_peer
    
    async def _handle_network_message(self, connection: NetworkConnection, message_dict: Dict[str, Any]) -> None:
        """Gestisce messaggio di rete"""
        destination_id = message_dict["destination_id"]
        
        # Se il messaggio è per noi
        if destination_id == self.node_id:
            if self.message_handler:
                payload = bytes.fromhex(message_dict["payload"])
                await self.message_handler(
                    message_dict["source_id"],
                    message_dict["message_type"],
                    payload
                )
            return
        
        # Altrimenti, inoltra il messaggio
        ttl = message_dict.get("ttl", 0) - 1
        if ttl <= 0:
            return  # TTL scaduto
        
        # Aggiorna TTL e route
        message_dict["ttl"] = ttl
        route = message_dict.get("route", [])
        
        # Evita loop
        if self.node_id in route:
            return
        
        # Trova next hop
        next_hop = self._find_route(destination_id)
        if next_hop and next_hop != connection.peer_id:  # Non rimandare al mittente
            next_connection = self.connections[next_hop]
            if next_connection.status == ConnectionStatus.CONNECTED:
                await self._send_raw_message(next_connection, json.dumps(message_dict).encode())
    
    async def _send_ping(self, connection: NetworkConnection) -> None:
        """Invia ping a un peer"""
        ping_message = {
            "type": "ping",
            "timestamp": time.time(),
            "node_id": self.node_id
        }
        
        await self._send_raw_message(connection, json.dumps(ping_message).encode())
    
    async def _handle_ping(self, connection: NetworkConnection, ping_dict: Dict[str, Any]) -> None:
        """Gestisce ping ricevuto"""
        pong_message = {
            "type": "pong",
            "timestamp": time.time(),
            "ping_timestamp": ping_dict["timestamp"],
            "node_id": self.node_id
        }
        
        await self._send_raw_message(connection, json.dumps(pong_message).encode())
    
    async def _handle_pong(self, connection: NetworkConnection, pong_dict: Dict[str, Any]) -> None:
        """Gestisce pong ricevuto"""
        ping_timestamp = pong_dict.get("ping_timestamp", 0)
        if ping_timestamp > 0:
            latency = time.time() - ping_timestamp
            connection.latency = latency
            
            # Aggiorna qualità connessione basata su latenza
            if latency < 0.1:
                connection.quality = 1.0
            elif latency < 0.5:
                connection.quality = 0.8
            elif latency < 1.0:
                connection.quality = 0.6
            else:
                connection.quality = 0.4
    
    async def _heartbeat_loop(self) -> None:
        """Loop heartbeat per mantenere connessioni"""
        while self.running:
            try:
                for connection in list(self.connections.values()):
                    if connection.status == ConnectionStatus.CONNECTED:
                        # Verifica timeout
                        if time.time() - connection.last_activity > self.config.get("heartbeat_timeout", 60.0):
                            await self.disconnect_from_peer(connection.peer_id)
                        else:
                            # Invia ping periodico
                            await self._send_ping(connection)
                
                await asyncio.sleep(self.config.get("heartbeat_interval", 30.0))
                
            except Exception as e:
                self.logger.error(f"Errore heartbeat loop: {e}")
                await asyncio.sleep(5.0)
    
    async def _discovery_loop(self) -> None:
        """Loop discovery automatico"""
        while self.running:
            try:
                # Discovery periodico
                if len(self.connections) < self.config.get("min_connections", 3):
                    await self.discover_peers()
                    
                    # Connetti a bootstrap peer se necessario
                    if len(self.connections) == 0 and self.bootstrap_peers:
                        for address, port in self.bootstrap_peers:
                            success = await self.connect_to_peer(address, port)
                            if success:
                                break
                
                await asyncio.sleep(self.config.get("discovery_interval", 60.0))
                
            except Exception as e:
                self.logger.error(f"Errore discovery loop: {e}")
                await asyncio.sleep(10.0)
    
    async def _maintenance_loop(self) -> None:
        """Loop manutenzione rete"""
        while self.running:
            try:
                # Pulizia peer obsoleti
                current_time = time.time()
                obsolete_peers = []
                
                for peer_id, peer in self.peers.items():
                    if (peer.status == ConnectionStatus.DISCONNECTED and 
                        current_time - peer.last_seen > self.config.get("peer_timeout", 3600.0)):
                        obsolete_peers.append(peer_id)
                
                for peer_id in obsolete_peers:
                    del self.peers[peer_id]
                    if peer_id in self.routing_table:
                        del self.routing_table[peer_id]
                
                # Aggiorna routing table
                await self._update_routing_table()
                
                await asyncio.sleep(self.config.get("maintenance_interval", 300.0))
                
            except Exception as e:
                self.logger.error(f"Errore maintenance loop: {e}")
                await asyncio.sleep(30.0)
    
    async def _handle_discovery_requests(self, sock: socket.socket) -> None:
        """Gestisce richieste discovery UDP"""
        while self.running:
            try:
                data, addr = sock.recvfrom(1024)
                request = json.loads(data.decode())
                
                if (request.get("type") == "discovery_request" and 
                    request.get("node_id") != self.node_id):
                    
                    # Invia risposta
                    response = {
                        "type": "discovery_response",
                        "node_id": self.node_id,
                        "port": self.config.get("listen_port", 8888),
                        "capabilities": self.get_module_info()["capabilities"],
                        "timestamp": time.time()
                    }
                    
                    sock.sendto(json.dumps(response).encode(), addr)
            
            except Exception as e:
                self.logger.debug(f"Errore gestione discovery: {e}")
                await asyncio.sleep(0.1)
    
    async def _update_routing_table(self) -> None:
        """Aggiorna routing table"""
        # Implementazione semplice: ogni peer è raggiungibile direttamente
        # In futuro si può implementare un algoritmo più sofisticato
        
        for peer_id in self.connections:
            connection = self.connections[peer_id]
            if connection.status == ConnectionStatus.CONNECTED:
                self.routing_table[peer_id] = peer_id
    
    def _update_routing_table_on_disconnect(self, peer_id: str) -> None:
        """Aggiorna routing table quando un peer si disconnette"""
        # Rimuovi route dirette
        if peer_id in self.routing_table:
            del self.routing_table[peer_id]
        
        # Rimuovi route che passano per questo peer
        to_remove = []
        for dest, next_hop in self.routing_table.items():
            if next_hop == peer_id:
                to_remove.append(dest)
        
        for dest in to_remove:
            del self.routing_table[dest]
    
    async def _close_all_connections(self) -> None:
        """Chiude tutte le connessioni"""
        for peer_id in list(self.connections.keys()):
            await self.disconnect_from_peer(peer_id)
    
    async def _load_persistent_data(self) -> None:
        """Carica dati persistenti"""
        try:
            data_dir = Path(self.config.get("data_dir", "data/network"))
            
            # Carica peer
            peers_file = data_dir / "peers.json"
            if peers_file.exists():
                with open(peers_file, 'r') as f:
                    peers_data = json.load(f)
                    
                for peer_data in peers_data:
                    peer = NetworkPeer(**peer_data)
                    peer.status = ConnectionStatus.DISCONNECTED  # Reset stato
                    self.peers[peer.id] = peer
        
        except Exception as e:
            self.logger.error(f"Errore caricamento dati persistenti: {e}")
    
    async def _save_persistent_data(self) -> None:
        """Salva dati persistenti"""
        try:
            data_dir = Path(self.config.get("data_dir", "data/network"))
            data_dir.mkdir(parents=True, exist_ok=True)
            
            # Salva peer (solo quelli affidabili)
            peers_file = data_dir / "peers.json"
            reliable_peers = []
            
            for peer in self.peers.values():
                if peer.reliability > 0.5:  # Solo peer affidabili
                    peer_data = asdict(peer)
                    # Rimuovi campi non serializzabili
                    peer_data["peer_type"] = peer_data["peer_type"].value
                    peer_data["status"] = peer_data["status"].value
                    reliable_peers.append(peer_data)
            
            with open(peers_file, 'w') as f:
                json.dump(reliable_peers, f, indent=2)
        
        except Exception as e:
            self.logger.error(f"Errore salvataggio dati persistenti: {e}")
    
    async def _notify_peer_event(self, peer_id: str, event: str) -> None:
        """Notifica evento peer"""
        if self.peer_handler:
            try:
                await self.peer_handler(peer_id, event)
            except Exception as e:
                self.logger.error(f"Errore notifica evento peer: {e}")
    
    async def _handle_routing_update(self, connection: NetworkConnection, message_dict: Dict[str, Any]) -> None:
        """Gestisce aggiornamento routing"""
        # Implementazione futura per protocolli di routing avanzati
        pass


# Configurazione predefinita
DEFAULT_CONFIG = {
    "listen_host": "0.0.0.0",
    "listen_port": 8888,
    "discovery_host": "0.0.0.0", 
    "discovery_port": 8889,
    "data_dir": "data/network",
    "bootstrap_peers": [],
    "enable_discovery": True,
    "min_connections": 3,
    "max_connections": 50,
    "connection_timeout": 10.0,
    "read_timeout": 30.0,
    "heartbeat_interval": 30.0,
    "heartbeat_timeout": 60.0,
    "discovery_interval": 60.0,
    "maintenance_interval": 300.0,
    "max_message_size": 1024 * 1024,  # 1MB
    "peer_timeout": 3600.0,  # 1 ora
    "auto_connect": True,
    "enable_routing": True,
    "enable_load_balancing": True
}


async def create_basic_network_module(config: Dict[str, Any] = None) -> BasicNetworkModule:
    """
    Factory function per creare BasicNetworkModule
    
    Args:
        config: Configurazione del modulo (usa DEFAULT_CONFIG se None)
    
    Returns:
        Istanza inizializzata di BasicNetworkModule
    """
    if config is None:
        config = DEFAULT_CONFIG.copy()
    else:
        # Merge con configurazione predefinita
        merged_config = DEFAULT_CONFIG.copy()
        merged_config.update(config)
        config = merged_config
    
    module = BasicNetworkModule()
    await module.initialize(config)
    return module