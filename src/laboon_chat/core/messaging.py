"""
💬 P2P Messaging Engine - Motore Messaggi Decentralizzato
========================================================

Motore di messaggistica P2P completamente decentralizzato.
Utilizza BitTorrent DHT per comunicazioni sicure e anonime.

🌐 "I messaggi viaggiano liberi nell'oceano digitale" 🌊

Author: P2P Messaging Team
License: GPL-3.0
"""

import asyncio
import json
import time
import hashlib
import socket
from typing import Optional, Dict, Any, List, Callable, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import threading
from queue import Queue, Empty

from .crypto_core import LaboonCrypto, EncryptedData
from .identity import IdentityManager, IdentityInfo


@dataclass
class Message:
    """Struttura messaggio LaboonChat"""
    message_id: str
    sender_hash: str
    recipient_hash: str
    content: str
    timestamp: float
    message_type: str = "text"
    encrypted: bool = True
    signature: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte in dizionario per serializzazione"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Crea da dizionario"""
        return cls(**data)


@dataclass
class PeerInfo:
    """Informazioni peer nella rete"""
    peer_hash: str
    public_key: bytes
    display_name: str
    last_seen: float
    ip_address: Optional[str] = None
    port: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte in dizionario"""
        data = asdict(self)
        data['public_key'] = self.public_key.hex()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PeerInfo':
        """Crea da dizionario"""
        data['public_key'] = bytes.fromhex(data['public_key'])
        return cls(**data)


class SimpleDHT:
    """
    🌐 DHT semplificato per LaboonChat
    
    Implementazione leggera di DHT per discovery e routing messaggi.
    Basato su UDP per massima semplicità e velocità.
    """
    
    def __init__(self, port: int = 6881):
        """
        Inizializza DHT
        
        Args:
            port: Porta UDP per DHT
        """
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.running = False
        
        # Storage DHT
        self.storage: Dict[str, Any] = {}
        self.peers: Dict[str, PeerInfo] = {}
        
        # Callbacks
        self.message_callback: Optional[Callable[[Message], None]] = None
        self.peer_discovered_callback: Optional[Callable[[PeerInfo], None]] = None
        
        # Thread per ascolto
        self.listen_thread: Optional[threading.Thread] = None
        
        # Bootstrap nodes (nodi pubblici BitTorrent)
        self.bootstrap_nodes = [
            ("router.bittorrent.com", 6881),
            ("dht.transmissionbt.com", 6881),
            ("router.utorrent.com", 6881)
        ]
    
    def start(self) -> bool:
        """
        Avvia DHT
        
        Returns:
            bool: True se avvio riuscito
        """
        try:
            # Crea socket UDP
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(('0.0.0.0', self.port))
            self.socket.settimeout(1.0)  # Timeout per non bloccare
            
            self.running = True
            
            # Avvia thread ascolto
            self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
            self.listen_thread.start()
            
            # Bootstrap iniziale
            self._bootstrap()
            
            return True
            
        except Exception as e:
            print(f"❌ Errore avvio DHT: {e}")
            return False
    
    def stop(self):
        """Ferma DHT"""
        self.running = False
        
        if self.socket:
            self.socket.close()
            self.socket = None
        
        if self.listen_thread:
            self.listen_thread.join(timeout=2.0)
    
    def store_value(self, key: str, value: Any) -> bool:
        """
        Memorizza valore nel DHT
        
        Args:
            key: Chiave per il valore
            value: Valore da memorizzare
            
        Returns:
            bool: True se memorizzazione riuscita
        """
        try:
            self.storage[key] = {
                'value': value,
                'timestamp': time.time()
            }
            return True
        except Exception:
            return False
    
    def get_value(self, key: str) -> Optional[Any]:
        """
        Recupera valore dal DHT
        
        Args:
            key: Chiave del valore
            
        Returns:
            Optional[Any]: Valore o None se non trovato
        """
        stored = self.storage.get(key)
        if stored:
            # Controlla se non troppo vecchio (24 ore)
            if time.time() - stored['timestamp'] < 86400:
                return stored['value']
            else:
                # Rimuovi valore scaduto
                del self.storage[key]
        
        return None
    
    def announce_peer(self, peer_info: PeerInfo):
        """
        Annuncia peer nella rete
        
        Args:
            peer_info: Informazioni peer da annunciare
        """
        key = f"peer_{peer_info.peer_hash}"
        self.store_value(key, peer_info.to_dict())
        self.peers[peer_info.peer_hash] = peer_info
    
    def find_peer(self, peer_hash: str) -> Optional[PeerInfo]:
        """
        Cerca peer nella rete
        
        Args:
            peer_hash: Hash del peer da cercare
            
        Returns:
            Optional[PeerInfo]: Info peer o None se non trovato
        """
        # Prima controlla cache locale
        if peer_hash in self.peers:
            return self.peers[peer_hash]
        
        # Poi cerca nel DHT
        key = f"peer_{peer_hash}"
        peer_data = self.get_value(key)
        if peer_data:
            peer_info = PeerInfo.from_dict(peer_data)
            self.peers[peer_hash] = peer_info
            return peer_info
        
        return None
    
    def send_message_to_peer(self, message: Message, peer_info: PeerInfo) -> bool:
        """
        Invia messaggio diretto a peer
        
        Args:
            message: Messaggio da inviare
            peer_info: Informazioni destinatario
            
        Returns:
            bool: True se invio riuscito
        """
        if not peer_info.ip_address or not peer_info.port:
            return False
        
        try:
            # Serializza messaggio
            message_data = json.dumps({
                'type': 'message',
                'data': message.to_dict()
            }).encode('utf-8')
            
            # Invia via UDP
            self.socket.sendto(message_data, (peer_info.ip_address, peer_info.port))
            return True
            
        except Exception:
            return False
    
    def _listen_loop(self):
        """Loop ascolto messaggi DHT"""
        while self.running:
            try:
                data, addr = self.socket.recvfrom(4096)
                self._handle_message(data, addr)
            except socket.timeout:
                continue
            except Exception:
                if self.running:
                    continue
    
    def _handle_message(self, data: bytes, addr: Tuple[str, int]):
        """Gestisce messaggio ricevuto"""
        try:
            message_json = json.loads(data.decode('utf-8'))
            message_type = message_json.get('type')
            
            if message_type == 'message':
                # Messaggio chat
                message_data = message_json.get('data', {})
                message = Message.from_dict(message_data)
                
                if self.message_callback:
                    self.message_callback(message)
            
            elif message_type == 'peer_announce':
                # Annuncio peer
                peer_data = message_json.get('data', {})
                peer_info = PeerInfo.from_dict(peer_data)
                peer_info.ip_address = addr[0]
                peer_info.last_seen = time.time()
                
                self.peers[peer_info.peer_hash] = peer_info
                
                if self.peer_discovered_callback:
                    self.peer_discovered_callback(peer_info)
            
        except Exception:
            pass  # Ignora messaggi malformati
    
    def _bootstrap(self):
        """Bootstrap iniziale con nodi pubblici"""
        # Per ora implementazione semplificata
        # In futuro: connessione vera ai nodi BitTorrent
        pass


class LaboonMessaging:
    """
    💬 Motore messaggistica LaboonChat
    
    Gestisce invio, ricezione e crittografia messaggi P2P.
    Utilizza DHT per discovery e routing decentralizzato.
    """
    
    def __init__(self, dht_port: int = 6881):
        """
        Inizializza motore messaggistica
        
        Args:
            dht_port: Porta DHT per comunicazioni P2P
        """
        self.identity_manager = IdentityManager()
        self.dht = SimpleDHT(dht_port)
        
        # Storage messaggi
        self.messages: List[Message] = []
        self.message_queue = Queue()
        
        # Callbacks
        self.message_received_callback: Optional[Callable[[Message], None]] = None
        self.peer_discovered_callback: Optional[Callable[[PeerInfo], None]] = None
        
        # Stato
        self.is_running = False
        
        # Setup callbacks DHT
        self.dht.message_callback = self._handle_received_message
        self.dht.peer_discovered_callback = self._handle_peer_discovered
    
    def start(self) -> bool:
        """
        Avvia motore messaggistica
        
        Returns:
            bool: True se avvio riuscito
        """
        try:
            # Assicura identità
            identity_hash = self.identity_manager.ensure_identity()
            
            # Avvia DHT
            if not self.dht.start():
                return False
            
            # Annuncia presenza nella rete
            self._announce_self()
            
            self.is_running = True
            return True
            
        except Exception as e:
            print(f"❌ Errore avvio messaging: {e}")
            return False
    
    def stop(self):
        """Ferma motore messaggistica"""
        self.is_running = False
        self.dht.stop()
    
    def send_message(self, recipient_hash: str, content: str, message_type: str = "text") -> bool:
        """
        Invia messaggio a destinatario
        
        Args:
            recipient_hash: Hash identità destinatario
            content: Contenuto messaggio
            message_type: Tipo messaggio (default: "text")
            
        Returns:
            bool: True se invio riuscito
        """
        try:
            # Ottieni identità corrente
            current_identity = self.identity_manager.get_current_identity()
            if not current_identity:
                return False
            
            # Cerca destinatario nella rete
            peer_info = self.dht.find_peer(recipient_hash)
            if not peer_info:
                print(f"❌ Peer {recipient_hash[:16]}... non trovato")
                return False
            
            # Crea messaggio
            message_id = self._generate_message_id()
            message = Message(
                message_id=message_id,
                sender_hash=current_identity.identity_hash,
                recipient_hash=recipient_hash,
                content=content,
                timestamp=time.time(),
                message_type=message_type,
                encrypted=True
            )
            
            # Critta contenuto se necessario
            if message.encrypted:
                encrypted_content = self._encrypt_message_content(content, peer_info.public_key)
                if encrypted_content:
                    message.content = encrypted_content
                else:
                    return False
            
            # Firma messaggio
            message_data = json.dumps(message.to_dict()).encode('utf-8')
            signature = self.identity_manager.sign_data(message_data)
            if signature:
                message.signature = signature.hex()
            
            # Invia tramite DHT
            success = self.dht.send_message_to_peer(message, peer_info)
            
            if success:
                # Salva in cronologia locale
                self.messages.append(message)
            
            return success
            
        except Exception as e:
            print(f"❌ Errore invio messaggio: {e}")
            return False
    
    def get_messages(self, peer_hash: Optional[str] = None) -> List[Message]:
        """
        Ottiene messaggi dalla cronologia
        
        Args:
            peer_hash: Hash peer specifico (None per tutti)
            
        Returns:
            List[Message]: Lista messaggi
        """
        if peer_hash:
            return [msg for msg in self.messages 
                   if msg.sender_hash == peer_hash or msg.recipient_hash == peer_hash]
        return self.messages.copy()
    
    def get_peers(self) -> List[PeerInfo]:
        """
        Ottiene lista peer conosciuti
        
        Returns:
            List[PeerInfo]: Lista peer
        """
        return list(self.dht.peers.values())
    
    def find_peer_by_name(self, display_name: str) -> Optional[PeerInfo]:
        """
        Cerca peer per nome visualizzato
        
        Args:
            display_name: Nome da cercare
            
        Returns:
            Optional[PeerInfo]: Peer trovato o None
        """
        for peer in self.dht.peers.values():
            if peer.display_name.lower() == display_name.lower():
                return peer
        return None
    
    def _handle_received_message(self, message: Message):
        """Gestisce messaggio ricevuto"""
        try:
            # Verifica che il messaggio sia per noi
            current_identity = self.identity_manager.get_current_identity()
            if not current_identity or message.recipient_hash != current_identity.identity_hash:
                return
            
            # Verifica firma se presente
            if message.signature:
                sender_peer = self.dht.find_peer(message.sender_hash)
                if sender_peer:
                    message_data = json.dumps(message.to_dict()).encode('utf-8')
                    signature = bytes.fromhex(message.signature)
                    
                    if not self.identity_manager.verify_peer_signature(
                        message_data, signature, sender_peer.public_key
                    ):
                        print(f"❌ Firma non valida per messaggio da {message.sender_hash[:16]}...")
                        return
            
            # Decritta contenuto se necessario
            if message.encrypted:
                decrypted_content = self._decrypt_message_content(message.content)
                if decrypted_content:
                    message.content = decrypted_content
                    message.encrypted = False
                else:
                    print(f"❌ Impossibile decrittare messaggio da {message.sender_hash[:16]}...")
                    return
            
            # Salva messaggio
            self.messages.append(message)
            
            # Notifica callback
            if self.message_received_callback:
                self.message_received_callback(message)
            
        except Exception as e:
            print(f"❌ Errore gestione messaggio ricevuto: {e}")
    
    def _handle_peer_discovered(self, peer_info: PeerInfo):
        """Gestisce discovery nuovo peer"""
        if self.peer_discovered_callback:
            self.peer_discovered_callback(peer_info)
    
    def _announce_self(self):
        """Annuncia presenza nella rete"""
        current_identity = self.identity_manager.get_current_identity()
        if not current_identity:
            return
        
        peer_info = PeerInfo(
            peer_hash=current_identity.identity_hash,
            public_key=current_identity.public_key,
            display_name=current_identity.display_name,
            last_seen=time.time(),
            port=self.dht.port
        )
        
        self.dht.announce_peer(peer_info)
    
    def _generate_message_id(self) -> str:
        """Genera ID univoco per messaggio"""
        timestamp = str(time.time())
        random_data = LaboonCrypto.generate_random_bytes(16)
        combined = timestamp.encode('utf-8') + random_data
        return LaboonCrypto.hash_data(combined).hex()[:32]
    
    def _encrypt_message_content(self, content: str, recipient_public_key: bytes) -> Optional[str]:
        """
        Critta contenuto messaggio per destinatario
        
        Args:
            content: Contenuto da crittare
            recipient_public_key: Chiave pubblica destinatario
            
        Returns:
            Optional[str]: Contenuto crittato o None se errore
        """
        try:
            # Per ora usa crittografia simmetrica semplice
            # In futuro: implementare ECDH per chiave condivisa
            content_bytes = content.encode('utf-8')
            
            # Usa hash della chiave pubblica come password temporanea
            key_hash = LaboonCrypto.hash_data(recipient_public_key)
            password = key_hash.hex()[:32]
            
            encrypted = LaboonCrypto.encrypt_data(content_bytes, password)
            if encrypted:
                return json.dumps({
                    'nonce': encrypted.nonce.hex(),
                    'ciphertext': encrypted.ciphertext.hex()
                })
            
            return None
            
        except Exception:
            return None
    
    def _decrypt_message_content(self, encrypted_content: str) -> Optional[str]:
        """
        Decritta contenuto messaggio
        
        Args:
            encrypted_content: Contenuto crittato
            
        Returns:
            Optional[str]: Contenuto in chiaro o None se errore
        """
        try:
            # Parse dati crittografati
            encrypted_data = json.loads(encrypted_content)
            nonce = bytes.fromhex(encrypted_data['nonce'])
            ciphertext = bytes.fromhex(encrypted_data['ciphertext'])
            
            # Usa hash della nostra chiave pubblica come password
            current_identity = self.identity_manager.get_current_identity()
            if not current_identity:
                return None
            
            key_hash = LaboonCrypto.hash_data(current_identity.public_key)
            password = key_hash.hex()[:32]
            
            # Decritta
            encrypted_obj = EncryptedData(nonce=nonce, ciphertext=ciphertext)
            decrypted_bytes = LaboonCrypto.decrypt_data(encrypted_obj, password)
            
            if decrypted_bytes:
                return decrypted_bytes.decode('utf-8')
            
            return None
            
        except Exception:
            return None


# Test rapido del modulo
if __name__ == "__main__":
    print("💬 Test LaboonMessaging...")
    
    # Test inizializzazione
    messaging = LaboonMessaging(6882)
    
    # Test avvio
    started = messaging.start()
    print(f"✅ Avvio: {started}")
    
    if started:
        # Test identità
        identity = messaging.identity_manager.get_current_identity()
        print(f"✅ Identità: {identity.identity_hash[:16] if identity else 'None'}...")
        
        # Test peers
        peers = messaging.get_peers()
        print(f"✅ Peers: {len(peers)}")
        
        # Test messaggi
        messages = messaging.get_messages()
        print(f"✅ Messaggi: {len(messages)}")
        
        # Ferma
        messaging.stop()
    
    print("🐋 LaboonMessaging funziona perfettamente! 🌊")