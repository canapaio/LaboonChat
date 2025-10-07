"""
Advanced Cryptographic Utilities for LaboonChat v2.0

Provides secure encryption, digital signatures, key management, and identity verification.
"""

import os
import hashlib
import hmac
import secrets
import base64
from typing import Dict, Any, Optional, Tuple, Union, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa, padding, ed25519
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
    from cryptography.hazmat.backends import default_backend
    from cryptography.fernet import Fernet
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False


@dataclass
class KeyPair:
    """Coppia di chiavi pubblica/privata."""
    public_key: bytes
    private_key: bytes
    key_type: str
    created_at: datetime
    fingerprint: str


@dataclass
class EncryptedData:
    """Dati crittografati con metadati."""
    ciphertext: bytes
    nonce: Optional[bytes] = None
    tag: Optional[bytes] = None
    algorithm: str = "AES-GCM"
    key_derivation: Optional[str] = None
    salt: Optional[bytes] = None


@dataclass
class DigitalSignature:
    """Firma digitale con metadati."""
    signature: bytes
    algorithm: str
    public_key_fingerprint: str
    timestamp: datetime
    message_hash: str


class CryptoError(Exception):
    """Errore crittografico base."""
    pass


class KeyGenerationError(CryptoError):
    """Errore nella generazione chiavi."""
    pass


class EncryptionError(CryptoError):
    """Errore nella crittografia."""
    pass


class DecryptionError(CryptoError):
    """Errore nella decrittografia."""
    pass


class SignatureError(CryptoError):
    """Errore nelle firme digitali."""
    pass


