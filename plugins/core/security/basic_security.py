"""
Basic Security Module for LaboonChat v2.0

Implements core security functionality including identity management,
encryption, digital signatures, and key management.
"""

import os
import json
import asyncio
from typing import Dict, Any, Optional, List, Tuple, Union
from datetime import datetime, timedelta
from pathlib import Path
import logging

# Import delle interfacce
from laboon_chat2.interfaces.security_interface import (
    ISecurityModule,
    SecurityError,
    IdentityError,
    EncryptionError,
    SignatureError,
    KeyManagementError
)

# Import delle utility
from laboon_chat2.utils.crypto_utils import (
    CryptoUtils,
    KeyPair,
    EncryptedData,
    DigitalSignature
)
from laboon_chat2.utils.logger import setup_plugin_logger


class BasicSecurityModule(ISecurityModule):
    """
    Modulo di sicurezza base per LaboonChat v2.0.
    
    Caratteristiche:
    - Gestione identità con chiavi Ed25519
    - Crittografia simmetrica AES-GCM
    - Firme digitali Ed25519
    - Gestione sicura delle chiavi
    - Autenticazione peer-to-peer
    - Protezione dati sensibili
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inizializza il modulo di sicurezza.
        
        Args:
            config: Configurazione del modulo
        """
        self.config = config or {}
        self.logger = setup_plugin_logger("BasicSecurity")
        self.crypto = CryptoUtils()
        
        # Stato del modulo
        self._initialized = False
        self._identity: Optional[KeyPair] = None
        self._session_keys: Dict[str, bytes] = {}
        self._trusted_peers: Dict[str, Dict[str, Any]] = {}
        self._blacklisted_peers: set = set()
        
        # Configurazioni di default
        self._default_config = {
            "identity_file": "identity.json",
            "trusted_peers_file": "trusted_peers.json",
            "key_rotation_interval": 3600,  # 1 ora
            "max_session_keys": 100,
            "encryption_algorithm": "AES-GCM",
            "signature_algorithm": "Ed25519",
            "auto_save": True,
            "backup_keys": True
        }
        
        # Merge configurazioni
        self._config = {**self._default_config, **self.config}
        
        self.logger.info("BasicSecurityModule inizializzato")
    
    # === Implementazione ISecurityModule ===
    
    async def initialize(self) -> bool:
        """
        Inizializza il modulo di sicurezza.
        
        Returns:
            bool: True se inizializzazione riuscita
        """
        try:
            self.logger.info("Inizializzazione BasicSecurityModule...")
            
            # Crea directory per i dati di sicurezza
            security_dir = Path("security")
            security_dir.mkdir(exist_ok=True)
            
            # Carica o genera identità
            await self._load_or_generate_identity()
            
            # Carica peer fidati
            await self._load_trusted_peers()
            
            # Avvia task di manutenzione
            asyncio.create_task(self._maintenance_task())
            
            self._initialized = True
            self.logger.info("BasicSecurityModule inizializzato con successo")
            return True
            
        except Exception as e:
            self.logger.error(f"Errore inizializzazione: {e}")
            return False
    
    async def cleanup(self) -> None:
        """Cleanup del modulo."""
        try:
            self.logger.info("Cleanup BasicSecurityModule...")
            
            # Salva dati se auto_save abilitato
            if self._config["auto_save"]:
                await self._save_identity()
                await self._save_trusted_peers()
            
            # Pulisci chiavi di sessione
            self._session_keys.clear()
            
            self._initialized = False
            self.logger.info("Cleanup completato")
            
        except Exception as e:
            self.logger.error(f"Errore durante cleanup: {e}")
    
    def get_module_info(self) -> Dict[str, Any]:
        """
        Ottiene informazioni sul modulo.
        
        Returns:
            Dict: Informazioni modulo
        """
        return {
            "name": "BasicSecurityModule",
            "version": "1.0.0",
            "description": "Modulo di sicurezza base con crittografia Ed25519/AES-GCM",
            "author": "LaboonChat Team",
            "capabilities": [
                "identity_management",
                "encryption",
                "digital_signatures",
                "key_management",
                "peer_authentication"
            ],
            "algorithms": {
                "asymmetric": ["Ed25519"],
                "symmetric": ["AES-GCM", "AES-CBC", "ChaCha20"],
                "hash": ["SHA256", "SHA512", "BLAKE2b"]
            },
            "initialized": self._initialized,
            "identity_fingerprint": self._identity.fingerprint if self._identity else None,
            "trusted_peers_count": len(self._trusted_peers),
            "session_keys_count": len(self._session_keys)
        }
    
    # === Gestione Identità ===
    
    async def generate_identity(self, save: bool = True) -> str:
        """
        Genera nuova identità.
        
        Args:
            save: Se salvare l'identità
            
        Returns:
            str: Fingerprint dell'identità
            
        Raises:
            IdentityError: Se generazione fallisce
        """
        try:
            self.logger.info("Generazione nuova identità...")
            
            # Backup identità esistente se richiesto
            if self._identity and self._config["backup_keys"]:
                await self._backup_identity()
            
            # Genera nuova coppia di chiavi
            self._identity = self.crypto.generate_ed25519_keypair()
            
            # Salva se richiesto
            if save:
                await self._save_identity()
            
            self.logger.info(f"Nuova identità generata: {self._identity.fingerprint}")
            return self._identity.fingerprint
            
        except Exception as e:
            raise IdentityError(f"Errore generazione identità: {e}")
    
    async def load_identity(self, identity_data: Dict[str, Any]) -> bool:
        """
        Carica identità da dati.
        
        Args:
            identity_data: Dati identità
            
        Returns:
            bool: True se caricamento riuscito
            
        Raises:
            IdentityError: Se caricamento fallisce
        """
        try:
            # Valida dati
            required_fields = ["public_key", "private_key", "key_type", "fingerprint"]
            if not all(field in identity_data for field in required_fields):
                raise IdentityError("Dati identità incompleti")
            
            # Ricostruisci KeyPair
            self._identity = KeyPair(
                public_key=identity_data["public_key"].encode(),
                private_key=identity_data["private_key"].encode(),
                key_type=identity_data["key_type"],
                created_at=datetime.fromisoformat(identity_data.get("created_at", datetime.now().isoformat())),
                fingerprint=identity_data["fingerprint"]
            )
            
            # Verifica integrità
            calculated_fingerprint = self.crypto.calculate_key_fingerprint(self._identity.public_key)
            if calculated_fingerprint != self._identity.fingerprint:
                raise IdentityError("Fingerprint identità non corrisponde")
            
            self.logger.info(f"Identità caricata: {self._identity.fingerprint}")
            return True
            
        except Exception as e:
            raise IdentityError(f"Errore caricamento identità: {e}")
    
    def get_identity(self) -> Optional[Dict[str, Any]]:
        """
        Ottiene identità corrente.
        
        Returns:
            Optional[Dict]: Dati identità (solo chiave pubblica)
        """
        if not self._identity:
            return None
        
        return {
            "public_key": self._identity.public_key.decode(),
            "key_type": self._identity.key_type,
            "fingerprint": self._identity.fingerprint,
            "created_at": self._identity.created_at.isoformat()
        }
    
    def get_public_key(self) -> Optional[bytes]:
        """
        Ottiene chiave pubblica.
        
        Returns:
            Optional[bytes]: Chiave pubblica
        """
        return self._identity.public_key if self._identity else None
    
    def get_fingerprint(self) -> Optional[str]:
        """
        Ottiene fingerprint identità.
        
        Returns:
            Optional[str]: Fingerprint
        """
        return self._identity.fingerprint if self._identity else None
    
    # === Crittografia ===
    
    async def encrypt_message(
        self,
        message: Union[str, bytes],
        recipient_public_key: Optional[bytes] = None
    ) -> EncryptedData:
        """
        Cripta messaggio.
        
        Args:
            message: Messaggio da crittografare
            recipient_public_key: Chiave pubblica destinatario (opzionale)
            
        Returns:
            EncryptedData: Messaggio crittografato
            
        Raises:
            EncryptionError: Se crittografia fallisce
        """
        try:
            if recipient_public_key:
                # Crittografia asimmetrica
                # Per messaggi lunghi, usa crittografia ibrida
                if len(message) > 200:  # Limite RSA
                    # Genera chiave simmetrica
                    session_key = self.crypto.generate_symmetric_key()
                    
                    # Cripta messaggio con chiave simmetrica
                    encrypted_message = self.crypto.encrypt_symmetric(
                        message,
                        session_key,
                        self._config["encryption_algorithm"]
                    )
                    
                    # Cripta chiave simmetrica con chiave pubblica
                    # Nota: Ed25519 non supporta crittografia, usa solo per firme
                    # Per ora usa solo crittografia simmetrica
                    return encrypted_message
                else:
                    # Per messaggi corti, usa crittografia simmetrica con chiave derivata
                    # Questo è un compromesso per Ed25519
                    session_key = self.crypto.generate_symmetric_key()
                    return self.crypto.encrypt_symmetric(
                        message,
                        session_key,
                        self._config["encryption_algorithm"]
                    )
            else:
                # Crittografia simmetrica con chiave di sessione
                session_key = self.crypto.generate_symmetric_key()
                return self.crypto.encrypt_symmetric(
                    message,
                    session_key,
                    self._config["encryption_algorithm"]
                )
                
        except Exception as e:
            raise EncryptionError(f"Errore crittografia messaggio: {e}")
    
    async def decrypt_message(
        self,
        encrypted_data: EncryptedData,
        session_key: Optional[bytes] = None
    ) -> bytes:
        """
        Decripta messaggio.
        
        Args:
            encrypted_data: Dati crittografati
            session_key: Chiave di sessione (opzionale)
            
        Returns:
            bytes: Messaggio decrittografato
            
        Raises:
            EncryptionError: Se decrittografia fallisce
        """
        try:
            if session_key:
                return self.crypto.decrypt_symmetric(encrypted_data, session_key)
            else:
                # Prova con chiavi di sessione memorizzate
                for key in self._session_keys.values():
                    try:
                        return self.crypto.decrypt_symmetric(encrypted_data, key)
                    except:
                        continue
                
                raise EncryptionError("Nessuna chiave valida per decrittografia")
                
        except Exception as e:
            raise EncryptionError(f"Errore decrittografia messaggio: {e}")
    
    # === Firme Digitali ===
    
    async def sign_message(self, message: Union[str, bytes]) -> DigitalSignature:
        """
        Firma messaggio.
        
        Args:
            message: Messaggio da firmare
            
        Returns:
            DigitalSignature: Firma digitale
            
        Raises:
            SignatureError: Se firma fallisce
        """
        if not self._identity:
            raise SignatureError("Identità non disponibile per firma")
        
        try:
            return self.crypto.sign_data(
                message,
                self._identity.private_key,
                self._config["signature_algorithm"]
            )
            
        except Exception as e:
            raise SignatureError(f"Errore firma messaggio: {e}")
    
    async def verify_signature(
        self,
        message: Union[str, bytes],
        signature: DigitalSignature,
        public_key: bytes
    ) -> bool:
        """
        Verifica firma.
        
        Args:
            message: Messaggio originale
            signature: Firma digitale
            public_key: Chiave pubblica del firmatario
            
        Returns:
            bool: True se firma valida
            
        Raises:
            SignatureError: Se verifica fallisce
        """
        try:
            return self.crypto.verify_signature(message, signature, public_key)
            
        except Exception as e:
            raise SignatureError(f"Errore verifica firma: {e}")
    
    # === Gestione Chiavi ===
    
    async def generate_session_key(self, peer_id: str) -> bytes:
        """
        Genera chiave di sessione.
        
        Args:
            peer_id: ID del peer
            
        Returns:
            bytes: Chiave di sessione
            
        Raises:
            KeyManagementError: Se generazione fallisce
        """
        try:
            # Genera chiave casuale
            session_key = self.crypto.generate_symmetric_key()
            
            # Memorizza chiave
            self._session_keys[peer_id] = session_key
            
            # Limita numero di chiavi
            if len(self._session_keys) > self._config["max_session_keys"]:
                # Rimuovi chiave più vecchia (semplificato)
                oldest_peer = next(iter(self._session_keys))
                del self._session_keys[oldest_peer]
            
            self.logger.debug(f"Chiave di sessione generata per peer {peer_id}")
            return session_key
            
        except Exception as e:
            raise KeyManagementError(f"Errore generazione chiave sessione: {e}")
    
    async def get_session_key(self, peer_id: str) -> Optional[bytes]:
        """
        Ottiene chiave di sessione.
        
        Args:
            peer_id: ID del peer
            
        Returns:
            Optional[bytes]: Chiave di sessione
        """
        return self._session_keys.get(peer_id)
    
    async def revoke_session_key(self, peer_id: str) -> bool:
        """
        Revoca chiave di sessione.
        
        Args:
            peer_id: ID del peer
            
        Returns:
            bool: True se revoca riuscita
        """
        if peer_id in self._session_keys:
            del self._session_keys[peer_id]
            self.logger.debug(f"Chiave di sessione revocata per peer {peer_id}")
            return True
        return False
    
    async def rotate_keys(self) -> bool:
        """
        Ruota chiavi di sicurezza.
        
        Returns:
            bool: True se rotazione riuscita
            
        Raises:
            KeyManagementError: Se rotazione fallisce
        """
        try:
            self.logger.info("Rotazione chiavi di sicurezza...")
            
            # Backup identità corrente
            if self._config["backup_keys"]:
                await self._backup_identity()
            
            # Genera nuova identità
            await self.generate_identity(save=True)
            
            # Pulisci chiavi di sessione
            self._session_keys.clear()
            
            self.logger.info("Rotazione chiavi completata")
            return True
            
        except Exception as e:
            raise KeyManagementError(f"Errore rotazione chiavi: {e}")
    
    # === Funzionalità di Sicurezza ===
    
    async def authenticate_peer(
        self,
        peer_id: str,
        challenge: bytes,
        signature: DigitalSignature,
        public_key: bytes
    ) -> bool:
        """
        Autentica peer.
        
        Args:
            peer_id: ID del peer
            challenge: Challenge di autenticazione
            signature: Firma del challenge
            public_key: Chiave pubblica del peer
            
        Returns:
            bool: True se autenticazione riuscita
        """
        try:
            # Verifica se peer è nella blacklist
            if peer_id in self._blacklisted_peers:
                self.logger.warning(f"Peer {peer_id} in blacklist")
                return False
            
            # Verifica firma del challenge
            is_valid = await self.verify_signature(challenge, signature, public_key)
            
            if is_valid:
                # Aggiungi a peer fidati se non presente
                if peer_id not in self._trusted_peers:
                    await self.add_trusted_peer(peer_id, {
                        "public_key": public_key.decode(),
                        "first_seen": datetime.now().isoformat(),
                        "last_authenticated": datetime.now().isoformat()
                    })
                else:
                    # Aggiorna ultima autenticazione
                    self._trusted_peers[peer_id]["last_authenticated"] = datetime.now().isoformat()
                
                self.logger.info(f"Peer {peer_id} autenticato con successo")
            else:
                self.logger.warning(f"Autenticazione fallita per peer {peer_id}")
            
            return is_valid
            
        except Exception as e:
            self.logger.error(f"Errore autenticazione peer {peer_id}: {e}")
            return False
    
    async def add_trusted_peer(self, peer_id: str, peer_info: Dict[str, Any]) -> bool:
        """
        Aggiunge peer fidato.
        
        Args:
            peer_id: ID del peer
            peer_info: Informazioni del peer
            
        Returns:
            bool: True se aggiunta riuscita
        """
        try:
            self._trusted_peers[peer_id] = {
                **peer_info,
                "added_at": datetime.now().isoformat()
            }
            
            # Salva se auto_save abilitato
            if self._config["auto_save"]:
                await self._save_trusted_peers()
            
            self.logger.info(f"Peer fidato aggiunto: {peer_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Errore aggiunta peer fidato {peer_id}: {e}")
            return False
    
    async def remove_trusted_peer(self, peer_id: str) -> bool:
        """
        Rimuove peer fidato.
        
        Args:
            peer_id: ID del peer
            
        Returns:
            bool: True se rimozione riuscita
        """
        if peer_id in self._trusted_peers:
            del self._trusted_peers[peer_id]
            
            # Salva se auto_save abilitato
            if self._config["auto_save"]:
                await self._save_trusted_peers()
            
            self.logger.info(f"Peer fidato rimosso: {peer_id}")
            return True
        return False
    
    async def is_trusted_peer(self, peer_id: str) -> bool:
        """
        Verifica se peer è fidato.
        
        Args:
            peer_id: ID del peer
            
        Returns:
            bool: True se peer è fidato
        """
        return peer_id in self._trusted_peers and peer_id not in self._blacklisted_peers
    
    async def blacklist_peer(self, peer_id: str, reason: str = "") -> bool:
        """
        Aggiunge peer alla blacklist.
        
        Args:
            peer_id: ID del peer
            reason: Motivo del ban
            
        Returns:
            bool: True se aggiunta riuscita
        """
        self._blacklisted_peers.add(peer_id)
        
        # Rimuovi da peer fidati se presente
        if peer_id in self._trusted_peers:
            del self._trusted_peers[peer_id]
        
        # Revoca chiave di sessione
        await self.revoke_session_key(peer_id)
        
        self.logger.warning(f"Peer {peer_id} aggiunto alla blacklist: {reason}")
        return True
    
    async def unblacklist_peer(self, peer_id: str) -> bool:
        """
        Rimuove peer dalla blacklist.
        
        Args:
            peer_id: ID del peer
            
        Returns:
            bool: True se rimozione riuscita
        """
        if peer_id in self._blacklisted_peers:
            self._blacklisted_peers.remove(peer_id)
            self.logger.info(f"Peer {peer_id} rimosso dalla blacklist")
            return True
        return False
    
    # === Configurazione ===
    
    async def update_config(self, new_config: Dict[str, Any]) -> bool:
        """
        Aggiorna configurazione.
        
        Args:
            new_config: Nuova configurazione
            
        Returns:
            bool: True se aggiornamento riuscito
        """
        try:
            # Valida configurazione
            valid_keys = set(self._default_config.keys())
            invalid_keys = set(new_config.keys()) - valid_keys
            
            if invalid_keys:
                self.logger.warning(f"Chiavi configurazione non valide: {invalid_keys}")
            
            # Aggiorna solo chiavi valide
            for key, value in new_config.items():
                if key in valid_keys:
                    self._config[key] = value
            
            self.logger.info("Configurazione aggiornata")
            return True
            
        except Exception as e:
            self.logger.error(f"Errore aggiornamento configurazione: {e}")
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """
        Ottiene configurazione corrente.
        
        Returns:
            Dict: Configurazione
        """
        return self._config.copy()
    
    # === Metodi Privati ===
    
    async def _load_or_generate_identity(self) -> None:
        """Carica identità esistente o ne genera una nuova."""
        identity_file = Path("security") / self._config["identity_file"]
        
        if identity_file.exists():
            try:
                with open(identity_file, 'r') as f:
                    identity_data = json.load(f)
                await self.load_identity(identity_data)
                self.logger.info("Identità caricata da file")
            except Exception as e:
                self.logger.warning(f"Errore caricamento identità: {e}")
                await self.generate_identity()
        else:
            await self.generate_identity()
    
    async def _save_identity(self) -> None:
        """Salva identità su file."""
        if not self._identity:
            return
        
        identity_file = Path("security") / self._config["identity_file"]
        
        identity_data = {
            "public_key": self._identity.public_key.decode(),
            "private_key": self._identity.private_key.decode(),
            "key_type": self._identity.key_type,
            "fingerprint": self._identity.fingerprint,
            "created_at": self._identity.created_at.isoformat()
        }
        
        with open(identity_file, 'w') as f:
            json.dump(identity_data, f, indent=2)
        
        # Imposta permessi restrittivi (solo su Unix)
        if os.name != 'nt':
            os.chmod(identity_file, 0o600)
    
    async def _backup_identity(self) -> None:
        """Crea backup dell'identità."""
        if not self._identity:
            return
        
        backup_dir = Path("security") / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"identity_backup_{timestamp}.json"
        
        identity_data = {
            "public_key": self._identity.public_key.decode(),
            "private_key": self._identity.private_key.decode(),
            "key_type": self._identity.key_type,
            "fingerprint": self._identity.fingerprint,
            "created_at": self._identity.created_at.isoformat(),
            "backed_up_at": datetime.now().isoformat()
        }
        
        with open(backup_file, 'w') as f:
            json.dump(identity_data, f, indent=2)
        
        self.logger.info(f"Backup identità creato: {backup_file}")
    
    async def _load_trusted_peers(self) -> None:
        """Carica peer fidati da file."""
        peers_file = Path("security") / self._config["trusted_peers_file"]
        
        if peers_file.exists():
            try:
                with open(peers_file, 'r') as f:
                    self._trusted_peers = json.load(f)
                self.logger.info(f"Caricati {len(self._trusted_peers)} peer fidati")
            except Exception as e:
                self.logger.warning(f"Errore caricamento peer fidati: {e}")
                self._trusted_peers = {}
    
    async def _save_trusted_peers(self) -> None:
        """Salva peer fidati su file."""
        peers_file = Path("security") / self._config["trusted_peers_file"]
        
        with open(peers_file, 'w') as f:
            json.dump(self._trusted_peers, f, indent=2)
    
    async def _maintenance_task(self) -> None:
        """Task di manutenzione periodica."""
        while self._initialized:
            try:
                # Rotazione chiavi se abilitata
                rotation_interval = self._config.get("key_rotation_interval", 0)
                if rotation_interval > 0:
                    # Verifica se è tempo di ruotare
                    if self._identity:
                        age = datetime.now() - self._identity.created_at
                        if age.total_seconds() > rotation_interval:
                            await self.rotate_keys()
                
                # Pulizia chiavi di sessione vecchie
                # (implementazione semplificata)
                
                # Attendi prima del prossimo ciclo
                await asyncio.sleep(300)  # 5 minuti
                
            except Exception as e:
                self.logger.error(f"Errore task manutenzione: {e}")
                await asyncio.sleep(60)  # Riprova dopo 1 minuto


# === Factory Function ===

def create_basic_security_module(config: Optional[Dict[str, Any]] = None) -> BasicSecurityModule:
    """
    Crea istanza BasicSecurityModule.
    
    Args:
        config: Configurazione del modulo
        
    Returns:
        BasicSecurityModule: Istanza del modulo
    """
    return BasicSecurityModule(config)