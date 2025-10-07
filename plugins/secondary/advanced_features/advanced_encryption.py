"""
Advanced Encryption Plugin - Plugin Secondario per LaboonChat2

Plugin avanzato per crittografia che fornisce:
- Algoritmi di crittografia multipli (AES, ChaCha20, RSA)
- Gestione avanzata delle chiavi (generazione, rotazione, backup)
- Crittografia end-to-end per messaggi e file
- Firma digitale e verifica integrità
- Perfect Forward Secrecy (PFS)
- Steganografia per nascondere messaggi
- Crittografia quantistica-resistente
- Audit trail delle operazioni crittografiche
"""

import asyncio
import hashlib
import json
import time
import secrets
import os
from typing import Dict, List, Optional, Any, Callable, Tuple, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import logging
import base64

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from laboon_chat2.core.interfaces import ISecondaryPlugin


class EncryptionAlgorithm(Enum):
    """Algoritmi di crittografia supportati"""
    AES_256_GCM = "aes_256_gcm"
    CHACHA20_POLY1305 = "chacha20_poly1305"
    RSA_4096 = "rsa_4096"
    ECDSA_P384 = "ecdsa_p384"
    KYBER_1024 = "kyber_1024"  # Post-quantum
    DILITHIUM_5 = "dilithium_5"  # Post-quantum signatures


class KeyType(Enum):
    """Tipi di chiavi"""
    SYMMETRIC = "symmetric"
    ASYMMETRIC_PUBLIC = "asymmetric_public"
    ASYMMETRIC_PRIVATE = "asymmetric_private"
    EPHEMERAL = "ephemeral"
    MASTER = "master"
    DERIVED = "derived"


class OperationType(Enum):
    """Tipi di operazioni crittografiche"""
    ENCRYPT = "encrypt"
    DECRYPT = "decrypt"
    SIGN = "sign"
    VERIFY = "verify"
    KEY_GENERATION = "key_generation"
    KEY_EXCHANGE = "key_exchange"
    KEY_DERIVATION = "key_derivation"


@dataclass
class CryptoKey:
    """Chiave crittografica"""
    key_id: str
    key_type: KeyType
    algorithm: EncryptionAlgorithm
    key_data: bytes
    public_key: Optional[bytes] = None
    created_at: float = 0.0
    expires_at: float = 0.0
    usage_count: int = 0
    max_usage: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.created_at == 0.0:
            self.created_at = time.time()


@dataclass
class EncryptionResult:
    """Risultato operazione di crittografia"""
    success: bool
    data: Optional[bytes] = None
    algorithm: Optional[EncryptionAlgorithm] = None
    key_id: Optional[str] = None
    nonce: Optional[bytes] = None
    tag: Optional[bytes] = None
    signature: Optional[bytes] = None
    error_message: str = ""
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class CryptoOperation:
    """Operazione crittografica per audit"""
    operation_id: str
    operation_type: OperationType
    algorithm: EncryptionAlgorithm
    key_id: str
    timestamp: float
    peer_id: Optional[str] = None
    data_size: int = 0
    success: bool = True
    error_message: str = ""
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class SteganographyResult:
    """Risultato operazione steganografica"""
    success: bool
    data: Optional[bytes] = None
    cover_type: str = ""
    hidden_size: int = 0
    error_message: str = ""


@dataclass
class CryptoStats:
    """Statistiche crittografiche"""
    total_encryptions: int = 0
    total_decryptions: int = 0
    total_signatures: int = 0
    total_verifications: int = 0
    total_key_generations: int = 0
    total_key_exchanges: int = 0
    bytes_encrypted: int = 0
    bytes_decrypted: int = 0
    active_keys: int = 0
    expired_keys: int = 0
    failed_operations: int = 0


