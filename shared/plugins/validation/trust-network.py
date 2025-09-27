#!/usr/bin/env python3
"""
Sistema di Propagazione Validità Plugin - LaboonChat
Implementa una rete di fiducia distribuita per validare plugin tra client
"""

import json
import hashlib
import time
import asyncio
import aiohttp
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, asdict
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
import sqlite3
import threading
from pathlib import Path

@dataclass
class PluginValidation:
    """Rappresenta una validazione di plugin"""
    plugin_id: str
    plugin_hash: str
    validator_id: str
    validator_signature: str
    trust_score: float
    timestamp: int
    validation_type: str  # "safe", "warning", "malicious"
    metadata: Dict

@dataclass
class TrustNode:
    """Rappresenta un nodo nella rete di fiducia"""
    node_id: str
    public_key: str
    trust_level: float
    last_seen: int
    validations_count: int
    reputation_score: float

class TrustNetwork:
    """Gestisce la rete di fiducia distribuita per la validazione plugin"""
    
    def __init__(self, data_dir: str = "./shared/plugins/validation"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Database locale per cache validazioni
        self.db_path = self.data_dir / "trust_network.db"
        self.init_database()
        
        # Configurazione rete
        self.node_id = self.generate_node_id()
        self.private_key, self.public_key = self.load_or_generate_keys()
        
        # Peer discovery
        self.known_peers: Set[str] = set()
        self.active_peers: Dict[str, TrustNode] = {}
        
        # Validazioni cache
        self.validation_cache: Dict[str, List[PluginValidation]] = {}
        self.trust_scores: Dict[str, float] = {}
        
        # DHT-like storage per propagazione
        self.dht_storage: Dict[str, Dict] = {}
        
        # Lock per thread safety
        self.lock = threading.RLock()
        
    def init_database(self):
        """Inizializza il database SQLite per la cache locale"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabella validazioni
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS validations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plugin_id TEXT NOT NULL,
                plugin_hash TEXT NOT NULL,
                validator_id TEXT NOT NULL,
                validator_signature TEXT NOT NULL,
                trust_score REAL NOT NULL,
                timestamp INTEGER NOT NULL,
                validation_type TEXT NOT NULL,
                metadata TEXT NOT NULL,
                UNIQUE(plugin_id, plugin_hash, validator_id)
            )
        ''')
        
        # Tabella nodi fiducia
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trust_nodes (
                node_id TEXT PRIMARY KEY,
                public_key TEXT NOT NULL,
                trust_level REAL NOT NULL,
                last_seen INTEGER NOT NULL,
                validations_count INTEGER NOT NULL,
                reputation_score REAL NOT NULL
            )
        ''')
        
        # Indici per performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_plugin_hash ON validations(plugin_hash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_validator ON validations(validator_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON validations(timestamp)')
        
        conn.commit()
        conn.close()
        
    def generate_node_id(self) -> str:
        """Genera un ID univoco per questo nodo"""
        import uuid
        import platform
        
        # Combina informazioni sistema per ID stabile
        system_info = f"{platform.node()}-{platform.system()}-{uuid.getnode()}"
        return hashlib.sha256(system_info.encode()).hexdigest()[:16]
        
    def load_or_generate_keys(self) -> Tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
        """Carica o genera chiavi RSA per questo nodo"""
        private_key_path = self.data_dir / f"node_{self.node_id}_private.pem"
        public_key_path = self.data_dir / f"node_{self.node_id}_public.pem"
        
        if private_key_path.exists() and public_key_path.exists():
            # Carica chiavi esistenti
            with open(private_key_path, 'rb') as f:
                private_key = serialization.load_pem_private_key(f.read(), password=None)
            
            with open(public_key_path, 'rb') as f:
                public_key = serialization.load_pem_public_key(f.read())
                
            return private_key, public_key
        else:
            # Genera nuove chiavi
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            public_key = private_key.public_key()
            
            # Salva chiavi
            with open(private_key_path, 'wb') as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
                
            with open(public_key_path, 'wb') as f:
                f.write(public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ))
                
            return private_key, public_key
            
    def sign_validation(self, plugin_hash: str, validation_type: str, metadata: Dict) -> str:
        """Firma una validazione con la chiave privata del nodo"""
        validation_data = {
            "plugin_hash": plugin_hash,
            "validation_type": validation_type,
            "metadata": metadata,
            "timestamp": int(time.time()),
            "validator_id": self.node_id
        }
        
        message = json.dumps(validation_data, sort_keys=True).encode()
        signature = self.private_key.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        return signature.hex()
        
    def verify_validation(self, validation: PluginValidation, public_key_pem: str) -> bool:
        """Verifica la firma di una validazione"""
        try:
            public_key = serialization.load_pem_public_key(public_key_pem.encode())
            
            validation_data = {
                "plugin_hash": validation.plugin_hash,
                "validation_type": validation.validation_type,
                "metadata": validation.metadata,
                "timestamp": validation.timestamp,
                "validator_id": validation.validator_id
            }
            
            message = json.dumps(validation_data, sort_keys=True).encode()
            signature = bytes.fromhex(validation.validator_signature)
            
            public_key.verify(
                signature,
                message,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            return True
        except Exception:
            return False
            
    def add_validation(self, plugin_id: str, plugin_hash: str, validation_type: str, 
                      metadata: Dict = None) -> PluginValidation:
        """Aggiunge una nuova validazione per un plugin"""
        if metadata is None:
            metadata = {}
            
        signature = self.sign_validation(plugin_hash, validation_type, metadata)
        
        validation = PluginValidation(
            plugin_id=plugin_id,
            plugin_hash=plugin_hash,
            validator_id=self.node_id,
            validator_signature=signature,
            trust_score=1.0,  # Massima fiducia per validazioni proprie
            timestamp=int(time.time()),
            validation_type=validation_type,
            metadata=metadata
        )
        
        # Salva nel database locale
        self.store_validation(validation)
        
        # Propaga nella rete
        asyncio.create_task(self.propagate_validation(validation))
        
        return validation
        
    def store_validation(self, validation: PluginValidation):
        """Memorizza una validazione nel database locale"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO validations 
                (plugin_id, plugin_hash, validator_id, validator_signature, 
                 trust_score, timestamp, validation_type, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                validation.plugin_id,
                validation.plugin_hash,
                validation.validator_id,
                validation.validator_signature,
                validation.trust_score,
                validation.timestamp,
                validation.validation_type,
                json.dumps(validation.metadata)
            ))
            
            conn.commit()
            conn.close()
            
    def get_plugin_validations(self, plugin_hash: str) -> List[PluginValidation]:
        """Recupera tutte le validazioni per un plugin"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT plugin_id, plugin_hash, validator_id, validator_signature,
                       trust_score, timestamp, validation_type, metadata
                FROM validations 
                WHERE plugin_hash = ?
                ORDER BY timestamp DESC
            ''', (plugin_hash,))
            
            validations = []
            for row in cursor.fetchall():
                validations.append(PluginValidation(
                    plugin_id=row[0],
                    plugin_hash=row[1],
                    validator_id=row[2],
                    validator_signature=row[3],
                    trust_score=row[4],
                    timestamp=row[5],
                    validation_type=row[6],
                    metadata=json.loads(row[7])
                ))
                
            conn.close()
            return validations
            
    def calculate_plugin_trust_score(self, plugin_hash: str) -> float:
        """Calcola il punteggio di fiducia aggregato per un plugin"""
        validations = self.get_plugin_validations(plugin_hash)
        
        if not validations:
            return 0.0
            
        # Algoritmo di calcolo fiducia pesato
        total_weight = 0.0
        weighted_score = 0.0
        
        for validation in validations:
            # Peso basato su reputazione validatore e età validazione
            validator_reputation = self.get_validator_reputation(validation.validator_id)
            age_factor = max(0.1, 1.0 - (time.time() - validation.timestamp) / (30 * 24 * 3600))  # Decade in 30 giorni
            
            weight = validator_reputation * age_factor
            
            # Score basato su tipo validazione
            if validation.validation_type == "safe":
                score = 1.0
            elif validation.validation_type == "warning":
                score = 0.5
            elif validation.validation_type == "malicious":
                score = 0.0
            else:
                score = 0.5  # Default per tipi sconosciuti
                
            weighted_score += score * weight
            total_weight += weight
            
        return weighted_score / total_weight if total_weight > 0 else 0.0
        
    def get_validator_reputation(self, validator_id: str) -> float:
        """Calcola la reputazione di un validatore"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT reputation_score FROM trust_nodes WHERE node_id = ?
            ''', (validator_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return result[0]
            else:
                # Reputazione default per nodi sconosciuti
                return 0.5
                
    async def propagate_validation(self, validation: PluginValidation):
        """Propaga una validazione nella rete P2P"""
        message = {
            "type": "validation_propagation",
            "validation": asdict(validation),
            "source_node": self.node_id,
            "timestamp": int(time.time())
        }
        
        # Invia a tutti i peer attivi
        tasks = []
        for peer_id, peer_node in self.active_peers.items():
            if peer_id != self.node_id:  # Non inviare a se stesso
                tasks.append(self.send_to_peer(peer_id, message))
                
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            
    async def send_to_peer(self, peer_id: str, message: Dict):
        """Invia un messaggio a un peer specifico"""
        try:
            # Implementazione semplificata - in realtà userebbe il protocollo P2P di LaboonChat
            # Per ora simula l'invio
            print(f"Sending validation to peer {peer_id}: {message['type']}")
            
            # TODO: Integrare con il sistema P2P esistente di LaboonChat
            # await self.p2p_client.send_message(peer_id, message)
            
        except Exception as e:
            print(f"Failed to send message to peer {peer_id}: {e}")
            
    def receive_validation(self, validation_data: Dict, source_peer: str):
        """Riceve e processa una validazione da un peer"""
        try:
            validation = PluginValidation(**validation_data)
            
            # Verifica che non sia già presente
            existing = self.get_plugin_validations(validation.plugin_hash)
            for existing_val in existing:
                if (existing_val.validator_id == validation.validator_id and 
                    existing_val.timestamp == validation.timestamp):
                    return  # Già presente
                    
            # Calcola trust score basato sulla reputazione del source peer
            source_reputation = self.get_validator_reputation(source_peer)
            validation.trust_score = source_reputation
            
            # Memorizza la validazione
            self.store_validation(validation)
            
            # Propaga ulteriormente (con limite per evitare loop)
            if validation.metadata.get("propagation_count", 0) < 3:
                validation.metadata["propagation_count"] = validation.metadata.get("propagation_count", 0) + 1
                asyncio.create_task(self.propagate_validation(validation))
                
        except Exception as e:
            print(f"Error processing received validation: {e}")
            
    def update_peer_reputation(self, peer_id: str, reputation_delta: float):
        """Aggiorna la reputazione di un peer"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE trust_nodes 
                SET reputation_score = CASE 
                    WHEN reputation_score + ? > 1.0 THEN 1.0
                    WHEN reputation_score + ? < 0.0 THEN 0.0
                    ELSE reputation_score + ?
                END,
                last_seen = ?
                WHERE node_id = ?
            ''', (reputation_delta, reputation_delta, reputation_delta, int(time.time()), peer_id))
            
            if cursor.rowcount == 0:
                # Nuovo nodo
                cursor.execute('''
                    INSERT INTO trust_nodes 
                    (node_id, public_key, trust_level, last_seen, validations_count, reputation_score)
                    VALUES (?, '', 0.5, ?, 0, ?)
                ''', (peer_id, int(time.time()), max(0.0, min(1.0, 0.5 + reputation_delta))))
                
            conn.commit()
            conn.close()
            
    def get_network_consensus(self, plugin_hash: str) -> Dict:
        """Ottiene il consenso della rete su un plugin"""
        validations = self.get_plugin_validations(plugin_hash)
        
        if not validations:
            return {
                "consensus": "unknown",
                "confidence": 0.0,
                "total_validations": 0,
                "trust_score": 0.0
            }
            
        # Conta validazioni per tipo
        safe_count = sum(1 for v in validations if v.validation_type == "safe")
        warning_count = sum(1 for v in validations if v.validation_type == "warning")
        malicious_count = sum(1 for v in validations if v.validation_type == "malicious")
        
        total_validations = len(validations)
        trust_score = self.calculate_plugin_trust_score(plugin_hash)
        
        # Determina consenso
        if malicious_count > total_validations * 0.3:  # 30% soglia per malicious
            consensus = "malicious"
            confidence = malicious_count / total_validations
        elif safe_count > total_validations * 0.6:  # 60% soglia per safe
            consensus = "safe"
            confidence = safe_count / total_validations
        elif warning_count > total_validations * 0.4:  # 40% soglia per warning
            consensus = "warning"
            confidence = warning_count / total_validations
        else:
            consensus = "uncertain"
            confidence = 0.5
            
        return {
            "consensus": consensus,
            "confidence": confidence,
            "total_validations": total_validations,
            "trust_score": trust_score,
            "breakdown": {
                "safe": safe_count,
                "warning": warning_count,
                "malicious": malicious_count
            }
        }

# Esempio di utilizzo
if __name__ == "__main__":
    # Inizializza rete di fiducia
    trust_network = TrustNetwork()
    
    # Simula validazione di un plugin
    plugin_hash = "abc123def456"
    validation = trust_network.add_validation(
        plugin_id="security-core",
        plugin_hash=plugin_hash,
        validation_type="safe",
        metadata={"scanned_by": "antivirus", "clean": True}
    )
    
    print(f"Added validation: {validation}")
    
    # Ottieni consenso rete
    consensus = trust_network.get_network_consensus(plugin_hash)
    print(f"Network consensus: {consensus}")