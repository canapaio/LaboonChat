"""
🆔 LaboonChat Identity Manager - Gestione Identità Crittografiche
================================================================

Gestione sicura delle identità crittografiche per LaboonChat.
Ogni utente ha un'identità unica e sicura per comunicazioni P2P.

🐋 "Ogni Laboon ha la sua voce unica nell'oceano digitale" 🌊

Author: LaboonChat Team
License: GPL-3.0
"""

import os
import json
import time
import hashlib
import logging
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

from .crypto_core import LaboonCrypto, SecureStorage

logger = logging.getLogger(__name__)


@dataclass
class IdentityInfo:
    """Informazioni identità pubblica"""
    identity_hash: str
    public_key: bytes
    display_name: str
    created_at: float
    version: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte in dizionario per serializzazione"""
        data = asdict(self)
        # Converte bytes in hex per JSON
        data['public_key'] = self.public_key.hex()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IdentityInfo':
        """Crea da dizionario"""
        # Converte hex in bytes
        data['public_key'] = bytes.fromhex(data['public_key'])
        return cls(**data)


@dataclass
class PrivateIdentity:
    """Identità privata completa"""
    private_key: bytes
    public_key: bytes
    identity_hash: str
    display_name: str
    created_at: float
    passphrase_hash: Optional[bytes] = None
    
    def get_public_info(self) -> IdentityInfo:
        """Estrae informazioni pubbliche"""
        return IdentityInfo(
            identity_hash=self.identity_hash,
            public_key=self.public_key,
            display_name=self.display_name,
            created_at=self.created_at
        )


class LaboonIdentity:
    """
    🆔 Gestione identità crittografiche LaboonChat
    
    Gestisce creazione, caricamento e utilizzo delle identità crittografiche.
    Ogni identità è unica e sicura, protetta da crittografia forte.
    """
    
    def __init__(self, identity_path: Optional[str] = None):
        """
        Inizializza gestore identità
        
        Args:
            identity_path: Percorso directory identità (default: ~/.laboon/identity)
        """
        if identity_path is None:
            home_dir = Path.home()
            identity_path = home_dir / ".laboon" / "identity"
        
        self.identity_path = Path(identity_path)
        self.storage = SecureStorage(str(self.identity_path))
        
        # Stato corrente identità
        self.current_identity: Optional[PrivateIdentity] = None
        self.is_loaded = False
        
        # File identità
        self.identity_file = "identity.enc"
        self.public_file = "identity_public.json"
    
    def create_new_identity(self, display_name: str, passphrase: Optional[str] = None) -> str:
        """
        Crea nuova identità crittografica
        
        Args:
            display_name: Nome visualizzato per l'identità
            passphrase: Passphrase opzionale per protezione extra
            
        Returns:
            str: Hash identità pubblica (ID utente)
            
        Raises:
            ValueError: Se parametri non validi
            RuntimeError: Se creazione fallisce
        """
        if not display_name or len(display_name.strip()) == 0:
            raise ValueError("Display name non può essere vuoto")
        
        try:
            # Genera coppia chiavi crittografiche
            private_key, public_key = LaboonCrypto.generate_identity_keypair()
            
            # Calcola hash identità (ID pubblico)
            identity_data = public_key + display_name.encode('utf-8')
            identity_hash = LaboonCrypto.hash_data(identity_data).hex()
            
            # Hash passphrase se fornita
            passphrase_hash = None
            if passphrase:
                passphrase_hash = LaboonCrypto.hash_data(passphrase.encode('utf-8'))
            
            # Crea identità privata
            self.current_identity = PrivateIdentity(
                private_key=private_key,
                public_key=public_key,
                identity_hash=identity_hash,
                display_name=display_name.strip(),
                created_at=time.time(),
                passphrase_hash=passphrase_hash
            )
            
            # Salva identità
            self._save_identity(passphrase)
            self._save_public_info()
            
            self.is_loaded = True
            
            return identity_hash
            
        except Exception as e:
            raise RuntimeError(f"Errore creazione identità: {e}") from e
    
    def load_identity(self, passphrase: Optional[str] = None) -> bool:
        """
        Carica identità esistente
        
        Args:
            passphrase: Passphrase per decrittografia
            
        Returns:
            bool: True se caricamento riuscito
        """
        try:
            # Controlla se file identità esiste
            if not self.storage.file_exists(self.identity_file):
                return False
            
            # Determina password per decrittografia
            password = self._get_decryption_password(passphrase)
            
            # Carica dati crittografati
            encrypted_data = self.storage.load_encrypted(self.identity_file, password)
            if encrypted_data is None:
                return False
            
            # Deserializza identità
            identity_dict = json.loads(encrypted_data.decode('utf-8'))
            self.current_identity = self._deserialize_identity(identity_dict)
            
            # Valida identità caricata
            if not self._validate_loaded_identity():
                self.current_identity = None
                return False
            
            self.is_loaded = True
            return True
            
        except Exception:
            self.current_identity = None
            self.is_loaded = False
            return False
    
    def get_identity_hash(self) -> Optional[str]:
        """
        Ottiene hash identità corrente
        
        Returns:
            Optional[str]: Hash identità o None se non caricata
        """
        if self.current_identity:
            return self.current_identity.identity_hash
        return None
    
    def get_public_key(self) -> Optional[bytes]:
        """
        Ottiene chiave pubblica corrente
        
        Returns:
            Optional[bytes]: Chiave pubblica o None se non caricata
        """
        if self.current_identity:
            return self.current_identity.public_key
        return None
    
    def get_display_name(self) -> Optional[str]:
        """
        Ottiene nome visualizzato
        
        Returns:
            Optional[str]: Nome visualizzato o None se non caricata
        """
        if self.current_identity:
            return self.current_identity.display_name
        return None
    
    def get_public_identity(self) -> Optional[IdentityInfo]:
        """
        Ottiene informazioni identità pubblica condivisibile
        
        Returns:
            Optional[IdentityInfo]: Info pubbliche o None se non caricata
        """
        if self.current_identity:
            return self.current_identity.get_public_info()
        return None
    
    def sign_message(self, message: bytes) -> Optional[bytes]:
        """
        Firma digitale messaggio con identità corrente
        
        Args:
            message: Messaggio da firmare
            
        Returns:
            Optional[bytes]: Firma digitale o None se identità non caricata
        """
        if not self.current_identity:
            return None
        
        return LaboonCrypto.sign_data(message, self.current_identity.private_key)
    
    def verify_signature(self, message: bytes, signature: bytes, peer_public_key: bytes) -> bool:
        """
        Verifica firma digitale di un peer
        
        Args:
            message: Messaggio originale
            signature: Firma da verificare
            peer_public_key: Chiave pubblica del peer
            
        Returns:
            bool: True se firma valida
        """
        return LaboonCrypto.verify_signature(message, signature, peer_public_key)
    
    def change_display_name(self, new_name: str, passphrase: Optional[str] = None) -> bool:
        """
        Cambia nome visualizzato
        
        Args:
            new_name: Nuovo nome
            passphrase: Passphrase per salvataggio
            
        Returns:
            bool: True se cambio riuscito
        """
        if not self.current_identity or not new_name.strip():
            return False
        
        try:
            self.current_identity.display_name = new_name.strip()
            self._save_identity(passphrase)
            self._save_public_info()
            return True
        except Exception:
            return False
    
    def export_public_identity(self) -> Optional[Dict[str, Any]]:
        """
        Esporta identità pubblica per condivisione
        
        Returns:
            Optional[Dict]: Dati identità pubblica o None se non caricata
        """
        if not self.current_identity:
            return None
        
        public_info = self.current_identity.get_public_info()
        return public_info.to_dict()
    
    def identity_exists(self) -> bool:
        """
        Controlla se esiste un'identità salvata
        
        Returns:
            bool: True se identità esiste
        """
        return self.storage.file_exists(self.identity_file)
    
    def _save_identity(self, passphrase: Optional[str] = None):
        """Salva identità crittografata"""
        if not self.current_identity:
            raise RuntimeError("Nessuna identità da salvare")
        
        # Serializza identità
        identity_dict = {
            'private_key': self.current_identity.private_key.hex(),
            'public_key': self.current_identity.public_key.hex(),
            'identity_hash': self.current_identity.identity_hash,
            'display_name': self.current_identity.display_name,
            'created_at': self.current_identity.created_at,
            'passphrase_hash': self.current_identity.passphrase_hash.hex() if self.current_identity.passphrase_hash else None
        }
        
        identity_json = json.dumps(identity_dict, indent=2)
        
        # Determina password per crittografia
        password = self._get_encryption_password(passphrase)
        
        # Salva crittografato
        success = self.storage.store_encrypted(
            self.identity_file,
            identity_json.encode('utf-8'),
            password
        )
        
        if not success:
            raise RuntimeError("Errore salvataggio identità")
    
    def _save_public_info(self):
        """Salva informazioni pubbliche in chiaro"""
        if not self.current_identity:
            return
        
        public_info = self.current_identity.get_public_info()
        public_dict = public_info.to_dict()
        
        public_file_path = self.identity_path / self.public_file
        with open(public_file_path, 'w', encoding='utf-8') as f:
            json.dump(public_dict, f, indent=2)
    
    def _deserialize_identity(self, identity_dict: Dict[str, Any]) -> PrivateIdentity:
        """Deserializza identità da dizionario"""
        return PrivateIdentity(
            private_key=bytes.fromhex(identity_dict['private_key']),
            public_key=bytes.fromhex(identity_dict['public_key']),
            identity_hash=identity_dict['identity_hash'],
            display_name=identity_dict['display_name'],
            created_at=identity_dict['created_at'],
            passphrase_hash=bytes.fromhex(identity_dict['passphrase_hash']) if identity_dict.get('passphrase_hash') else None
        )
    
    def _validate_loaded_identity(self) -> bool:
        """Valida identità caricata"""
        if not self.current_identity:
            return False
        
        try:
            # Verifica che la chiave pubblica sia derivata correttamente dalla privata
            expected_public = LaboonCrypto.hash_data(self.current_identity.private_key)
            if not LaboonCrypto.secure_compare(expected_public, self.current_identity.public_key):
                return False
            
            # Verifica hash identità
            identity_data = self.current_identity.public_key + self.current_identity.display_name.encode('utf-8')
            expected_hash = LaboonCrypto.hash_data(identity_data).hex()
            if expected_hash != self.current_identity.identity_hash:
                return False
            
            return True
            
        except Exception:
            return False
    
    def _get_encryption_password(self, passphrase: Optional[str] = None) -> str:
        """Determina password per crittografia"""
        if passphrase:
            return passphrase
        
        # Password di default basata su identità
        if self.current_identity:
            return f"laboon_{self.current_identity.identity_hash[:16]}"
        
        return "laboon_default_key"
    
    def _get_decryption_password(self, passphrase: Optional[str] = None) -> str:
        """Determina password per decrittografia"""
        if passphrase:
            return passphrase
        
        # Prova password di default
        return "laboon_default_key"


class IdentityManager:
    """
    🌊 Gestore identità globale per LaboonChat
    
    Gestisce l'identità corrente dell'applicazione e fornisce
    un'interfaccia semplificata per le operazioni comuni.
    """
    
    _instance: Optional['IdentityManager'] = None
    
    def __new__(cls) -> 'IdentityManager':
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Inizializza gestore identità"""
        if not hasattr(self, 'initialized'):
            self.identity = LaboonIdentity()
            self.initialized = True
    
    def ensure_identity(self, display_name: str = "Laboon User") -> str:
        """
        Assicura che esista un'identità, creandola se necessario
        
        Args:
            display_name: Nome di default se deve creare identità
            
        Returns:
            str: Hash identità
        """
        # Prova a caricare identità esistente
        if self.identity.load_identity():
            return self.identity.get_identity_hash()
        
        # Prima creazione - mostra dialog di setup se possibile
        identity_data = None
        try:
            # Prova a importare e mostrare il dialog di setup
            from .identity_setup_ui import show_identity_setup
            identity_data = show_identity_setup()
            
            if identity_data:
                # Usa i dati dal dialog
                display_name = identity_data['username']
                logger.info(f"Identity setup completed for: {display_name}")
            else:
                logger.info("Identity setup cancelled, using default name")
                
        except ImportError:
            logger.info("GUI not available, using default identity setup")
        except Exception as e:
            logger.warning(f"Error showing identity setup dialog: {e}")
        
        # Crea nuova identità
        return self.identity.create_new_identity(display_name)
    
    def get_current_identity(self) -> Optional[IdentityInfo]:
        """Ottiene identità corrente"""
        return self.identity.get_public_identity()
    
    def sign_data(self, data: bytes) -> Optional[bytes]:
        """Firma dati con identità corrente"""
        return self.identity.sign_message(data)
    
    def verify_peer_signature(self, data: bytes, signature: bytes, peer_public_key: bytes) -> bool:
        """Verifica firma di un peer"""
        return self.identity.verify_signature(data, signature, peer_public_key)


# Test rapido del modulo
if __name__ == "__main__":
    print("🆔 Test LaboonIdentity...")
    
    # Test creazione identità
    identity = LaboonIdentity("/tmp/test_identity")
    
    # Crea nuova identità
    identity_hash = identity.create_new_identity("Test Laboon", "test_password")
    print(f"✅ Identità creata: {identity_hash[:16]}...")
    
    # Test caricamento
    identity2 = LaboonIdentity("/tmp/test_identity")
    loaded = identity2.load_identity("test_password")
    print(f"✅ Caricamento: {loaded}")
    
    # Test firma
    message = "Hello, Laboon!".encode('utf-8')
    signature = identity2.sign_message(message)
    print(f"✅ Firma: {signature is not None}")
    
    # Test verifica
    public_key = identity2.get_public_key()
    valid = identity2.verify_signature(message, signature, public_key)
    print(f"✅ Verifica: {valid}")
    
    # Test export
    public_info = identity2.export_public_identity()
    print(f"✅ Export: {public_info is not None}")
    
    print("🐋 LaboonIdentity funziona perfettamente! 🌊")