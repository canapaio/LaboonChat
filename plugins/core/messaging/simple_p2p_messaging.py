"""
Simple P2P Messaging Module for LaboonChat v2.0

This module provides a basic peer-to-peer messaging implementation
with support for direct connections, message history, and file transfers.
"""

import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Callable, Any, AsyncGenerator, Tuple
from dataclasses import dataclass, asdict
from threading import Lock
import logging

from laboon_chat2.interfaces import IMessagingModule
from laboon_chat2.interfaces.messaging_interface import (
    MessagingError, ConnectionError, MessageError, 
    FileTransferError, SynchronizationError
)


@dataclass
class P2PMessage:
    """Rappresenta un messaggio P2P"""
    id: str
    sender_id: str
    recipient_id: str
    content: str
    timestamp: float
    message_type: str = "text"
    metadata: Optional[Dict[str, Any]] = None
    encrypted: bool = False
    signature: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte il messaggio in dizionario"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'P2PMessage':
        """Crea un messaggio da dizionario"""
        return cls(**data)


@dataclass
class P2PPeer:
    """Rappresenta un peer nella rete P2P"""
    peer_id: str
    address: str
    port: int
    last_seen: float
    status: str = "online"
    capabilities: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte il peer in dizionario"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'P2PPeer':
        """Crea un peer da dizionario"""
        return cls(**data)