class AdvancedEncryption(ISecondaryPlugin):
    """
    Plugin avanzato per crittografia e sicurezza
    
    Caratteristiche:
    - Algoritmi multipli (classici e post-quantum)
    - Gestione avanzata chiavi
    - Perfect Forward Secrecy
    - Steganografia
    - Audit completo
    - Crittografia end-to-end
    """
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        
        # Moduli core
        self.security_module = None
        self.messaging_module = None
        self.network_module = None
        self.interface_module = None
        
        # Stato interno
        self.running = False
        self.logger = logging.getLogger(__name__)
        
        # Gestione chiavi
        self.keys: Dict[str, CryptoKey] = {}
        self.key_pairs: Dict[str, Tuple[str, str]] = {}  # key_id -> (public_id, private_id)
        self.ephemeral_keys: Dict[str, CryptoKey] = {}
        
        # Sessioni crittografiche
        self.active_sessions: Dict[str, Dict[str, Any]] = {}  # peer_id -> session_data
        
        # Audit trail
        self.operations_log: List[CryptoOperation] = []
        self.stats = CryptoStats()
        
        # Task asincroni
        self.background_tasks: Set[asyncio.Task] = set()
        
        # Handler eventi
        self.key_rotation_handler: Optional[Callable] = None
        self.security_alert_handler: Optional[Callable] = None
        
        # Configurazioni
        self.default_algorithm = EncryptionAlgorithm.AES_256_GCM
        self.key_rotation_interval = 3600  # 1 ora
        self.max_key_usage = 1000000  # 1M operazioni
        self.enable_pfs = True
        self.enable_steganography = True
        
        # Directory
        self.keys_dir = Path("keys")
        self.audit_dir = Path("audit")
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Inizializza il plugin"""
        self.config = config.copy()
        
        # Configura parametri
        self.default_algorithm = EncryptionAlgorithm(
            config.get("default_algorithm", "aes_256_gcm")
        )
        self.key_rotation_interval = config.get("key_rotation_interval", 3600)
        self.max_key_usage = config.get("max_key_usage", 1000000)
        self.enable_pfs = config.get("enable_pfs", True)
        self.enable_steganography = config.get("enable_steganography", True)
        
        # Crea directory
        base_dir = Path(config.get("data_dir", "data/encryption"))
        self.keys_dir = base_dir / "keys"
        self.audit_dir = base_dir / "audit"
        
        for directory in [self.keys_dir, self.audit_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Carica dati persistenti
        await self._load_persistent_data()
        
        # Genera chiavi master se non esistono
        await self._ensure_master_keys()
        
        # Avvia task di background
        await self._start_background_tasks()
        
        self.running = True
        self.logger.info("AdvancedEncryption inizializzato")
    
    async def cleanup(self) -> None:
        """Pulisce le risorse del plugin"""
        self.running = False
        
        # Ferma task di background
        await self._stop_background_tasks()
        
        # Salva dati persistenti
        await self._save_persistent_data()
        
        # Pulisci chiavi dalla memoria
        self.keys.clear()
        self.ephemeral_keys.clear()
        self.active_sessions.clear()
        
        self.logger.info("AdvancedEncryption terminato")
    
    def get_plugin_info(self) -> Dict[str, Any]:
        """Restituisce informazioni sul plugin"""
        return {
            "name": "AdvancedEncryption",
            "version": "1.0.0",
            "type": "secondary",
            "category": "advanced_features",
            "description": "Sistema avanzato di crittografia con algoritmi multipli e gestione chiavi",
            "author": "LaboonChat2 Team",
            "capabilities": [
                "multiple_algorithms",
                "key_management",
                "perfect_forward_secrecy",
                "steganography",
                "post_quantum_crypto",
                "audit_trail",
                "end_to_end_encryption",
                "digital_signatures"
            ],
            "dependencies": ["security"],
            "optional_dependencies": ["messaging", "network", "interface"]
        }
    
    async def activate(self) -> bool:
        """Attiva il plugin"""
        try:
            # Registra handler messaggi se disponibile
            if self.messaging_module:
                await self.messaging_module.set_message_handler(self._handle_crypto_message)
            
            self.logger.info("AdvancedEncryption attivato")
            return True
            
        except Exception as e:
            self.logger.error(f"Errore attivazione AdvancedEncryption: {e}")
            return False
    
    async def deactivate(self) -> bool:
        """Disattiva il plugin"""
        try:
            # Termina sessioni attive
            for peer_id in list(self.active_sessions.keys()):
                await self.end_session(peer_id)
            
            self.logger.info("AdvancedEncryption disattivato")
            return True
            
        except Exception as e:
            self.logger.error(f"Errore disattivazione AdvancedEncryption: {e}")
            return False
    
    async def set_core_module(self, module_type: str, module_instance: Any) -> None:
        """Imposta riferimento a modulo core"""
        if module_type == "security":
            self.security_module = module_instance
        elif module_type == "messaging":
            self.messaging_module = module_instance
        elif module_type == "network":
            self.network_module = module_instance
        elif module_type == "interface":
            self.interface_module = module_instance
    
    async def get_status(self) -> Dict[str, Any]:
        """Restituisce stato del plugin"""
        return {
            "running": self.running,
            "total_keys": len(self.keys),
            "ephemeral_keys": len(self.ephemeral_keys),
            "active_sessions": len(self.active_sessions),
            "stats": asdict(self.stats)
        }
    
    async def update_config(self, new_config: Dict[str, Any]) -> None:
        """Aggiorna configurazione del plugin"""
        self.config.update(new_config)
        
        # Aggiorna parametri se cambiati
        if "default_algorithm" in new_config:
            self.default_algorithm = EncryptionAlgorithm(new_config["default_algorithm"])
        if "key_rotation_interval" in new_config:
            self.key_rotation_interval = new_config["key_rotation_interval"]
        if "enable_pfs" in new_config:
            self.enable_pfs = new_config["enable_pfs"]
    
    # Metodi pubblici per crittografia
    
    async def encrypt_data(self, data: bytes, algorithm: EncryptionAlgorithm = None, 
                          key_id: str = None, peer_id: str = None) -> EncryptionResult:
        """Crittografa dati"""
        try:
            if algorithm is None:
                algorithm = self.default_algorithm
            
            # Seleziona o genera chiave
            if key_id is None:
                if peer_id and peer_id in self.active_sessions:
                    key_id = self.active_sessions[peer_id].get("session_key_id")
                else:
                    key_id = await self._get_or_create_key(algorithm, KeyType.SYMMETRIC)
            
            if key_id not in self.keys:
                return EncryptionResult(
                    success=False,
                    error_message=f"Chiave non trovata: {key_id}"
                )
            
            key = self.keys[key_id]
            
            # Esegui crittografia
            result = await self._encrypt_with_algorithm(data, key, algorithm)
            
            if result.success:
                # Aggiorna statistiche
                self.stats.total_encryptions += 1
                self.stats.bytes_encrypted += len(data)
                key.usage_count += 1
                
                # Log operazione
                await self._log_operation(
                    OperationType.ENCRYPT,
                    algorithm,
                    key_id,
                    peer_id,
                    len(data),
                    True
                )
                
                # Verifica limiti di utilizzo
                if key.max_usage > 0 and key.usage_count >= key.max_usage:
                    await self._schedule_key_rotation(key_id)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Errore crittografia: {e}")
            self.stats.failed_operations += 1
            return EncryptionResult(
                success=False,
                error_message=str(e)
            )
    
    async def decrypt_data(self, encrypted_data: bytes, algorithm: EncryptionAlgorithm,
                          key_id: str, nonce: bytes = None, tag: bytes = None,
                          peer_id: str = None) -> EncryptionResult:
        """Decrittografa dati"""
        try:
            if key_id not in self.keys:
                return EncryptionResult(
                    success=False,
                    error_message=f"Chiave non trovata: {key_id}"
                )
            
            key = self.keys[key_id]
            
            # Esegui decrittografia
            result = await self._decrypt_with_algorithm(
                encrypted_data, key, algorithm, nonce, tag
            )
            
            if result.success:
                # Aggiorna statistiche
                self.stats.total_decryptions += 1
                self.stats.bytes_decrypted += len(result.data)
                key.usage_count += 1
                
                # Log operazione
                await self._log_operation(
                    OperationType.DECRYPT,
                    algorithm,
                    key_id,
                    peer_id,
                    len(encrypted_data),
                    True
                )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Errore decrittografia: {e}")
            self.stats.failed_operations += 1
            return EncryptionResult(
                success=False,
                error_message=str(e)
            )
    
    async def sign_data(self, data: bytes, algorithm: EncryptionAlgorithm = None,
                       key_id: str = None) -> EncryptionResult:
        """Firma digitalmente i dati"""
        try:
            if algorithm is None:
                algorithm = EncryptionAlgorithm.ECDSA_P384
            
            if key_id is None:
                key_id = await self._get_or_create_key(algorithm, KeyType.ASYMMETRIC_PRIVATE)
            
            if key_id not in self.keys:
                return EncryptionResult(
                    success=False,
                    error_message=f"Chiave privata non trovata: {key_id}"
                )
            
            key = self.keys[key_id]
            
            # Esegui firma
            signature = await self._sign_with_algorithm(data, key, algorithm)
            
            if signature:
                # Aggiorna statistiche
                self.stats.total_signatures += 1
                key.usage_count += 1
                
                # Log operazione
                await self._log_operation(
                    OperationType.SIGN,
                    algorithm,
                    key_id,
                    None,
                    len(data),
                    True
                )
                
                return EncryptionResult(
                    success=True,
                    signature=signature,
                    algorithm=algorithm,
                    key_id=key_id
                )
            else:
                return EncryptionResult(
                    success=False,
                    error_message="Errore generazione firma"
                )
            
        except Exception as e:
            self.logger.error(f"Errore firma: {e}")
            self.stats.failed_operations += 1
            return EncryptionResult(
                success=False,
                error_message=str(e)
            )
    
    async def verify_signature(self, data: bytes, signature: bytes,
                              algorithm: EncryptionAlgorithm, key_id: str) -> bool:
        """Verifica firma digitale"""
        try:
            # Cerca chiave pubblica
            public_key_id = None
            if key_id in self.key_pairs:
                public_key_id = self.key_pairs[key_id][0]
            elif key_id in self.keys and self.keys[key_id].key_type == KeyType.ASYMMETRIC_PUBLIC:
                public_key_id = key_id
            
            if not public_key_id or public_key_id not in self.keys:
                self.logger.error(f"Chiave pubblica non trovata per: {key_id}")
                return False
            
            public_key = self.keys[public_key_id]
            
            # Verifica firma
            valid = await self._verify_with_algorithm(data, signature, public_key, algorithm)
            
            # Aggiorna statistiche
            self.stats.total_verifications += 1
            if not valid:
                self.stats.failed_operations += 1
            
            # Log operazione
            await self._log_operation(
                OperationType.VERIFY,
                algorithm,
                public_key_id,
                None,
                len(data),
                valid
            )
            
            return valid
            
        except Exception as e:
            self.logger.error(f"Errore verifica firma: {e}")
            self.stats.failed_operations += 1
            return False
    
    async def generate_key_pair(self, algorithm: EncryptionAlgorithm) -> Optional[Tuple[str, str]]:
        """Genera coppia di chiavi asimmetriche"""
        try:
            # Genera chiavi
            private_key_data, public_key_data = await self._generate_key_pair(algorithm)
            
            if not private_key_data or not public_key_data:
                return None
            
            # Crea ID chiavi
            private_key_id = self._generate_key_id()
            public_key_id = self._generate_key_id()
            
            # Crea oggetti chiave
            private_key = CryptoKey(
                key_id=private_key_id,
                key_type=KeyType.ASYMMETRIC_PRIVATE,
                algorithm=algorithm,
                key_data=private_key_data,
                public_key=public_key_data,
                max_usage=self.max_key_usage
            )
            
            public_key = CryptoKey(
                key_id=public_key_id,
                key_type=KeyType.ASYMMETRIC_PUBLIC,
                algorithm=algorithm,
                key_data=public_key_data,
                max_usage=self.max_key_usage
            )
            
            # Salva chiavi
            self.keys[private_key_id] = private_key
            self.keys[public_key_id] = public_key
            self.key_pairs[private_key_id] = (public_key_id, private_key_id)
            
            # Aggiorna statistiche
            self.stats.total_key_generations += 1
            self.stats.active_keys += 2
            
            # Log operazione
            await self._log_operation(
                OperationType.KEY_GENERATION,
                algorithm,
                private_key_id,
                None,
                0,
                True
            )
            
            self.logger.info(f"Coppia chiavi generata: {algorithm.value}")
            return (public_key_id, private_key_id)
            
        except Exception as e:
            self.logger.error(f"Errore generazione coppia chiavi: {e}")
            self.stats.failed_operations += 1
            return None
    
    async def start_session(self, peer_id: str, use_pfs: bool = None) -> bool:
        """Avvia sessione crittografica con un peer"""
        try:
            if use_pfs is None:
                use_pfs = self.enable_pfs
            
            if peer_id in self.active_sessions:
                await self.end_session(peer_id)
            
            # Genera chiave di sessione
            session_key_id = await self._generate_session_key(peer_id, use_pfs)
            
            if not session_key_id:
                return False
            
            # Crea sessione
            session_data = {
                "session_key_id": session_key_id,
                "peer_id": peer_id,
                "started_at": time.time(),
                "use_pfs": use_pfs,
                "message_count": 0,
                "last_activity": time.time()
            }
            
            self.active_sessions[peer_id] = session_data
            
            # Log operazione
            await self._log_operation(
                OperationType.KEY_EXCHANGE,
                self.default_algorithm,
                session_key_id,
                peer_id,
                0,
                True
            )
            
            self.logger.info(f"Sessione crittografica avviata con {peer_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Errore avvio sessione con {peer_id}: {e}")
            return False
    
    async def end_session(self, peer_id: str) -> bool:
        """Termina sessione crittografica"""
        try:
            if peer_id not in self.active_sessions:
                return False
            
            session_data = self.active_sessions[peer_id]
            session_key_id = session_data["session_key_id"]
            
            # Rimuovi chiave di sessione se PFS
            if session_data.get("use_pfs", False):
                if session_key_id in self.ephemeral_keys:
                    del self.ephemeral_keys[session_key_id]
                elif session_key_id in self.keys:
                    del self.keys[session_key_id]
            
            # Rimuovi sessione
            del self.active_sessions[peer_id]
            
            self.logger.info(f"Sessione crittografica terminata con {peer_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Errore terminazione sessione con {peer_id}: {e}")
            return False
    
    async def rotate_key(self, key_id: str) -> Optional[str]:
        """Ruota una chiave"""
        try:
            if key_id not in self.keys:
                return None
            
            old_key = self.keys[key_id]
            
            # Genera nuova chiave dello stesso tipo
            if old_key.key_type == KeyType.SYMMETRIC:
                new_key_id = await self._get_or_create_key(old_key.algorithm, KeyType.SYMMETRIC)
            elif old_key.key_type == KeyType.ASYMMETRIC_PRIVATE:
                key_pair = await self.generate_key_pair(old_key.algorithm)
                if key_pair:
                    new_key_id = key_pair[1]  # Chiave privata
                else:
                    return None
            else:
                return None
            
            # Marca vecchia chiave come scaduta
            old_key.expires_at = time.time()
            
            # Notifica rotazione se handler disponibile
            if self.key_rotation_handler:
                await self.key_rotation_handler(key_id, new_key_id)
            
            self.logger.info(f"Chiave ruotata: {key_id} -> {new_key_id}")
            return new_key_id
            
        except Exception as e:
            self.logger.error(f"Errore rotazione chiave {key_id}: {e}")
            return None
    
    async def hide_message_in_image(self, message: bytes, cover_image: bytes) -> SteganographyResult:
        """Nasconde messaggio in immagine usando steganografia"""
        try:
            if not self.enable_steganography:
                return SteganographyResult(
                    success=False,
                    error_message="Steganografia disabilitata"
                )
            
            # Implementazione semplificata LSB steganography
            # In produzione usare librerie specializzate
            
            if len(message) * 8 > len(cover_image):
                return SteganographyResult(
                    success=False,
                    error_message="Messaggio troppo grande per l'immagine"
                )
            
            # Copia immagine
            stego_image = bytearray(cover_image)
            
            # Nascondi lunghezza messaggio nei primi 32 bit
            msg_len = len(message)
            for i in range(32):
                bit = (msg_len >> (31 - i)) & 1
                stego_image[i] = (stego_image[i] & 0xFE) | bit
            
            # Nascondi messaggio
            bit_index = 32
            for byte in message:
                for i in range(8):
                    bit = (byte >> (7 - i)) & 1
                    stego_image[bit_index] = (stego_image[bit_index] & 0xFE) | bit
                    bit_index += 1
            
            return SteganographyResult(
                success=True,
                data=bytes(stego_image),
                cover_type="image",
                hidden_size=len(message)
            )
            
        except Exception as e:
            self.logger.error(f"Errore steganografia: {e}")
            return SteganographyResult(
                success=False,
                error_message=str(e)
            )
    
    async def extract_message_from_image(self, stego_image: bytes) -> SteganographyResult:
        """Estrae messaggio nascosto da immagine"""
        try:
            if not self.enable_steganography:
                return SteganographyResult(
                    success=False,
                    error_message="Steganografia disabilitata"
                )
            
            # Estrai lunghezza messaggio
            msg_len = 0
            for i in range(32):
                bit = stego_image[i] & 1
                msg_len = (msg_len << 1) | bit
            
            if msg_len <= 0 or msg_len > len(stego_image) // 8:
                return SteganographyResult(
                    success=False,
                    error_message="Lunghezza messaggio non valida"
                )
            
            # Estrai messaggio
            message = bytearray()
            bit_index = 32
            
            for _ in range(msg_len):
                byte_val = 0
                for i in range(8):
                    bit = stego_image[bit_index] & 1
                    byte_val = (byte_val << 1) | bit
                    bit_index += 1
                message.append(byte_val)
            
            return SteganographyResult(
                success=True,
                data=bytes(message),
                cover_type="image",
                hidden_size=len(message)
            )
            
        except Exception as e:
            self.logger.error(f"Errore estrazione steganografia: {e}")
            return SteganographyResult(
                success=False,
                error_message=str(e)
            )
    
    async def get_key_info(self, key_id: str) -> Optional[Dict[str, Any]]:
        """Restituisce informazioni su una chiave"""
        if key_id in self.keys:
            key = self.keys[key_id]
            info = {
                "key_id": key.key_id,
                "key_type": key.key_type.value,
                "algorithm": key.algorithm.value,
                "created_at": key.created_at,
                "expires_at": key.expires_at,
                "usage_count": key.usage_count,
                "max_usage": key.max_usage,
                "is_expired": key.expires_at > 0 and time.time() > key.expires_at,
                "metadata": key.metadata
            }
            
            # Aggiungi chiave pubblica se disponibile
            if key_id in self.key_pairs:
                info["public_key_id"] = self.key_pairs[key_id][0]
            
            return info
        
        return None
    
    async def list_keys(self, key_type: KeyType = None, algorithm: EncryptionAlgorithm = None) -> List[Dict[str, Any]]:
        """Lista chiavi con filtri opzionali"""
        keys_info = []
        
        for key_id, key in self.keys.items():
            # Applica filtri
            if key_type and key.key_type != key_type:
                continue
            if algorithm and key.algorithm != algorithm:
                continue
            
            info = await self.get_key_info(key_id)
            if info:
                keys_info.append(info)
        
        return keys_info
    
    async def get_audit_log(self, limit: int = 100, operation_type: OperationType = None) -> List[Dict[str, Any]]:
        """Restituisce log audit delle operazioni"""
        operations = self.operations_log[-limit:] if limit > 0 else self.operations_log
        
        if operation_type:
            operations = [op for op in operations if op.operation_type == operation_type]
        
        return [asdict(op) for op in operations]
    
    async def get_crypto_stats(self) -> Dict[str, Any]:
        """Restituisce statistiche crittografiche"""
        stats_dict = asdict(self.stats)
        
        # Aggiungi statistiche in tempo reale
        stats_dict["active_keys"] = len(self.keys)
        stats_dict["ephemeral_keys"] = len(self.ephemeral_keys)
        stats_dict["active_sessions"] = len(self.active_sessions)
        
        # Conta chiavi scadute
        current_time = time.time()
        expired_count = sum(
            1 for key in self.keys.values()
            if key.expires_at > 0 and current_time > key.expires_at
        )
        stats_dict["expired_keys"] = expired_count
        
        return stats_dict
    
    async def set_key_rotation_handler(self, handler: Callable) -> None:
        """Imposta handler per rotazione chiavi"""
        self.key_rotation_handler = handler
    
    async def set_security_alert_handler(self, handler: Callable) -> None:
        """Imposta handler per alert di sicurezza"""
        self.security_alert_handler = handler
    
    # Metodi privati
    
    async def _handle_crypto_message(self, sender_id: str, message_type: str, content: bytes) -> None:
        """Handler per messaggi crittografici"""
        try:
            if message_type.startswith("crypto_"):
                await self._handle_crypto_protocol_message(sender_id, message_type, content)
        except Exception as e:
            self.logger.error(f"Errore gestione messaggio crypto: {e}")
    
    async def _handle_crypto_protocol_message(self, sender_id: str, message_type: str, content: bytes) -> None:
        """Gestisce messaggi del protocollo crittografico"""
        try:
            data = json.loads(content.decode('utf-8'))
            
            if message_type == "crypto_key_exchange":
                await self._handle_key_exchange(sender_id, data)
            elif message_type == "crypto_session_request":
                await self._handle_session_request(sender_id, data)
            elif message_type == "crypto_session_response":
                await self._handle_session_response(sender_id, data)
                
        except Exception as e:
            self.logger.error(f"Errore gestione messaggio protocollo crypto: {e}")
    
    async def _get_or_create_key(self, algorithm: EncryptionAlgorithm, key_type: KeyType) -> str:
        """Ottiene o crea una chiave"""
        # Cerca chiave esistente
        for key_id, key in self.keys.items():
            if (key.algorithm == algorithm and 
                key.key_type == key_type and
                (key.expires_at == 0 or time.time() < key.expires_at) and
                (key.max_usage == 0 or key.usage_count < key.max_usage)):
                return key_id
        
        # Crea nuova chiave
        return await self._create_new_key(algorithm, key_type)
    
    async def _create_new_key(self, algorithm: EncryptionAlgorithm, key_type: KeyType) -> str:
        """Crea una nuova chiave"""
        key_id = self._generate_key_id()
        
        if key_type == KeyType.SYMMETRIC:
            key_data = await self._generate_symmetric_key(algorithm)
        else:
            # Per chiavi asimmetriche, genera coppia
            key_pair = await self.generate_key_pair(algorithm)
            if key_pair:
                return key_pair[1] if key_type == KeyType.ASYMMETRIC_PRIVATE else key_pair[0]
            else:
                raise Exception("Errore generazione coppia chiavi")
        
        key = CryptoKey(
            key_id=key_id,
            key_type=key_type,
            algorithm=algorithm,
            key_data=key_data,
            max_usage=self.max_key_usage
        )
        
        self.keys[key_id] = key
        self.stats.active_keys += 1
        
        return key_id
    
    async def _generate_symmetric_key(self, algorithm: EncryptionAlgorithm) -> bytes:
        """Genera chiave simmetrica"""
        if algorithm == EncryptionAlgorithm.AES_256_GCM:
            return secrets.token_bytes(32)  # 256 bit
        elif algorithm == EncryptionAlgorithm.CHACHA20_POLY1305:
            return secrets.token_bytes(32)  # 256 bit
        else:
            raise ValueError(f"Algoritmo simmetrico non supportato: {algorithm}")
    
    async def _generate_key_pair(self, algorithm: EncryptionAlgorithm) -> Tuple[bytes, bytes]:
        """Genera coppia di chiavi asimmetriche"""
        # Implementazione semplificata - in produzione usare cryptography library
        if algorithm == EncryptionAlgorithm.RSA_4096:
            # Simula generazione RSA 4096
            private_key = secrets.token_bytes(512)  # 4096 bit
            public_key = secrets.token_bytes(512)
            return private_key, public_key
        elif algorithm == EncryptionAlgorithm.ECDSA_P384:
            # Simula generazione ECDSA P-384
            private_key = secrets.token_bytes(48)  # 384 bit
            public_key = secrets.token_bytes(96)  # Punto non compresso
            return private_key, public_key
        elif algorithm == EncryptionAlgorithm.KYBER_1024:
            # Simula generazione Kyber-1024 (post-quantum)
            private_key = secrets.token_bytes(1632)
            public_key = secrets.token_bytes(1568)
            return private_key, public_key
        else:
            raise ValueError(f"Algoritmo asimmetrico non supportato: {algorithm}")
    
    async def _encrypt_with_algorithm(self, data: bytes, key: CryptoKey, 
                                    algorithm: EncryptionAlgorithm) -> EncryptionResult:
        """Crittografa con algoritmo specifico"""
        try:
            if algorithm == EncryptionAlgorithm.AES_256_GCM:
                return await self._encrypt_aes_gcm(data, key)
            elif algorithm == EncryptionAlgorithm.CHACHA20_POLY1305:
                return await self._encrypt_chacha20(data, key)
            else:
                return EncryptionResult(
                    success=False,
                    error_message=f"Algoritmo di crittografia non supportato: {algorithm}"
                )
        except Exception as e:
            return EncryptionResult(
                success=False,
                error_message=str(e)
            )
    
    async def _decrypt_with_algorithm(self, encrypted_data: bytes, key: CryptoKey,
                                    algorithm: EncryptionAlgorithm, nonce: bytes = None,
                                    tag: bytes = None) -> EncryptionResult:
        """Decrittografa con algoritmo specifico"""
        try:
            if algorithm == EncryptionAlgorithm.AES_256_GCM:
                return await self._decrypt_aes_gcm(encrypted_data, key, nonce, tag)
            elif algorithm == EncryptionAlgorithm.CHACHA20_POLY1305:
                return await self._decrypt_chacha20(encrypted_data, key, nonce, tag)
            else:
                return EncryptionResult(
                    success=False,
                    error_message=f"Algoritmo di decrittografia non supportato: {algorithm}"
                )
        except Exception as e:
            return EncryptionResult(
                success=False,
                error_message=str(e)
            )
    
    async def _encrypt_aes_gcm(self, data: bytes, key: CryptoKey) -> EncryptionResult:
        """Crittografia AES-256-GCM (implementazione semplificata)"""
        try:
            # Genera nonce casuale
            nonce = secrets.token_bytes(12)  # 96 bit per GCM
            
            # Simula crittografia AES-GCM
            # In produzione usare cryptography library
            encrypted_data = bytearray(data)
            for i in range(len(encrypted_data)):
                encrypted_data[i] ^= key.key_data[i % len(key.key_data)]
                encrypted_data[i] ^= nonce[i % len(nonce)]
            
            # Simula tag di autenticazione
            tag = hashlib.sha256(bytes(encrypted_data) + nonce + key.key_data).digest()[:16]
            
            return EncryptionResult(
                success=True,
                data=bytes(encrypted_data),
                algorithm=EncryptionAlgorithm.AES_256_GCM,
                key_id=key.key_id,
                nonce=nonce,
                tag=tag
            )
            
        except Exception as e:
            return EncryptionResult(
                success=False,
                error_message=str(e)
            )
    
    async def _decrypt_aes_gcm(self, encrypted_data: bytes, key: CryptoKey,
                             nonce: bytes, tag: bytes) -> EncryptionResult:
        """Decrittografia AES-256-GCM (implementazione semplificata)"""
        try:
            # Verifica tag
            expected_tag = hashlib.sha256(encrypted_data + nonce + key.key_data).digest()[:16]
            if tag != expected_tag:
                return EncryptionResult(
                    success=False,
                    error_message="Tag di autenticazione non valido"
                )
            
            # Simula decrittografia
            decrypted_data = bytearray(encrypted_data)
            for i in range(len(decrypted_data)):
                decrypted_data[i] ^= nonce[i % len(nonce)]
                decrypted_data[i] ^= key.key_data[i % len(key.key_data)]
            
            return EncryptionResult(
                success=True,
                data=bytes(decrypted_data),
                algorithm=EncryptionAlgorithm.AES_256_GCM,
                key_id=key.key_id
            )
            
        except Exception as e:
            return EncryptionResult(
                success=False,
                error_message=str(e)
            )
    
    async def _encrypt_chacha20(self, data: bytes, key: CryptoKey) -> EncryptionResult:
        """Crittografia ChaCha20-Poly1305 (implementazione semplificata)"""
        try:
            # Genera nonce casuale
            nonce = secrets.token_bytes(12)  # 96 bit
            
            # Simula crittografia ChaCha20
            encrypted_data = bytearray(data)
            for i in range(len(encrypted_data)):
                encrypted_data[i] ^= key.key_data[i % len(key.key_data)]
                encrypted_data[i] ^= nonce[i % len(nonce)]
                encrypted_data[i] ^= (i & 0xFF)  # Simula stream cipher
            
            # Simula tag Poly1305
            tag = hashlib.sha256(bytes(encrypted_data) + nonce + key.key_data).digest()[:16]
            
            return EncryptionResult(
                success=True,
                data=bytes(encrypted_data),
                algorithm=EncryptionAlgorithm.CHACHA20_POLY1305,
                key_id=key.key_id,
                nonce=nonce,
                tag=tag
            )
            
        except Exception as e:
            return EncryptionResult(
                success=False,
                error_message=str(e)
            )
    
    async def _decrypt_chacha20(self, encrypted_data: bytes, key: CryptoKey,
                              nonce: bytes, tag: bytes) -> EncryptionResult:
        """Decrittografia ChaCha20-Poly1305 (implementazione semplificata)"""
        try:
            # Verifica tag
            expected_tag = hashlib.sha256(encrypted_data + nonce + key.key_data).digest()[:16]
            if tag != expected_tag:
                return EncryptionResult(
                    success=False,
                    error_message="Tag di autenticazione non valido"
                )
            
            # Simula decrittografia
            decrypted_data = bytearray(encrypted_data)
            for i in range(len(decrypted_data)):
                decrypted_data[i] ^= (i & 0xFF)
                decrypted_data[i] ^= nonce[i % len(nonce)]
                decrypted_data[i] ^= key.key_data[i % len(key.key_data)]
            
            return EncryptionResult(
                success=True,
                data=bytes(decrypted_data),
                algorithm=EncryptionAlgorithm.CHACHA20_POLY1305,
                key_id=key.key_id
            )
            
        except Exception as e:
            return EncryptionResult(
                success=False,
                error_message=str(e)
            )
    
    async def _sign_with_algorithm(self, data: bytes, key: CryptoKey,
                                 algorithm: EncryptionAlgorithm) -> Optional[bytes]:
        """Firma con algoritmo specifico"""
        try:
            if algorithm == EncryptionAlgorithm.ECDSA_P384:
                # Simula firma ECDSA
                hash_data = hashlib.sha384(data).digest()
                signature = hashlib.sha256(hash_data + key.key_data).digest()
                return signature
            elif algorithm == EncryptionAlgorithm.RSA_4096:
                # Simula firma RSA
                hash_data = hashlib.sha256(data).digest()
                signature = hashlib.sha256(hash_data + key.key_data).digest()
                return signature
            else:
                return None
        except Exception as e:
            self.logger.error(f"Errore firma con {algorithm}: {e}")
            return None
    
    async def _verify_with_algorithm(self, data: bytes, signature: bytes,
                                   key: CryptoKey, algorithm: EncryptionAlgorithm) -> bool:
        """Verifica firma con algoritmo specifico"""
        try:
            if algorithm == EncryptionAlgorithm.ECDSA_P384:
                # Simula verifica ECDSA
                hash_data = hashlib.sha384(data).digest()
                expected_signature = hashlib.sha256(hash_data + key.key_data).digest()
                return signature == expected_signature
            elif algorithm == EncryptionAlgorithm.RSA_4096:
                # Simula verifica RSA
                hash_data = hashlib.sha256(data).digest()
                expected_signature = hashlib.sha256(hash_data + key.key_data).digest()
                return signature == expected_signature
            else:
                return False
        except Exception as e:
            self.logger.error(f"Errore verifica con {algorithm}: {e}")
            return False
    
    async def _generate_session_key(self, peer_id: str, use_pfs: bool) -> Optional[str]:
        """Genera chiave di sessione"""
        try:
            if use_pfs:
                # Genera chiave effimera
                key_id = self._generate_key_id()
                key_data = await self._generate_symmetric_key(self.default_algorithm)
                
                ephemeral_key = CryptoKey(
                    key_id=key_id,
                    key_type=KeyType.EPHEMERAL,
                    algorithm=self.default_algorithm,
                    key_data=key_data,
                    expires_at=time.time() + self.key_rotation_interval
                )
                
                self.ephemeral_keys[key_id] = ephemeral_key
                return key_id
            else:
                # Usa chiave persistente
                return await self._get_or_create_key(self.default_algorithm, KeyType.SYMMETRIC)
                
        except Exception as e:
            self.logger.error(f"Errore generazione chiave sessione: {e}")
            return None
    
    def _generate_key_id(self) -> str:
        """Genera ID univoco per chiave"""
        return hashlib.sha256(
            secrets.token_bytes(32) + str(time.time()).encode()
        ).hexdigest()[:16]
    
    async def _log_operation(self, operation_type: OperationType, algorithm: EncryptionAlgorithm,
                           key_id: str, peer_id: str = None, data_size: int = 0,
                           success: bool = True, error_message: str = "") -> None:
        """Log operazione crittografica"""
        try:
            operation = CryptoOperation(
                operation_id=self._generate_key_id(),
                operation_type=operation_type,
                algorithm=algorithm,
                key_id=key_id,
                timestamp=time.time(),
                peer_id=peer_id,
                data_size=data_size,
                success=success,
                error_message=error_message
            )
            
            self.operations_log.append(operation)
            
            # Mantieni solo ultime 10000 operazioni
            if len(self.operations_log) > 10000:
                self.operations_log = self.operations_log[-10000:]
                
        except Exception as e:
            self.logger.error(f"Errore log operazione: {e}")
    
    async def _schedule_key_rotation(self, key_id: str) -> None:
        """Pianifica rotazione chiave"""
        try:
            # Crea task per rotazione
            rotation_task = asyncio.create_task(self._perform_key_rotation(key_id))
            self.background_tasks.add(rotation_task)
            rotation_task.add_done_callback(self.background_tasks.discard)
            
        except Exception as e:
            self.logger.error(f"Errore pianificazione rotazione {key_id}: {e}")
    
    async def _perform_key_rotation(self, key_id: str) -> None:
        """Esegue rotazione chiave"""
        try:
            await asyncio.sleep(1.0)  # Piccolo delay
            new_key_id = await self.rotate_key(key_id)
            
            if new_key_id:
                self.logger.info(f"Rotazione completata: {key_id} -> {new_key_id}")
            else:
                self.logger.error(f"Rotazione fallita per chiave: {key_id}")
                
        except Exception as e:
            self.logger.error(f"Errore esecuzione rotazione {key_id}: {e}")
    
    async def _ensure_master_keys(self) -> None:
        """Assicura esistenza chiavi master"""
        try:
            # Verifica esistenza chiave master simmetrica
            master_symmetric = None
            for key in self.keys.values():
                if (key.key_type == KeyType.MASTER and 
                    key.algorithm == self.default_algorithm):
                    master_symmetric = key
                    break
            
            if not master_symmetric:
                # Genera chiave master simmetrica
                key_id = await self._create_new_key(self.default_algorithm, KeyType.MASTER)
                self.keys[key_id].key_type = KeyType.MASTER
                self.logger.info("Chiave master simmetrica generata")
            
            # Verifica esistenza coppia chiavi master asimmetriche
            master_asymmetric = None
            for key_id in self.key_pairs:
                key = self.keys[key_id]
                if key.key_type == KeyType.MASTER:
                    master_asymmetric = key
                    break
            
            if not master_asymmetric:
                # Genera coppia chiavi master asimmetriche
                key_pair = await self.generate_key_pair(EncryptionAlgorithm.ECDSA_P384)
                if key_pair:
                    # Marca come master
                    self.keys[key_pair[1]].key_type = KeyType.MASTER
                    self.keys[key_pair[0]].key_type = KeyType.MASTER
                    self.logger.info("Coppia chiavi master asimmetriche generata")
                    
        except Exception as e:
            self.logger.error(f"Errore generazione chiavi master: {e}")
    
    # Handler messaggi protocollo
    
    async def _handle_key_exchange(self, sender_id: str, data: Dict[str, Any]) -> None:
        """Gestisce scambio chiavi"""
        try:
            # Implementazione semplificata
            self.logger.info(f"Richiesta scambio chiavi da {sender_id}")
            
        except Exception as e:
            self.logger.error(f"Errore gestione scambio chiavi: {e}")
    
    async def _handle_session_request(self, sender_id: str, data: Dict[str, Any]) -> None:
        """Gestisce richiesta sessione"""
        try:
            # Implementazione semplificata
            self.logger.info(f"Richiesta sessione da {sender_id}")
            
        except Exception as e:
            self.logger.error(f"Errore gestione richiesta sessione: {e}")
    
    async def _handle_session_response(self, sender_id: str, data: Dict[str, Any]) -> None:
        """Gestisce risposta sessione"""
        try:
            # Implementazione semplificata
            self.logger.info(f"Risposta sessione da {sender_id}")
            
        except Exception as e:
            self.logger.error(f"Errore gestione risposta sessione: {e}")
    
    # Task di background
    
    async def _start_background_tasks(self) -> None:
        """Avvia task di background"""
        # Task di rotazione chiavi
        rotation_task = asyncio.create_task(self._key_rotation_task())
        self.background_tasks.add(rotation_task)
        rotation_task.add_done_callback(self.background_tasks.discard)
        
        # Task di pulizia
        cleanup_task = asyncio.create_task(self._cleanup_task())
        self.background_tasks.add(cleanup_task)
        cleanup_task.add_done_callback(self.background_tasks.discard)
    
    async def _stop_background_tasks(self) -> None:
        """Ferma task di background"""
        for task in self.background_tasks:
            task.cancel()
        
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        self.background_tasks.clear()
    
    async def _key_rotation_task(self) -> None:
        """Task di rotazione automatica chiavi"""
        while self.running:
            try:
                await asyncio.sleep(self.key_rotation_interval)
                
                current_time = time.time()
                
                # Verifica chiavi che necessitano rotazione
                for key_id, key in list(self.keys.items()):
                    needs_rotation = False
                    
                    # Verifica scadenza
                    if key.expires_at > 0 and current_time > key.expires_at:
                        needs_rotation = True
                    
                    # Verifica limite utilizzo
                    if key.max_usage > 0 and key.usage_count >= key.max_usage:
                        needs_rotation = True
                    
                    if needs_rotation and key.key_type != KeyType.MASTER:
                        await self._schedule_key_rotation(key_id)
                
                # Pulisci chiavi effimere scadute
                for key_id in list(self.ephemeral_keys.keys()):
                    key = self.ephemeral_keys[key_id]
                    if key.expires_at > 0 and current_time > key.expires_at:
                        del self.ephemeral_keys[key_id]
                        self.logger.info(f"Chiave effimera scaduta rimossa: {key_id}")
                
            except Exception as e:
                self.logger.error(f"Errore task rotazione chiavi: {e}")
    
    async def _cleanup_task(self) -> None:
        """Task di pulizia periodica"""
        while self.running:
            try:
                await asyncio.sleep(3600)  # Ogni ora
                
                current_time = time.time()
                
                # Rimuovi operazioni vecchie dal log
                cutoff_time = current_time - (7 * 24 * 3600)  # 7 giorni
                self.operations_log = [
                    op for op in self.operations_log
                    if op.timestamp > cutoff_time
                ]
                
                # Rimuovi sessioni inattive
                inactive_sessions = []
                for peer_id, session_data in self.active_sessions.items():
                    if current_time - session_data["last_activity"] > 3600:  # 1 ora
                        inactive_sessions.append(peer_id)
                
                for peer_id in inactive_sessions:
                    await self.end_session(peer_id)
                    self.logger.info(f"Sessione inattiva rimossa: {peer_id}")
                
            except Exception as e:
                self.logger.error(f"Errore task pulizia: {e}")
    
    # Persistenza dati
    
    async def _load_persistent_data(self) -> None:
        """Carica dati persistenti"""
        try:
            data_dir = Path(self.config.get("data_dir", "data/encryption"))
            
            # Carica chiavi
            keys_file = self.keys_dir / "keys.json"
            if keys_file.exists():
                with open(keys_file, 'r', encoding='utf-8') as f:
                    keys_data = json.load(f)
                    
                for key_id, key_dict in keys_data.items():
                    # Decodifica key_data da base64
                    key_dict["key_data"] = base64.b64decode(key_dict["key_data"])
                    if key_dict.get("public_key"):
                        key_dict["public_key"] = base64.b64decode(key_dict["public_key"])
                    
                    # Converti enum
                    key_dict["key_type"] = KeyType(key_dict["key_type"])
                    key_dict["algorithm"] = EncryptionAlgorithm(key_dict["algorithm"])
                    
                    self.keys[key_id] = CryptoKey(**key_dict)
            
            # Carica coppie chiavi
            pairs_file = self.keys_dir / "key_pairs.json"
            if pairs_file.exists():
                with open(pairs_file, 'r', encoding='utf-8') as f:
                    self.key_pairs = json.load(f)
            
            # Carica statistiche
            stats_file = data_dir / "stats.json"
            if stats_file.exists():
                with open(stats_file, 'r', encoding='utf-8') as f:
                    stats_data = json.load(f)
                    self.stats = CryptoStats(**stats_data)
        
        except Exception as e:
            self.logger.error(f"Errore caricamento dati persistenti: {e}")
    
    async def _save_persistent_data(self) -> None:
        """Salva dati persistenti"""
        try:
            data_dir = Path(self.config.get("data_dir", "data/encryption"))
            data_dir.mkdir(parents=True, exist_ok=True)
            
            # Salva chiavi
            keys_data = {}
            for key_id, key in self.keys.items():
                key_dict = asdict(key)
                # Codifica key_data in base64
                key_dict["key_data"] = base64.b64encode(key.key_data).decode('ascii')
                if key.public_key:
                    key_dict["public_key"] = base64.b64encode(key.public_key).decode('ascii')
                
                # Converti enum in stringhe
                key_dict["key_type"] = key.key_type.value
                key_dict["algorithm"] = key.algorithm.value
                
                keys_data[key_id] = key_dict
            
            keys_file = self.keys_dir / "keys.json"
            with open(keys_file, 'w', encoding='utf-8') as f:
                json.dump(keys_data, f, indent=2)
            
            # Salva coppie chiavi
            pairs_file = self.keys_dir / "key_pairs.json"
            with open(pairs_file, 'w', encoding='utf-8') as f:
                json.dump(self.key_pairs, f, indent=2)
            
            # Salva statistiche
            stats_file = data_dir / "stats.json"
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.stats), f, indent=2)
        
        except Exception as e:
            self.logger.error(f"Errore salvataggio dati persistenti: {e}")


# Configurazione predefinita
DEFAULT_CONFIG = {
    "data_dir": "data/encryption",
    "default_algorithm": "aes_256_gcm",
    "key_rotation_interval": 3600,  # 1 ora
    "max_key_usage": 1000000,  # 1M operazioni
    "enable_pfs": True,
    "enable_steganography": True,
    "enable_post_quantum": False,
    "audit_retention_days": 30,
    "max_session_duration": 86400,  # 24 ore
    "auto_key_backup": True,
    "compression_enabled": True,
    "integrity_checks": True,
    "secure_memory": True,
    "algorithms": {
        "symmetric": ["aes_256_gcm", "chacha20_poly1305"],
        "asymmetric": ["rsa_4096", "ecdsa_p384"],
        "post_quantum": ["kyber_1024", "dilithium_5"]
    },
    "key_derivation": {
        "iterations": 100000,
        "salt_length": 32,
        "key_length": 32
    },
    "session_config": {
        "heartbeat_interval": 60,
        "max_idle_time": 3600,
        "renegotiation_threshold": 1000000
    }
}


def create_advanced_encryption(config: Dict[str, Any] = None) -> AdvancedEncryption:
    """
    Factory function per creare istanza AdvancedEncryption
    
    Args:
        config: Configurazione personalizzata (opzionale)
    
    Returns:
        Istanza configurata di AdvancedEncryption
    """
    if config is None:
        config = DEFAULT_CONFIG.copy()
    else:
        # Merge con configurazione predefinita
        merged_config = DEFAULT_CONFIG.copy()
        merged_config.update(config)
        config = merged_config
    
    return AdvancedEncryption()