"""
Abstract interface for Security Modules in LaboonChat v2.0

Defines the contract that all security plugins must implement.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Tuple
import asyncio


class ISecurityModule(ABC):
    """
    Interfaccia astratta per moduli di sicurezza esclusivi.
    
    Ogni implementazione di sicurezza deve fornire:
    - Gestione identità crittografiche
    - Crittografia/decrittografia messaggi
    - Firma digitale e verifica
    - Gestione chiavi sicura
    """
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Inizializza il modulo di sicurezza.
        
        Args:
            config: Configurazione specifica del modulo
            
        Returns:
            bool: True se inizializzazione riuscita, False altrimenti
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
    
    # === Identity Management ===
    
    @abstractmethod
    async def create_identity(self, display_name: str, **kwargs) -> str:
        """
        Crea una nuova identità crittografica.
        
        Args:
            display_name: Nome visualizzato per l'identità
            **kwargs: Parametri aggiuntivi specifici dell'implementazione
            
        Returns:
            str: ID univoco dell'identità creata
        """
        pass
    
    @abstractmethod
    async def load_identity(self) -> Optional[Dict[str, Any]]:
        """
        Carica l'identità esistente dal storage.
        
        Returns:
            Optional[Dict]: Dati identità se presente, None altrimenti
        """
        pass
    
    @abstractmethod
    async def get_public_key(self, identity_id: Optional[str] = None) -> str:
        """
        Ottiene la chiave pubblica per un'identità.
        
        Args:
            identity_id: ID identità (None per identità corrente)
            
        Returns:
            str: Chiave pubblica in formato PEM o equivalente
        """
        pass
    
    @abstractmethod
    async def get_identity_info(self) -> Dict[str, Any]:
        """
        Ottiene informazioni sull'identità corrente.
        
        Returns:
            Dict: Informazioni identità (nome, ID, timestamp creazione, etc.)
        """
        pass
    
    # === Message Encryption ===
    
    @abstractmethod
    async def encrypt_message(
        self, 
        message: str, 
        recipient_public_key: str,
        **kwargs
    ) -> bytes:
        """
        Cripta un messaggio per un destinatario specifico.
        
        Args:
            message: Messaggio in chiaro da crittare
            recipient_public_key: Chiave pubblica del destinatario
            **kwargs: Parametri aggiuntivi (algoritmo, padding, etc.)
            
        Returns:
            bytes: Messaggio crittato
        """
        pass
    
    @abstractmethod
    async def decrypt_message(
        self, 
        encrypted_message: bytes, 
        sender_public_key: str,
        **kwargs
    ) -> str:
        """
        Decripta un messaggio ricevuto.
        
        Args:
            encrypted_message: Messaggio crittato
            sender_public_key: Chiave pubblica del mittente
            **kwargs: Parametri aggiuntivi
            
        Returns:
            str: Messaggio in chiaro
            
        Raises:
            DecryptionError: Se decrittazione fallisce
        """
        pass
    
    # === Digital Signatures ===
    
    @abstractmethod
    async def sign_data(self, data: bytes, **kwargs) -> bytes:
        """
        Firma digitalmente dei dati.
        
        Args:
            data: Dati da firmare
            **kwargs: Parametri aggiuntivi (algoritmo hash, etc.)
            
        Returns:
            bytes: Firma digitale
        """
        pass
    
    @abstractmethod
    async def verify_signature(
        self, 
        data: bytes, 
        signature: bytes, 
        public_key: str,
        **kwargs
    ) -> bool:
        """
        Verifica una firma digitale.
        
        Args:
            data: Dati originali
            signature: Firma da verificare
            public_key: Chiave pubblica del firmatario
            **kwargs: Parametri aggiuntivi
            
        Returns:
            bool: True se firma valida, False altrimenti
        """
        pass
    
    # === Key Management ===
    
    @abstractmethod
    async def generate_session_key(self) -> Tuple[bytes, str]:
        """
        Genera una chiave di sessione temporanea.
        
        Returns:
            Tuple[bytes, str]: (chiave_binaria, chiave_base64)
        """
        pass
    
    @abstractmethod
    async def derive_shared_secret(
        self, 
        peer_public_key: str,
        **kwargs
    ) -> bytes:
        """
        Deriva un segreto condiviso usando ECDH o simile.
        
        Args:
            peer_public_key: Chiave pubblica del peer
            **kwargs: Parametri aggiuntivi
            
        Returns:
            bytes: Segreto condiviso derivato
        """
        pass
    
    # === Security Features ===
    
    @abstractmethod
    async def secure_delete(self, data: Any) -> bool:
        """
        Cancellazione sicura di dati sensibili dalla memoria.
        
        Args:
            data: Dati da cancellare in modo sicuro
            
        Returns:
            bool: True se cancellazione riuscita
        """
        pass
    
    @abstractmethod
    async def get_security_level(self) -> str:
        """
        Ottiene il livello di sicurezza del modulo.
        
        Returns:
            str: Livello sicurezza ("basic", "standard", "advanced", "quantum")
        """
        pass
    
    @abstractmethod
    async def validate_peer_identity(
        self, 
        peer_id: str, 
        public_key: str,
        **kwargs
    ) -> bool:
        """
        Valida l'identità di un peer.
        
        Args:
            peer_id: ID del peer
            public_key: Chiave pubblica dichiarata
            **kwargs: Parametri aggiuntivi per validazione
            
        Returns:
            bool: True se identità valida
        """
        pass
    
    # === Configuration ===
    
    @abstractmethod
    async def get_supported_algorithms(self) -> Dict[str, List[str]]:
        """
        Ottiene gli algoritmi supportati dal modulo.
        
        Returns:
            Dict: {
                "encryption": ["AES-256-GCM", "ChaCha20-Poly1305"],
                "signing": ["RSA-PSS", "ECDSA"],
                "hashing": ["SHA-256", "SHA-3-256"],
                "key_exchange": ["ECDH", "X25519"]
            }
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


class SecurityModuleError(Exception):
    """Eccezione base per errori dei moduli di sicurezza."""
    pass


class IdentityError(SecurityModuleError):
    """Errore nella gestione dell'identità."""
    pass


class EncryptionError(SecurityModuleError):
    """Errore nella crittografia."""
    pass


class DecryptionError(SecurityModuleError):
    """Errore nella decrittografia."""
    pass


class SignatureError(SecurityModuleError):
    """Errore nella firma digitale."""
    pass


class KeyManagementError(SecurityModuleError):
    """Errore nella gestione delle chiavi."""
    pass