@dataclass
class FileTransfer:
    """Rappresenta un trasferimento file"""
    transfer_id: str
    sender_id: str
    recipient_id: str
    filename: str
    file_size: int
    file_hash: str
    status: str = "pending"  # pending, active, completed, failed, cancelled
    progress: float = 0.0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte il trasferimento in dizionario"""
        return asdict(self)


class SimpleP2PMessaging(IMessagingModule):
    """
    Implementazione semplice di un modulo di messaggistica P2P.
    
    Fornisce funzionalità di base per:
    - Connessioni dirette peer-to-peer
    - Invio e ricezione messaggi
    - Cronologia messaggi
    - Trasferimento file
    - Sincronizzazione messaggi
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Inizializza il modulo di messaggistica P2P"""
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.SimpleP2PMessaging")
        
        # Stato del modulo
        self._initialized = False
        self._running = False
        self._lock = Lock()
        
        # Configurazione
        self._listen_port = self.config.get("listen_port", 8888)
        self._max_connections = self.config.get("max_connections", 50)
        self._message_history_limit = self.config.get("message_history_limit", 1000)
        self._file_transfer_chunk_size = self.config.get("file_transfer_chunk_size", 8192)
        self._connection_timeout = self.config.get("connection_timeout", 30.0)
        
        # Storage
        self._data_dir = Path(self.config.get("data_dir", "data/messaging"))
        self._data_dir.mkdir(parents=True, exist_ok=True)
        
        # Stato interno
        self._peer_id = self.config.get("peer_id", str(uuid.uuid4()))
        self._connections: Dict[str, Any] = {}  # peer_id -> connection
        self._peers: Dict[str, P2PPeer] = {}
        self._message_history: List[P2PMessage] = []
        self._file_transfers: Dict[str, FileTransfer] = {}
        
        # Event handlers
        self._message_handlers: List[Callable] = []
        self._connection_handlers: List[Callable] = []
        self._file_transfer_handlers: List[Callable] = []
        
        # Server
        self._server = None
        self._server_task = None
        
        self.logger.info(f"SimpleP2PMessaging inizializzato con peer_id: {self._peer_id}")
    
    async def initialize(self) -> None:
        """Inizializza il modulo di messaggistica"""
        if self._initialized:
            return
        
        try:
            # Carica dati persistenti
            await self._load_persistent_data()
            
            # Avvia server
            await self._start_server()
            
            self._initialized = True
            self._running = True
            self.logger.info("SimpleP2PMessaging inizializzato con successo")
            
        except Exception as e:
            self.logger.error(f"Errore durante l'inizializzazione: {e}")
            raise MessagingError(f"Inizializzazione fallita: {e}")
    
    async def cleanup(self) -> None:
        """Pulisce le risorse del modulo"""
        if not self._initialized:
            return
        
        try:
            self._running = False
            
            # Chiudi tutte le connessioni
            await self._close_all_connections()
            
            # Ferma il server
            await self._stop_server()
            
            # Salva dati persistenti
            await self._save_persistent_data()
            
            self._initialized = False
            self.logger.info("SimpleP2PMessaging terminato con successo")
            
        except Exception as e:
            self.logger.error(f"Errore durante la pulizia: {e}")
            raise MessagingError(f"Pulizia fallita: {e}")
    
    def get_module_info(self) -> Dict[str, Any]:
        """Restituisce informazioni sul modulo"""
        return {
            "name": "SimpleP2PMessaging",
            "version": "1.0.0",
            "description": "Modulo di messaggistica P2P semplice",
            "author": "LaboonChat Team",
            "capabilities": [
                "direct_messaging",
                "file_transfer", 
                "message_history",
                "peer_discovery",
                "message_sync"
            ],
            "config_schema": {
                "listen_port": {"type": "integer", "default": 8888},
                "max_connections": {"type": "integer", "default": 50},
                "message_history_limit": {"type": "integer", "default": 1000},
                "file_transfer_chunk_size": {"type": "integer", "default": 8192},
                "connection_timeout": {"type": "number", "default": 30.0},
                "data_dir": {"type": "string", "default": "data/messaging"}
            }
        }
    
    # Gestione connessioni
    async def connect_to_peer(self, peer_address: str, peer_port: int, 
                            timeout: Optional[float] = None) -> str:
        """Connette a un peer"""
        if not self._running:
            raise ConnectionError("Modulo non in esecuzione")
        
        timeout = timeout or self._connection_timeout
        
        try:
            # Simula connessione (in implementazione reale userebbe socket/websocket)
            peer_id = f"peer_{peer_address}_{peer_port}"
            
            # Verifica se già connesso
            if peer_id in self._connections:
                return peer_id
            
            # Crea connessione simulata
            connection = {
                "peer_id": peer_id,
                "address": peer_address,
                "port": peer_port,
                "connected_at": time.time(),
                "status": "connected"
            }
            
            self._connections[peer_id] = connection
            
            # Aggiungi peer
            peer = P2PPeer(
                peer_id=peer_id,
                address=peer_address,
                port=peer_port,
                last_seen=time.time(),
                status="online"
            )
            self._peers[peer_id] = peer
            
            # Notifica handlers
            await self._notify_connection_handlers("connected", peer_id)
            
            self.logger.info(f"Connesso al peer {peer_id}")
            return peer_id
            
        except Exception as e:
            self.logger.error(f"Errore connessione a {peer_address}:{peer_port}: {e}")
            raise ConnectionError(f"Connessione fallita: {e}")
    
    async def disconnect_from_peer(self, peer_id: str) -> None:
        """Disconnette da un peer"""
        if peer_id not in self._connections:
            raise ConnectionError(f"Peer {peer_id} non connesso")
        
        try:
            # Rimuovi connessione
            del self._connections[peer_id]
            
            # Aggiorna stato peer
            if peer_id in self._peers:
                self._peers[peer_id].status = "offline"
                self._peers[peer_id].last_seen = time.time()
            
            # Notifica handlers
            await self._notify_connection_handlers("disconnected", peer_id)
            
            self.logger.info(f"Disconnesso dal peer {peer_id}")
            
        except Exception as e:
            self.logger.error(f"Errore disconnessione da {peer_id}: {e}")
            raise ConnectionError(f"Disconnessione fallita: {e}")
    
    def get_connected_peers(self) -> List[str]:
        """Restituisce la lista dei peer connessi"""
        return list(self._connections.keys())
    
    def is_connected_to_peer(self, peer_id: str) -> bool:
        """Verifica se connesso a un peer"""
        return peer_id in self._connections
    
    # Scoperta peer
    async def discover_peers(self, timeout: Optional[float] = None) -> List[Dict[str, Any]]:
        """Scopre peer nella rete locale"""
        timeout = timeout or 10.0
        
        try:
            # Simula scoperta peer (in implementazione reale userebbe broadcast/multicast)
            discovered_peers = []
            
            # Aggiungi peer simulati per test
            for i in range(3):
                peer_info = {
                    "peer_id": f"discovered_peer_{i}",
                    "address": f"192.168.1.{100 + i}",
                    "port": 8888 + i,
                    "capabilities": ["messaging", "file_transfer"],
                    "last_seen": time.time()
                }
                discovered_peers.append(peer_info)
            
            self.logger.info(f"Scoperti {len(discovered_peers)} peer")
            return discovered_peers
            
        except Exception as e:
            self.logger.error(f"Errore scoperta peer: {e}")
            raise MessagingError(f"Scoperta peer fallita: {e}")
    
    def get_peer_info(self, peer_id: str) -> Optional[Dict[str, Any]]:
        """Restituisce informazioni su un peer"""
        if peer_id in self._peers:
            return self._peers[peer_id].to_dict()
        return None
    
    def get_all_peers(self) -> List[Dict[str, Any]]:
        """Restituisce tutti i peer conosciuti"""
        return [peer.to_dict() for peer in self._peers.values()]
    
    # Gestione messaggi
    async def send_message(self, recipient_id: str, content: str, 
                          message_type: str = "text", 
                          metadata: Optional[Dict[str, Any]] = None) -> str:
        """Invia un messaggio a un peer"""
        if not self._running:
            raise MessageError("Modulo non in esecuzione")
        
        if recipient_id not in self._connections:
            raise MessageError(f"Peer {recipient_id} non connesso")
        
        try:
            # Crea messaggio
            message = P2PMessage(
                id=str(uuid.uuid4()),
                sender_id=self._peer_id,
                recipient_id=recipient_id,
                content=content,
                timestamp=time.time(),
                message_type=message_type,
                metadata=metadata or {}
            )
            
            # Simula invio (in implementazione reale invierebbe via rete)
            await asyncio.sleep(0.1)  # Simula latenza rete
            
            # Aggiungi alla cronologia
            self._add_message_to_history(message)
            
            # Notifica handlers
            await self._notify_message_handlers("sent", message)
            
            self.logger.debug(f"Messaggio inviato a {recipient_id}: {message.id}")
            return message.id
            
        except Exception as e:
            self.logger.error(f"Errore invio messaggio a {recipient_id}: {e}")
            raise MessageError(f"Invio messaggio fallito: {e}")
    
    async def receive_messages(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Generatore asincrono per ricevere messaggi"""
        if not self._running:
            raise MessageError("Modulo non in esecuzione")
        
        try:
            while self._running:
                # Simula ricezione messaggi (in implementazione reale riceverebbe dalla rete)
                await asyncio.sleep(1.0)
                
                # Simula messaggio ricevuto occasionalmente
                if len(self._connections) > 0 and time.time() % 10 < 1:
                    peer_id = list(self._connections.keys())[0]
                    message = P2PMessage(
                        id=str(uuid.uuid4()),
                        sender_id=peer_id,
                        recipient_id=self._peer_id,
                        content=f"Messaggio simulato da {peer_id}",
                        timestamp=time.time(),
                        message_type="text"
                    )
                    
                    self._add_message_to_history(message)
                    await self._notify_message_handlers("received", message)
                    
                    yield message.to_dict()
                    
        except Exception as e:
            self.logger.error(f"Errore ricezione messaggi: {e}")
            raise MessageError(f"Ricezione messaggi fallita: {e}")
    
    def get_message_history(self, peer_id: Optional[str] = None, 
                          limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Restituisce la cronologia messaggi"""
        messages = self._message_history
        
        # Filtra per peer se specificato
        if peer_id:
            messages = [
                msg for msg in messages 
                if msg.sender_id == peer_id or msg.recipient_id == peer_id
            ]
        
        # Applica limite
        if limit:
            messages = messages[-limit:]
        
        return [msg.to_dict() for msg in messages]
    
    def clear_message_history(self, peer_id: Optional[str] = None) -> None:
        """Cancella la cronologia messaggi"""
        if peer_id:
            self._message_history = [
                msg for msg in self._message_history
                if msg.sender_id != peer_id and msg.recipient_id != peer_id
            ]
        else:
            self._message_history.clear()
        
        self.logger.info(f"Cronologia messaggi cancellata per peer: {peer_id or 'tutti'}")
    
    # Event handlers
    def set_message_handler(self, handler: Callable) -> None:
        """Imposta handler per messaggi"""
        if handler not in self._message_handlers:
            self._message_handlers.append(handler)
    
    def set_connection_handler(self, handler: Callable) -> None:
        """Imposta handler per connessioni"""
        if handler not in self._connection_handlers:
            self._connection_handlers.append(handler)
    
    def set_file_transfer_handler(self, handler: Callable) -> None:
        """Imposta handler per trasferimenti file"""
        if handler not in self._file_transfer_handlers:
            self._file_transfer_handlers.append(handler)
    
    # Trasferimento file
    async def send_file(self, recipient_id: str, file_path: str, 
                       metadata: Optional[Dict[str, Any]] = None) -> str:
        """Invia un file a un peer"""
        if not self._running:
            raise FileTransferError("Modulo non in esecuzione")
        
        if recipient_id not in self._connections:
            raise FileTransferError(f"Peer {recipient_id} non connesso")
        
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise FileTransferError(f"File non trovato: {file_path}")
        
        try:
            # Crea trasferimento
            transfer = FileTransfer(
                transfer_id=str(uuid.uuid4()),
                sender_id=self._peer_id,
                recipient_id=recipient_id,
                filename=file_path_obj.name,
                file_size=file_path_obj.stat().st_size,
                file_hash="simulated_hash",  # In implementazione reale calcolerebbe hash
                status="active",
                start_time=time.time()
            )
            
            self._file_transfers[transfer.transfer_id] = transfer
            
            # Simula trasferimento
            total_chunks = transfer.file_size // self._file_transfer_chunk_size + 1
            for chunk in range(total_chunks):
                if not self._running:
                    transfer.status = "cancelled"
                    break
                
                await asyncio.sleep(0.1)  # Simula tempo trasferimento
                transfer.progress = min(1.0, (chunk + 1) / total_chunks)
                
                # Notifica progresso
                await self._notify_file_transfer_handlers("progress", transfer)
            
            if transfer.status != "cancelled":
                transfer.status = "completed"
                transfer.end_time = time.time()
            
            await self._notify_file_transfer_handlers("completed", transfer)
            
            self.logger.info(f"Trasferimento file completato: {transfer.transfer_id}")
            return transfer.transfer_id
            
        except Exception as e:
            self.logger.error(f"Errore trasferimento file: {e}")
            raise FileTransferError(f"Trasferimento file fallito: {e}")
    
    async def receive_file(self, transfer_id: str, save_path: str) -> None:
        """Riceve un file"""
        if transfer_id not in self._file_transfers:
            raise FileTransferError(f"Trasferimento {transfer_id} non trovato")
        
        transfer = self._file_transfers[transfer_id]
        
        try:
            # Simula ricezione file
            save_path_obj = Path(save_path)
            save_path_obj.parent.mkdir(parents=True, exist_ok=True)
            
            # Crea file simulato
            with open(save_path_obj, 'w') as f:
                f.write(f"File simulato ricevuto da {transfer.sender_id}")
            
            transfer.status = "completed"
            transfer.end_time = time.time()
            
            await self._notify_file_transfer_handlers("received", transfer)
            
            self.logger.info(f"File ricevuto: {save_path}")
            
        except Exception as e:
            transfer.status = "failed"
            transfer.error_message = str(e)
            self.logger.error(f"Errore ricezione file: {e}")
            raise FileTransferError(f"Ricezione file fallita: {e}")
    
    def get_file_transfers(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Restituisce i trasferimenti file"""
        transfers = list(self._file_transfers.values())
        
        if status:
            transfers = [t for t in transfers if t.status == status]
        
        return [t.to_dict() for t in transfers]
    
    async def cancel_file_transfer(self, transfer_id: str) -> None:
        """Cancella un trasferimento file"""
        if transfer_id not in self._file_transfers:
            raise FileTransferError(f"Trasferimento {transfer_id} non trovato")
        
        transfer = self._file_transfers[transfer_id]
        transfer.status = "cancelled"
        transfer.end_time = time.time()
        
        await self._notify_file_transfer_handlers("cancelled", transfer)
        
        self.logger.info(f"Trasferimento file cancellato: {transfer_id}")
    
    # Sincronizzazione messaggi
    async def sync_messages_with_peer(self, peer_id: str, 
                                    since_timestamp: Optional[float] = None) -> int:
        """Sincronizza messaggi con un peer"""
        if not self._running:
            raise SynchronizationError("Modulo non in esecuzione")
        
        if peer_id not in self._connections:
            raise SynchronizationError(f"Peer {peer_id} non connesso")
        
        try:
            since_timestamp = since_timestamp or (time.time() - 86400)  # Ultimo giorno
            
            # Simula sincronizzazione
            await asyncio.sleep(0.5)
            
            # Simula messaggi sincronizzati
            synced_count = 0
            for i in range(3):  # Simula 3 messaggi sincronizzati
                message = P2PMessage(
                    id=str(uuid.uuid4()),
                    sender_id=peer_id,
                    recipient_id=self._peer_id,
                    content=f"Messaggio sincronizzato {i}",
                    timestamp=since_timestamp + i * 100,
                    message_type="text"
                )
                
                self._add_message_to_history(message)
                synced_count += 1
            
            self.logger.info(f"Sincronizzati {synced_count} messaggi con {peer_id}")
            return synced_count
            
        except Exception as e:
            self.logger.error(f"Errore sincronizzazione con {peer_id}: {e}")
            raise SynchronizationError(f"Sincronizzazione fallita: {e}")
    
    def get_sync_status(self, peer_id: str) -> Dict[str, Any]:
        """Restituisce lo stato di sincronizzazione con un peer"""
        if peer_id not in self._peers:
            return {"status": "unknown", "last_sync": None}
        
        peer = self._peers[peer_id]
        return {
            "status": "synced" if peer.status == "online" else "out_of_sync",
            "last_sync": peer.last_seen,
            "peer_status": peer.status
        }
    
    # Configurazione
    def update_config(self, config: Dict[str, Any]) -> None:
        """Aggiorna la configurazione del modulo"""
        self.config.update(config)
        
        # Aggiorna parametri configurabili
        self._listen_port = self.config.get("listen_port", self._listen_port)
        self._max_connections = self.config.get("max_connections", self._max_connections)
        self._message_history_limit = self.config.get("message_history_limit", self._message_history_limit)
        self._file_transfer_chunk_size = self.config.get("file_transfer_chunk_size", self._file_transfer_chunk_size)
        self._connection_timeout = self.config.get("connection_timeout", self._connection_timeout)
        
        self.logger.info("Configurazione aggiornata")
    
    # Metodi privati
    async def _start_server(self) -> None:
        """Avvia il server per connessioni in entrata"""
        try:
            # Simula avvio server (in implementazione reale userebbe asyncio.start_server)
            self._server = {"port": self._listen_port, "status": "running"}
            self.logger.info(f"Server avviato sulla porta {self._listen_port}")
            
        except Exception as e:
            self.logger.error(f"Errore avvio server: {e}")
            raise
    
    async def _stop_server(self) -> None:
        """Ferma il server"""
        if self._server:
            self._server["status"] = "stopped"
            self._server = None
            self.logger.info("Server fermato")
    
    async def _close_all_connections(self) -> None:
        """Chiude tutte le connessioni"""
        for peer_id in list(self._connections.keys()):
            await self.disconnect_from_peer(peer_id)
    
    def _add_message_to_history(self, message: P2PMessage) -> None:
        """Aggiunge un messaggio alla cronologia"""
        self._message_history.append(message)
        
        # Mantieni limite cronologia
        if len(self._message_history) > self._message_history_limit:
            self._message_history = self._message_history[-self._message_history_limit:]
    
    async def _notify_message_handlers(self, event_type: str, message: P2PMessage) -> None:
        """Notifica gli handler dei messaggi"""
        for handler in self._message_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_type, message.to_dict())
                else:
                    handler(event_type, message.to_dict())
            except Exception as e:
                self.logger.error(f"Errore handler messaggio: {e}")
    
    async def _notify_connection_handlers(self, event_type: str, peer_id: str) -> None:
        """Notifica gli handler delle connessioni"""
        for handler in self._connection_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_type, peer_id)
                else:
                    handler(event_type, peer_id)
            except Exception as e:
                self.logger.error(f"Errore handler connessione: {e}")
    
    async def _notify_file_transfer_handlers(self, event_type: str, transfer: FileTransfer) -> None:
        """Notifica gli handler dei trasferimenti file"""
        for handler in self._file_transfer_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_type, transfer.to_dict())
                else:
                    handler(event_type, transfer.to_dict())
            except Exception as e:
                self.logger.error(f"Errore handler trasferimento file: {e}")
    
    async def _load_persistent_data(self) -> None:
        """Carica dati persistenti"""
        try:
            # Carica peer
            peers_file = self._data_dir / "peers.json"
            if peers_file.exists():
                with open(peers_file, 'r') as f:
                    peers_data = json.load(f)
                    self._peers = {
                        peer_id: P2PPeer.from_dict(data)
                        for peer_id, data in peers_data.items()
                    }
            
            # Carica cronologia messaggi
            history_file = self._data_dir / "message_history.json"
            if history_file.exists():
                with open(history_file, 'r') as f:
                    history_data = json.load(f)
                    self._message_history = [
                        P2PMessage.from_dict(data) for data in history_data
                    ]
            
            self.logger.info("Dati persistenti caricati")
            
        except Exception as e:
            self.logger.warning(f"Errore caricamento dati persistenti: {e}")
    
    async def _save_persistent_data(self) -> None:
        """Salva dati persistenti"""
        try:
            # Salva peer
            peers_file = self._data_dir / "peers.json"
            with open(peers_file, 'w') as f:
                peers_data = {
                    peer_id: peer.to_dict()
                    for peer_id, peer in self._peers.items()
                }
                json.dump(peers_data, f, indent=2)
            
            # Salva cronologia messaggi (solo gli ultimi)
            history_file = self._data_dir / "message_history.json"
            with open(history_file, 'w') as f:
                recent_messages = self._message_history[-self._message_history_limit:]
                history_data = [msg.to_dict() for msg in recent_messages]
                json.dump(history_data, f, indent=2)
            
            self.logger.info("Dati persistenti salvati")
            
        except Exception as e:
            self.logger.error(f"Errore salvataggio dati persistenti: {e}")


def create_simple_p2p_messaging(config: Optional[Dict[str, Any]] = None) -> SimpleP2PMessaging:
    """
    Factory function per creare un'istanza di SimpleP2PMessaging.
    
    Args:
        config: Configurazione opzionale per il modulo
        
    Returns:
        Istanza di SimpleP2PMessaging configurata
    """
    return SimpleP2PMessaging(config)


# Configurazione di default per il modulo
DEFAULT_CONFIG = {
    "listen_port": 8888,
    "max_connections": 50,
    "message_history_limit": 1000,
    "file_transfer_chunk_size": 8192,
    "connection_timeout": 30.0,
    "data_dir": "data/messaging"
}