class CryptoUtils:
    """
    Utility crittografiche avanzate per LaboonChat v2.0.
    
    Caratteristiche:
    - Crittografia simmetrica e asimmetrica
    - Firme digitali
    - Gestione chiavi sicura
    - Derivazione chiavi da password
    - Hashing sicuro
    - Generazione numeri casuali
    """
    
    def __init__(self):
        if not CRYPTOGRAPHY_AVAILABLE:
            raise ImportError("Libreria cryptography non disponibile")
        
        self._backend = default_backend()
        self._key_cache: Dict[str, KeyPair] = {}
    
    # === Generazione Chiavi ===
    
    def generate_rsa_keypair(
        self,
        key_size: int = 2048,
        public_exponent: int = 65537
    ) -> KeyPair:
        """
        Genera coppia di chiavi RSA.
        
        Args:
            key_size: Dimensione chiave in bit
            public_exponent: Esponente pubblico
            
        Returns:
            KeyPair: Coppia di chiavi
            
        Raises:
            KeyGenerationError: Se generazione fallisce
        """
        try:
            private_key = rsa.generate_private_key(
                public_exponent=public_exponent,
                key_size=key_size,
                backend=self._backend
            )
            
            public_key = private_key.public_key()
            
            # Serializza chiavi
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            # Calcola fingerprint
            fingerprint = self.calculate_key_fingerprint(public_pem)
            
            return KeyPair(
                public_key=public_pem,
                private_key=private_pem,
                key_type="RSA",
                created_at=datetime.now(),
                fingerprint=fingerprint
            )
            
        except Exception as e:
            raise KeyGenerationError(f"Errore generazione chiavi RSA: {e}")
    
    def generate_ed25519_keypair(self) -> KeyPair:
        """
        Genera coppia di chiavi Ed25519 (curve ellittiche).
        
        Returns:
            KeyPair: Coppia di chiavi
            
        Raises:
            KeyGenerationError: Se generazione fallisce
        """
        try:
            private_key = ed25519.Ed25519PrivateKey.generate()
            public_key = private_key.public_key()
            
            # Serializza chiavi
            private_bytes = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            public_bytes = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            # Calcola fingerprint
            fingerprint = self.calculate_key_fingerprint(public_bytes)
            
            return KeyPair(
                public_key=public_bytes,
                private_key=private_bytes,
                key_type="Ed25519",
                created_at=datetime.now(),
                fingerprint=fingerprint
            )
            
        except Exception as e:
            raise KeyGenerationError(f"Errore generazione chiavi Ed25519: {e}")
    
    def generate_symmetric_key(self, key_size: int = 32) -> bytes:
        """
        Genera chiave simmetrica casuale.
        
        Args:
            key_size: Dimensione chiave in byte
            
        Returns:
            bytes: Chiave simmetrica
        """
        return secrets.token_bytes(key_size)
    
    def derive_key_from_password(
        self,
        password: str,
        salt: Optional[bytes] = None,
        key_length: int = 32,
        iterations: int = 100000,
        algorithm: str = "PBKDF2"
    ) -> Tuple[bytes, bytes]:
        """
        Deriva chiave da password.
        
        Args:
            password: Password
            salt: Salt (generato se None)
            key_length: Lunghezza chiave derivata
            iterations: Numero iterazioni
            algorithm: Algoritmo (PBKDF2 o Scrypt)
            
        Returns:
            Tuple[bytes, bytes]: (chiave_derivata, salt)
            
        Raises:
            CryptoError: Se derivazione fallisce
        """
        if salt is None:
            salt = secrets.token_bytes(16)
        
        try:
            if algorithm.upper() == "PBKDF2":
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=key_length,
                    salt=salt,
                    iterations=iterations,
                    backend=self._backend
                )
            elif algorithm.upper() == "SCRYPT":
                kdf = Scrypt(
                    algorithm=hashes.SHA256(),
                    length=key_length,
                    salt=salt,
                    n=2**14,  # CPU/memory cost
                    r=8,      # Block size
                    p=1,      # Parallelization
                    backend=self._backend
                )
            else:
                raise CryptoError(f"Algoritmo derivazione non supportato: {algorithm}")
            
            key = kdf.derive(password.encode('utf-8'))
            return key, salt
            
        except Exception as e:
            raise CryptoError(f"Errore derivazione chiave: {e}")
    
    # === Crittografia Simmetrica ===
    
    def encrypt_symmetric(
        self,
        data: Union[str, bytes],
        key: bytes,
        algorithm: str = "AES-GCM"
    ) -> EncryptedData:
        """
        Crittografia simmetrica.
        
        Args:
            data: Dati da crittografare
            key: Chiave simmetrica
            algorithm: Algoritmo (AES-GCM, AES-CBC, ChaCha20)
            
        Returns:
            EncryptedData: Dati crittografati
            
        Raises:
            EncryptionError: Se crittografia fallisce
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        try:
            if algorithm == "AES-GCM":
                return self._encrypt_aes_gcm(data, key)
            elif algorithm == "AES-CBC":
                return self._encrypt_aes_cbc(data, key)
            elif algorithm == "ChaCha20":
                return self._encrypt_chacha20(data, key)
            else:
                raise EncryptionError(f"Algoritmo non supportato: {algorithm}")
                
        except Exception as e:
            raise EncryptionError(f"Errore crittografia: {e}")
    
    def decrypt_symmetric(
        self,
        encrypted_data: EncryptedData,
        key: bytes
    ) -> bytes:
        """
        Decrittografia simmetrica.
        
        Args:
            encrypted_data: Dati crittografati
            key: Chiave simmetrica
            
        Returns:
            bytes: Dati decrittografati
            
        Raises:
            DecryptionError: Se decrittografia fallisce
        """
        try:
            if encrypted_data.algorithm == "AES-GCM":
                return self._decrypt_aes_gcm(encrypted_data, key)
            elif encrypted_data.algorithm == "AES-CBC":
                return self._decrypt_aes_cbc(encrypted_data, key)
            elif encrypted_data.algorithm == "ChaCha20":
                return self._decrypt_chacha20(encrypted_data, key)
            else:
                raise DecryptionError(f"Algoritmo non supportato: {encrypted_data.algorithm}")
                
        except Exception as e:
            raise DecryptionError(f"Errore decrittografia: {e}")
    
    # === Crittografia Asimmetrica ===
    
    def encrypt_asymmetric(
        self,
        data: Union[str, bytes],
        public_key_pem: bytes,
        algorithm: str = "RSA-OAEP"
    ) -> bytes:
        """
        Crittografia asimmetrica.
        
        Args:
            data: Dati da crittografare
            public_key_pem: Chiave pubblica PEM
            algorithm: Algoritmo (RSA-OAEP)
            
        Returns:
            bytes: Dati crittografati
            
        Raises:
            EncryptionError: Se crittografia fallisce
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        try:
            public_key = serialization.load_pem_public_key(
                public_key_pem,
                backend=self._backend
            )
            
            if algorithm == "RSA-OAEP":
                if not isinstance(public_key, rsa.RSAPublicKey):
                    raise EncryptionError("Chiave non RSA per algoritmo RSA-OAEP")
                
                ciphertext = public_key.encrypt(
                    data,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                return ciphertext
            else:
                raise EncryptionError(f"Algoritmo non supportato: {algorithm}")
                
        except Exception as e:
            raise EncryptionError(f"Errore crittografia asimmetrica: {e}")
    
    def decrypt_asymmetric(
        self,
        ciphertext: bytes,
        private_key_pem: bytes,
        algorithm: str = "RSA-OAEP"
    ) -> bytes:
        """
        Decrittografia asimmetrica.
        
        Args:
            ciphertext: Dati crittografati
            private_key_pem: Chiave privata PEM
            algorithm: Algoritmo (RSA-OAEP)
            
        Returns:
            bytes: Dati decrittografati
            
        Raises:
            DecryptionError: Se decrittografia fallisce
        """
        try:
            private_key = serialization.load_pem_private_key(
                private_key_pem,
                password=None,
                backend=self._backend
            )
            
            if algorithm == "RSA-OAEP":
                if not isinstance(private_key, rsa.RSAPrivateKey):
                    raise DecryptionError("Chiave non RSA per algoritmo RSA-OAEP")
                
                plaintext = private_key.decrypt(
                    ciphertext,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                return plaintext
            else:
                raise DecryptionError(f"Algoritmo non supportato: {algorithm}")
                
        except Exception as e:
            raise DecryptionError(f"Errore decrittografia asimmetrica: {e}")
    
    # === Firme Digitali ===
    
    def sign_data(
        self,
        data: Union[str, bytes],
        private_key_pem: bytes,
        algorithm: str = "Ed25519"
    ) -> DigitalSignature:
        """
        Firma digitale.
        
        Args:
            data: Dati da firmare
            private_key_pem: Chiave privata PEM
            algorithm: Algoritmo (Ed25519, RSA-PSS)
            
        Returns:
            DigitalSignature: Firma digitale
            
        Raises:
            SignatureError: Se firma fallisce
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        try:
            private_key = serialization.load_pem_private_key(
                private_key_pem,
                password=None,
                backend=self._backend
            )
            
            # Calcola hash del messaggio
            message_hash = hashlib.sha256(data).hexdigest()
            
            # Ottieni fingerprint chiave pubblica
            public_key = private_key.public_key()
            public_key_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            fingerprint = self.calculate_key_fingerprint(public_key_pem)
            
            if algorithm == "Ed25519":
                if not isinstance(private_key, ed25519.Ed25519PrivateKey):
                    raise SignatureError("Chiave non Ed25519 per algoritmo Ed25519")
                
                signature = private_key.sign(data)
                
            elif algorithm == "RSA-PSS":
                if not isinstance(private_key, rsa.RSAPrivateKey):
                    raise SignatureError("Chiave non RSA per algoritmo RSA-PSS")
                
                signature = private_key.sign(
                    data,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA256()
                )
            else:
                raise SignatureError(f"Algoritmo non supportato: {algorithm}")
            
            return DigitalSignature(
                signature=signature,
                algorithm=algorithm,
                public_key_fingerprint=fingerprint,
                timestamp=datetime.now(),
                message_hash=message_hash
            )
            
        except Exception as e:
            raise SignatureError(f"Errore firma digitale: {e}")
    
    def verify_signature(
        self,
        data: Union[str, bytes],
        signature: DigitalSignature,
        public_key_pem: bytes
    ) -> bool:
        """
        Verifica firma digitale.
        
        Args:
            data: Dati originali
            signature: Firma digitale
            public_key_pem: Chiave pubblica PEM
            
        Returns:
            bool: True se firma valida
            
        Raises:
            SignatureError: Se verifica fallisce
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        try:
            public_key = serialization.load_pem_public_key(
                public_key_pem,
                backend=self._backend
            )
            
            # Verifica fingerprint chiave
            fingerprint = self.calculate_key_fingerprint(public_key_pem)
            if fingerprint != signature.public_key_fingerprint:
                return False
            
            # Verifica hash messaggio
            message_hash = hashlib.sha256(data).hexdigest()
            if message_hash != signature.message_hash:
                return False
            
            if signature.algorithm == "Ed25519":
                if not isinstance(public_key, ed25519.Ed25519PublicKey):
                    raise SignatureError("Chiave non Ed25519 per algoritmo Ed25519")
                
                try:
                    public_key.verify(signature.signature, data)
                    return True
                except Exception:
                    return False
                    
            elif signature.algorithm == "RSA-PSS":
                if not isinstance(public_key, rsa.RSAPublicKey):
                    raise SignatureError("Chiave non RSA per algoritmo RSA-PSS")
                
                try:
                    public_key.verify(
                        signature.signature,
                        data,
                        padding.PSS(
                            mgf=padding.MGF1(hashes.SHA256()),
                            salt_length=padding.PSS.MAX_LENGTH
                        ),
                        hashes.SHA256()
                    )
                    return True
                except Exception:
                    return False
            else:
                raise SignatureError(f"Algoritmo non supportato: {signature.algorithm}")
                
        except Exception as e:
            raise SignatureError(f"Errore verifica firma: {e}")
    
    # === Hashing ===
    
    def hash_data(
        self,
        data: Union[str, bytes],
        algorithm: str = "SHA256",
        salt: Optional[bytes] = None
    ) -> Tuple[str, Optional[bytes]]:
        """
        Calcola hash dei dati.
        
        Args:
            data: Dati da hashare
            algorithm: Algoritmo (SHA256, SHA512, BLAKE2b)
            salt: Salt opzionale
            
        Returns:
            Tuple[str, Optional[bytes]]: (hash_hex, salt)
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        if salt:
            data = salt + data
        
        if algorithm == "SHA256":
            hash_obj = hashlib.sha256(data)
        elif algorithm == "SHA512":
            hash_obj = hashlib.sha512(data)
        elif algorithm == "BLAKE2b":
            hash_obj = hashlib.blake2b(data)
        else:
            raise CryptoError(f"Algoritmo hash non supportato: {algorithm}")
        
        return hash_obj.hexdigest(), salt
    
    def verify_hash(
        self,
        data: Union[str, bytes],
        expected_hash: str,
        algorithm: str = "SHA256",
        salt: Optional[bytes] = None
    ) -> bool:
        """
        Verifica hash dei dati.
        
        Args:
            data: Dati originali
            expected_hash: Hash atteso
            algorithm: Algoritmo hash
            salt: Salt usato
            
        Returns:
            bool: True se hash corrisponde
        """
        calculated_hash, _ = self.hash_data(data, algorithm, salt)
        return hmac.compare_digest(calculated_hash, expected_hash)
    
    # === Utility ===
    
    def calculate_key_fingerprint(self, public_key_pem: bytes) -> str:
        """
        Calcola fingerprint di una chiave pubblica.
        
        Args:
            public_key_pem: Chiave pubblica PEM
            
        Returns:
            str: Fingerprint esadecimale
        """
        hash_obj = hashlib.sha256(public_key_pem)
        return hash_obj.hexdigest()[:16]  # Prime 16 cifre
    
    def generate_random_bytes(self, length: int) -> bytes:
        """
        Genera bytes casuali sicuri.
        
        Args:
            length: Numero di byte
            
        Returns:
            bytes: Byte casuali
        """
        return secrets.token_bytes(length)
    
    def generate_random_string(
        self,
        length: int,
        alphabet: str = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    ) -> str:
        """
        Genera stringa casuale sicura.
        
        Args:
            length: Lunghezza stringa
            alphabet: Alfabeto da usare
            
        Returns:
            str: Stringa casuale
        """
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def encode_base64(self, data: bytes) -> str:
        """
        Codifica in Base64.
        
        Args:
            data: Dati da codificare
            
        Returns:
            str: Stringa Base64
        """
        return base64.b64encode(data).decode('ascii')
    
    def decode_base64(self, encoded: str) -> bytes:
        """
        Decodifica da Base64.
        
        Args:
            encoded: Stringa Base64
            
        Returns:
            bytes: Dati decodificati
        """
        return base64.b64decode(encoded.encode('ascii'))
    
    # === Serializzazione ===
    
    def serialize_encrypted_data(self, encrypted_data: EncryptedData) -> str:
        """
        Serializza dati crittografati in JSON.
        
        Args:
            encrypted_data: Dati crittografati
            
        Returns:
            str: JSON serializzato
        """
        data = {
            "ciphertext": self.encode_base64(encrypted_data.ciphertext),
            "algorithm": encrypted_data.algorithm
        }
        
        if encrypted_data.nonce:
            data["nonce"] = self.encode_base64(encrypted_data.nonce)
        if encrypted_data.tag:
            data["tag"] = self.encode_base64(encrypted_data.tag)
        if encrypted_data.salt:
            data["salt"] = self.encode_base64(encrypted_data.salt)
        if encrypted_data.key_derivation:
            data["key_derivation"] = encrypted_data.key_derivation
        
        return json.dumps(data)
    
    def deserialize_encrypted_data(self, json_str: str) -> EncryptedData:
        """
        Deserializza dati crittografati da JSON.
        
        Args:
            json_str: JSON serializzato
            
        Returns:
            EncryptedData: Dati crittografati
        """
        data = json.loads(json_str)
        
        return EncryptedData(
            ciphertext=self.decode_base64(data["ciphertext"]),
            nonce=self.decode_base64(data["nonce"]) if "nonce" in data else None,
            tag=self.decode_base64(data["tag"]) if "tag" in data else None,
            algorithm=data["algorithm"],
            key_derivation=data.get("key_derivation"),
            salt=self.decode_base64(data["salt"]) if "salt" in data else None
        )
    
    def serialize_signature(self, signature: DigitalSignature) -> str:
        """
        Serializza firma digitale in JSON.
        
        Args:
            signature: Firma digitale
            
        Returns:
            str: JSON serializzato
        """
        data = {
            "signature": self.encode_base64(signature.signature),
            "algorithm": signature.algorithm,
            "public_key_fingerprint": signature.public_key_fingerprint,
            "timestamp": signature.timestamp.isoformat(),
            "message_hash": signature.message_hash
        }
        
        return json.dumps(data)
    
    def deserialize_signature(self, json_str: str) -> DigitalSignature:
        """
        Deserializza firma digitale da JSON.
        
        Args:
            json_str: JSON serializzato
            
        Returns:
            DigitalSignature: Firma digitale
        """
        data = json.loads(json_str)
        
        return DigitalSignature(
            signature=self.decode_base64(data["signature"]),
            algorithm=data["algorithm"],
            public_key_fingerprint=data["public_key_fingerprint"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            message_hash=data["message_hash"]
        )
    
    # === Private Methods ===
    
    def _encrypt_aes_gcm(self, data: bytes, key: bytes) -> EncryptedData:
        """Crittografia AES-GCM."""
        nonce = secrets.token_bytes(12)  # 96 bit per GCM
        
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(nonce),
            backend=self._backend
        )
        
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(data) + encryptor.finalize()
        
        return EncryptedData(
            ciphertext=ciphertext,
            nonce=nonce,
            tag=encryptor.tag,
            algorithm="AES-GCM"
        )
    
    def _decrypt_aes_gcm(self, encrypted_data: EncryptedData, key: bytes) -> bytes:
        """Decrittografia AES-GCM."""
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(encrypted_data.nonce, encrypted_data.tag),
            backend=self._backend
        )
        
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(encrypted_data.ciphertext) + decryptor.finalize()
        
        return plaintext
    
    def _encrypt_aes_cbc(self, data: bytes, key: bytes) -> EncryptedData:
        """Crittografia AES-CBC."""
        # Padding PKCS7
        pad_length = 16 - (len(data) % 16)
        padded_data = data + bytes([pad_length] * pad_length)
        
        nonce = secrets.token_bytes(16)  # IV per CBC
        
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(nonce),
            backend=self._backend
        )
        
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        
        return EncryptedData(
            ciphertext=ciphertext,
            nonce=nonce,
            algorithm="AES-CBC"
        )
    
    def _decrypt_aes_cbc(self, encrypted_data: EncryptedData, key: bytes) -> bytes:
        """Decrittografia AES-CBC."""
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(encrypted_data.nonce),
            backend=self._backend
        )
        
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(encrypted_data.ciphertext) + decryptor.finalize()
        
        # Rimuovi padding PKCS7
        pad_length = padded_data[-1]
        plaintext = padded_data[:-pad_length]
        
        return plaintext
    
    def _encrypt_chacha20(self, data: bytes, key: bytes) -> EncryptedData:
        """Crittografia ChaCha20."""
        nonce = secrets.token_bytes(16)
        
        cipher = Cipher(
            algorithms.ChaCha20(key, nonce),
            mode=None,
            backend=self._backend
        )
        
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(data) + encryptor.finalize()
        
        return EncryptedData(
            ciphertext=ciphertext,
            nonce=nonce,
            algorithm="ChaCha20"
        )
    
    def _decrypt_chacha20(self, encrypted_data: EncryptedData, key: bytes) -> bytes:
        """Decrittografia ChaCha20."""
        cipher = Cipher(
            algorithms.ChaCha20(key, encrypted_data.nonce),
            mode=None,
            backend=self._backend
        )
        
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(encrypted_data.ciphertext) + decryptor.finalize()
        
        return plaintext


# === Convenience Functions ===

def create_crypto_utils() -> CryptoUtils:
    """
    Crea istanza CryptoUtils.
    
    Returns:
        CryptoUtils: Istanza utility crittografiche
    """
    return CryptoUtils()


def quick_encrypt(data: Union[str, bytes], password: str) -> str:
    """
    Crittografia rapida con password.
    
    Args:
        data: Dati da crittografare
        password: Password
        
    Returns:
        str: Dati crittografati serializzati
    """
    crypto = CryptoUtils()
    key, salt = crypto.derive_key_from_password(password)
    encrypted = crypto.encrypt_symmetric(data, key)
    encrypted.salt = salt
    encrypted.key_derivation = "PBKDF2"
    return crypto.serialize_encrypted_data(encrypted)


def quick_decrypt(encrypted_json: str, password: str) -> bytes:
    """
    Decrittografia rapida con password.
    
    Args:
        encrypted_json: Dati crittografati serializzati
        password: Password
        
    Returns:
        bytes: Dati decrittografati
    """
    crypto = CryptoUtils()
    encrypted = crypto.deserialize_encrypted_data(encrypted_json)
    key, _ = crypto.derive_key_from_password(password, encrypted.salt)
    return crypto.decrypt_symmetric(encrypted, key)


def quick_hash(data: Union[str, bytes], algorithm: str = "SHA256") -> str:
    """
    Hash rapido.
    
    Args:
        data: Dati da hashare
        algorithm: Algoritmo hash
        
    Returns:
        str: Hash esadecimale
    """
    crypto = CryptoUtils()
    hash_hex, _ = crypto.hash_data(data, algorithm)
    return hash_hex