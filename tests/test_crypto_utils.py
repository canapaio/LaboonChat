"""
Test suite per CryptoUtils

Testa tutte le operazioni crittografiche: generazione chiavi,
cifratura simmetrica/asimmetrica, firma digitale, hashing.
"""

import pytest
import base64
import json
from unittest.mock import patch, Mock
from typing import Dict, Any

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from laboon_chat2.utils.crypto_utils import (
    CryptoUtils, KeyPair, EncryptedData, DigitalSignature,
    CryptoError, KeyGenerationError, EncryptionError, DecryptionError,
    SignatureError, VerificationError, create_crypto_utils,
    quick_encrypt, quick_decrypt, quick_hash
)


@pytest.fixture
def crypto_utils():
    """Crea un'istanza di CryptoUtils per i test"""
    return CryptoUtils()


@pytest.fixture
def sample_data():
    """Dati di esempio per i test"""
    return b"This is test data for encryption and signing"


@pytest.fixture
def sample_text():
    """Testo di esempio per i test"""
    return "This is test text for encryption and signing"


class TestCryptoDataClasses:
    """Test per le dataclass crittografiche"""
    
    def test_key_pair_creation(self):
        """Testa creazione KeyPair"""
        private_key = b"private_key_data"
        public_key = b"public_key_data"
        
        key_pair = KeyPair(
            private_key=private_key,
            public_key=public_key,
            algorithm="RSA",
            key_size=2048
        )
        
        assert key_pair.private_key == private_key
        assert key_pair.public_key == public_key
        assert key_pair.algorithm == "RSA"
        assert key_pair.key_size == 2048
    
    def test_encrypted_data_creation(self):
        """Testa creazione EncryptedData"""
        ciphertext = b"encrypted_data"
        nonce = b"nonce_data"
        tag = b"auth_tag"
        
        encrypted = EncryptedData(
            ciphertext=ciphertext,
            nonce=nonce,
            tag=tag,
            algorithm="AES-GCM"
        )
        
        assert encrypted.ciphertext == ciphertext
        assert encrypted.nonce == nonce
        assert encrypted.tag == tag
        assert encrypted.algorithm == "AES-GCM"
    
    def test_digital_signature_creation(self):
        """Testa creazione DigitalSignature"""
        signature = b"signature_data"
        
        digital_sig = DigitalSignature(
            signature=signature,
            algorithm="Ed25519",
            public_key=b"public_key"
        )
        
        assert digital_sig.signature == signature
        assert digital_sig.algorithm == "Ed25519"
        assert digital_sig.public_key == b"public_key"


class TestKeyGeneration:
    """Test per la generazione di chiavi"""
    
    def test_generate_rsa_keypair(self, crypto_utils):
        """Testa generazione coppia chiavi RSA"""
        key_pair = crypto_utils.generate_rsa_keypair(2048)
        
        assert isinstance(key_pair, KeyPair)
        assert key_pair.algorithm == "RSA"
        assert key_pair.key_size == 2048
        assert key_pair.private_key is not None
        assert key_pair.public_key is not None
        assert len(key_pair.private_key) > 0
        assert len(key_pair.public_key) > 0
    
    def test_generate_rsa_keypair_different_sizes(self, crypto_utils):
        """Testa generazione RSA con diverse dimensioni"""
        sizes = [1024, 2048, 4096]
        
        for size in sizes:
            key_pair = crypto_utils.generate_rsa_keypair(size)
            assert key_pair.key_size == size
            assert key_pair.algorithm == "RSA"
    
    def test_generate_ed25519_keypair(self, crypto_utils):
        """Testa generazione coppia chiavi Ed25519"""
        key_pair = crypto_utils.generate_ed25519_keypair()
        
        assert isinstance(key_pair, KeyPair)
        assert key_pair.algorithm == "Ed25519"
        assert key_pair.key_size == 256
        assert key_pair.private_key is not None
        assert key_pair.public_key is not None
    
    def test_generate_symmetric_key(self, crypto_utils):
        """Testa generazione chiave simmetrica"""
        key = crypto_utils.generate_symmetric_key(32)
        
        assert isinstance(key, bytes)
        assert len(key) == 32
    
    def test_generate_symmetric_key_different_sizes(self, crypto_utils):
        """Testa generazione chiavi simmetriche di diverse dimensioni"""
        sizes = [16, 24, 32, 64]
        
        for size in sizes:
            key = crypto_utils.generate_symmetric_key(size)
            assert len(key) == size
    
    def test_derive_key_from_password(self, crypto_utils):
        """Testa derivazione chiave da password"""
        password = "test_password"
        salt = crypto_utils.generate_random_bytes(16)
        
        key = crypto_utils.derive_key_from_password(password, salt)
        
        assert isinstance(key, bytes)
        assert len(key) == 32  # Default key length
    
    def test_derive_key_from_password_consistent(self, crypto_utils):
        """Testa che la derivazione sia consistente"""
        password = "test_password"
        salt = crypto_utils.generate_random_bytes(16)
        
        key1 = crypto_utils.derive_key_from_password(password, salt)
        key2 = crypto_utils.derive_key_from_password(password, salt)
        
        assert key1 == key2
    
    def test_derive_key_from_password_different_salts(self, crypto_utils):
        """Testa che salt diversi producano chiavi diverse"""
        password = "test_password"
        salt1 = crypto_utils.generate_random_bytes(16)
        salt2 = crypto_utils.generate_random_bytes(16)
        
        key1 = crypto_utils.derive_key_from_password(password, salt1)
        key2 = crypto_utils.derive_key_from_password(password, salt2)
        
        assert key1 != key2


class TestSymmetricEncryption:
    """Test per la cifratura simmetrica"""
    
    def test_encrypt_decrypt_aes_gcm(self, crypto_utils, sample_data):
        """Testa cifratura/decifratura AES-GCM"""
        key = crypto_utils.generate_symmetric_key(32)
        
        # Cifra
        encrypted = crypto_utils.encrypt_symmetric(sample_data, key, "AES-GCM")
        
        assert isinstance(encrypted, EncryptedData)
        assert encrypted.algorithm == "AES-GCM"
        assert encrypted.ciphertext != sample_data
        assert encrypted.nonce is not None
        assert encrypted.tag is not None
        
        # Decifra
        decrypted = crypto_utils.decrypt_symmetric(encrypted, key)
        
        assert decrypted == sample_data
    
    def test_encrypt_decrypt_aes_cbc(self, crypto_utils, sample_data):
        """Testa cifratura/decifratura AES-CBC"""
        key = crypto_utils.generate_symmetric_key(32)
        
        # Cifra
        encrypted = crypto_utils.encrypt_symmetric(sample_data, key, "AES-CBC")
        
        assert isinstance(encrypted, EncryptedData)
        assert encrypted.algorithm == "AES-CBC"
        assert encrypted.ciphertext != sample_data
        assert encrypted.nonce is not None  # IV per CBC
        
        # Decifra
        decrypted = crypto_utils.decrypt_symmetric(encrypted, key)
        
        assert decrypted == sample_data
    
    def test_encrypt_decrypt_chacha20(self, crypto_utils, sample_data):
        """Testa cifratura/decifratura ChaCha20"""
        key = crypto_utils.generate_symmetric_key(32)
        
        # Cifra
        encrypted = crypto_utils.encrypt_symmetric(sample_data, key, "ChaCha20")
        
        assert isinstance(encrypted, EncryptedData)
        assert encrypted.algorithm == "ChaCha20"
        assert encrypted.ciphertext != sample_data
        assert encrypted.nonce is not None
        
        # Decifra
        decrypted = crypto_utils.decrypt_symmetric(encrypted, key)
        
        assert decrypted == sample_data
    
    def test_encrypt_with_wrong_key_size(self, crypto_utils, sample_data):
        """Testa cifratura con chiave di dimensione sbagliata"""
        wrong_key = crypto_utils.generate_symmetric_key(16)  # Troppo piccola per AES-256
        
        with pytest.raises(EncryptionError):
            crypto_utils.encrypt_symmetric(sample_data, wrong_key, "AES-GCM")
    
    def test_decrypt_with_wrong_key(self, crypto_utils, sample_data):
        """Testa decifratura con chiave sbagliata"""
        key1 = crypto_utils.generate_symmetric_key(32)
        key2 = crypto_utils.generate_symmetric_key(32)
        
        encrypted = crypto_utils.encrypt_symmetric(sample_data, key1, "AES-GCM")
        
        with pytest.raises(DecryptionError):
            crypto_utils.decrypt_symmetric(encrypted, key2)
    
    def test_encrypt_empty_data(self, crypto_utils):
        """Testa cifratura di dati vuoti"""
        key = crypto_utils.generate_symmetric_key(32)
        empty_data = b""
        
        encrypted = crypto_utils.encrypt_symmetric(empty_data, key, "AES-GCM")
        decrypted = crypto_utils.decrypt_symmetric(encrypted, key)
        
        assert decrypted == empty_data
    
    def test_encrypt_large_data(self, crypto_utils):
        """Testa cifratura di dati grandi"""
        key = crypto_utils.generate_symmetric_key(32)
        large_data = b"A" * 1000000  # 1MB
        
        encrypted = crypto_utils.encrypt_symmetric(large_data, key, "AES-GCM")
        decrypted = crypto_utils.decrypt_symmetric(encrypted, key)
        
        assert decrypted == large_data


class TestAsymmetricEncryption:
    """Test per la cifratura asimmetrica"""
    
    def test_encrypt_decrypt_rsa(self, crypto_utils, sample_data):
        """Testa cifratura/decifratura RSA"""
        key_pair = crypto_utils.generate_rsa_keypair(2048)
        
        # Cifra con chiave pubblica
        encrypted = crypto_utils.encrypt_asymmetric(sample_data, key_pair.public_key, "RSA-OAEP")
        
        assert isinstance(encrypted, EncryptedData)
        assert encrypted.algorithm == "RSA-OAEP"
        assert encrypted.ciphertext != sample_data
        
        # Decifra con chiave privata
        decrypted = crypto_utils.decrypt_asymmetric(encrypted, key_pair.private_key)
        
        assert decrypted == sample_data
    
    def test_encrypt_rsa_data_too_large(self, crypto_utils):
        """Testa cifratura RSA con dati troppo grandi"""
        key_pair = crypto_utils.generate_rsa_keypair(1024)
        large_data = b"A" * 1000  # Troppo grande per RSA-1024
        
        with pytest.raises(EncryptionError):
            crypto_utils.encrypt_asymmetric(large_data, key_pair.public_key, "RSA-OAEP")
    
    def test_decrypt_with_wrong_private_key(self, crypto_utils, sample_data):
        """Testa decifratura con chiave privata sbagliata"""
        key_pair1 = crypto_utils.generate_rsa_keypair(2048)
        key_pair2 = crypto_utils.generate_rsa_keypair(2048)
        
        encrypted = crypto_utils.encrypt_asymmetric(sample_data, key_pair1.public_key, "RSA-OAEP")
        
        with pytest.raises(DecryptionError):
            crypto_utils.decrypt_asymmetric(encrypted, key_pair2.private_key)


class TestDigitalSignatures:
    """Test per le firme digitali"""
    
    def test_sign_verify_ed25519(self, crypto_utils, sample_data):
        """Testa firma/verifica Ed25519"""
        key_pair = crypto_utils.generate_ed25519_keypair()
        
        # Firma
        signature = crypto_utils.sign_data(sample_data, key_pair.private_key, "Ed25519")
        
        assert isinstance(signature, DigitalSignature)
        assert signature.algorithm == "Ed25519"
        assert signature.signature is not None
        assert signature.public_key == key_pair.public_key
        
        # Verifica
        is_valid = crypto_utils.verify_signature(sample_data, signature)
        
        assert is_valid is True
    
    def test_sign_verify_rsa_pss(self, crypto_utils, sample_data):
        """Testa firma/verifica RSA-PSS"""
        key_pair = crypto_utils.generate_rsa_keypair(2048)
        
        # Firma
        signature = crypto_utils.sign_data(sample_data, key_pair.private_key, "RSA-PSS")
        
        assert isinstance(signature, DigitalSignature)
        assert signature.algorithm == "RSA-PSS"
        assert signature.signature is not None
        assert signature.public_key == key_pair.public_key
        
        # Verifica
        is_valid = crypto_utils.verify_signature(sample_data, signature)
        
        assert is_valid is True
    
    def test_verify_signature_wrong_data(self, crypto_utils, sample_data):
        """Testa verifica firma con dati modificati"""
        key_pair = crypto_utils.generate_ed25519_keypair()
        
        signature = crypto_utils.sign_data(sample_data, key_pair.private_key, "Ed25519")
        
        # Modifica i dati
        modified_data = sample_data + b" modified"
        
        is_valid = crypto_utils.verify_signature(modified_data, signature)
        
        assert is_valid is False
    
    def test_verify_signature_wrong_key(self, crypto_utils, sample_data):
        """Testa verifica firma con chiave sbagliata"""
        key_pair1 = crypto_utils.generate_ed25519_keypair()
        key_pair2 = crypto_utils.generate_ed25519_keypair()
        
        signature = crypto_utils.sign_data(sample_data, key_pair1.private_key, "Ed25519")
        
        # Modifica la chiave pubblica nella firma
        signature.public_key = key_pair2.public_key
        
        is_valid = crypto_utils.verify_signature(sample_data, signature)
        
        assert is_valid is False
    
    def test_sign_empty_data(self, crypto_utils):
        """Testa firma di dati vuoti"""
        key_pair = crypto_utils.generate_ed25519_keypair()
        empty_data = b""
        
        signature = crypto_utils.sign_data(empty_data, key_pair.private_key, "Ed25519")
        is_valid = crypto_utils.verify_signature(empty_data, signature)
        
        assert is_valid is True


class TestHashing:
    """Test per le funzioni di hash"""
    
    def test_hash_data_sha256(self, crypto_utils, sample_data):
        """Testa hash SHA-256"""
        hash_value = crypto_utils.hash_data(sample_data, "SHA-256")
        
        assert isinstance(hash_value, bytes)
        assert len(hash_value) == 32  # SHA-256 produce 32 bytes
    
    def test_hash_data_sha512(self, crypto_utils, sample_data):
        """Testa hash SHA-512"""
        hash_value = crypto_utils.hash_data(sample_data, "SHA-512")
        
        assert isinstance(hash_value, bytes)
        assert len(hash_value) == 64  # SHA-512 produce 64 bytes
    
    def test_hash_data_blake2b(self, crypto_utils, sample_data):
        """Testa hash BLAKE2b"""
        hash_value = crypto_utils.hash_data(sample_data, "BLAKE2b")
        
        assert isinstance(hash_value, bytes)
        assert len(hash_value) == 64  # BLAKE2b produce 64 bytes di default
    
    def test_hash_consistency(self, crypto_utils, sample_data):
        """Testa che l'hash sia consistente"""
        hash1 = crypto_utils.hash_data(sample_data, "SHA-256")
        hash2 = crypto_utils.hash_data(sample_data, "SHA-256")
        
        assert hash1 == hash2
    
    def test_hash_different_data(self, crypto_utils):
        """Testa che dati diversi producano hash diversi"""
        data1 = b"test data 1"
        data2 = b"test data 2"
        
        hash1 = crypto_utils.hash_data(data1, "SHA-256")
        hash2 = crypto_utils.hash_data(data2, "SHA-256")
        
        assert hash1 != hash2
    
    def test_calculate_key_fingerprint(self, crypto_utils):
        """Testa calcolo fingerprint chiave"""
        key_pair = crypto_utils.generate_ed25519_keypair()
        
        fingerprint = crypto_utils.calculate_key_fingerprint(key_pair.public_key)
        
        assert isinstance(fingerprint, str)
        assert len(fingerprint) > 0
        assert ":" in fingerprint  # Formato fingerprint con separatori
    
    def test_key_fingerprint_consistency(self, crypto_utils):
        """Testa che il fingerprint sia consistente"""
        key_pair = crypto_utils.generate_ed25519_keypair()
        
        fingerprint1 = crypto_utils.calculate_key_fingerprint(key_pair.public_key)
        fingerprint2 = crypto_utils.calculate_key_fingerprint(key_pair.public_key)
        
        assert fingerprint1 == fingerprint2


class TestRandomGeneration:
    """Test per la generazione di dati casuali"""
    
    def test_generate_random_bytes(self, crypto_utils):
        """Testa generazione bytes casuali"""
        random_bytes = crypto_utils.generate_random_bytes(32)
        
        assert isinstance(random_bytes, bytes)
        assert len(random_bytes) == 32
    
    def test_generate_random_bytes_different_sizes(self, crypto_utils):
        """Testa generazione bytes di diverse dimensioni"""
        sizes = [8, 16, 32, 64, 128]
        
        for size in sizes:
            random_bytes = crypto_utils.generate_random_bytes(size)
            assert len(random_bytes) == size
    
    def test_generate_random_bytes_uniqueness(self, crypto_utils):
        """Testa che bytes generati siano diversi"""
        bytes1 = crypto_utils.generate_random_bytes(32)
        bytes2 = crypto_utils.generate_random_bytes(32)
        
        assert bytes1 != bytes2
    
    def test_generate_random_string(self, crypto_utils):
        """Testa generazione stringa casuale"""
        random_string = crypto_utils.generate_random_string(16)
        
        assert isinstance(random_string, str)
        assert len(random_string) == 16
    
    def test_generate_random_string_charset(self, crypto_utils):
        """Testa generazione stringa con charset specifico"""
        charset = "ABCDEF0123456789"
        random_string = crypto_utils.generate_random_string(10, charset)
        
        assert len(random_string) == 10
        assert all(c in charset for c in random_string)


class TestBase64Operations:
    """Test per le operazioni Base64"""
    
    def test_encode_decode_base64(self, crypto_utils, sample_data):
        """Testa codifica/decodifica Base64"""
        encoded = crypto_utils.encode_base64(sample_data)
        
        assert isinstance(encoded, str)
        assert len(encoded) > 0
        
        decoded = crypto_utils.decode_base64(encoded)
        
        assert decoded == sample_data
    
    def test_encode_decode_base64_empty(self, crypto_utils):
        """Testa Base64 con dati vuoti"""
        empty_data = b""
        
        encoded = crypto_utils.encode_base64(empty_data)
        decoded = crypto_utils.decode_base64(encoded)
        
        assert decoded == empty_data
    
    def test_decode_base64_invalid(self, crypto_utils):
        """Testa decodifica Base64 invalida"""
        invalid_base64 = "invalid base64 string!"
        
        with pytest.raises(CryptoError):
            crypto_utils.decode_base64(invalid_base64)


class TestSerialization:
    """Test per la serializzazione"""
    
    def test_serialize_deserialize_encrypted_data(self, crypto_utils, sample_data):
        """Testa serializzazione EncryptedData"""
        key = crypto_utils.generate_symmetric_key(32)
        encrypted = crypto_utils.encrypt_symmetric(sample_data, key, "AES-GCM")
        
        # Serializza
        serialized = crypto_utils.serialize_encrypted_data(encrypted)
        
        assert isinstance(serialized, str)
        
        # Deserializza
        deserialized = crypto_utils.deserialize_encrypted_data(serialized)
        
        assert isinstance(deserialized, EncryptedData)
        assert deserialized.algorithm == encrypted.algorithm
        assert deserialized.ciphertext == encrypted.ciphertext
        assert deserialized.nonce == encrypted.nonce
        assert deserialized.tag == encrypted.tag
    
    def test_serialize_deserialize_digital_signature(self, crypto_utils, sample_data):
        """Testa serializzazione DigitalSignature"""
        key_pair = crypto_utils.generate_ed25519_keypair()
        signature = crypto_utils.sign_data(sample_data, key_pair.private_key, "Ed25519")
        
        # Serializza
        serialized = crypto_utils.serialize_digital_signature(signature)
        
        assert isinstance(serialized, str)
        
        # Deserializza
        deserialized = crypto_utils.deserialize_digital_signature(serialized)
        
        assert isinstance(deserialized, DigitalSignature)
        assert deserialized.algorithm == signature.algorithm
        assert deserialized.signature == signature.signature
        assert deserialized.public_key == signature.public_key
    
    def test_deserialize_invalid_json(self, crypto_utils):
        """Testa deserializzazione JSON invalido"""
        invalid_json = "{ invalid json }"
        
        with pytest.raises(CryptoError):
            crypto_utils.deserialize_encrypted_data(invalid_json)


class TestUtilityFunctions:
    """Test per le funzioni di utilità"""
    
    def test_create_crypto_utils(self):
        """Testa funzione factory create_crypto_utils"""
        crypto = create_crypto_utils()
        
        assert isinstance(crypto, CryptoUtils)
    
    def test_quick_encrypt_decrypt(self, sample_text):
        """Testa funzioni quick_encrypt/quick_decrypt"""
        password = "test_password"
        
        # Cifra
        encrypted = quick_encrypt(sample_text, password)
        
        assert isinstance(encrypted, str)
        assert encrypted != sample_text
        
        # Decifra
        decrypted = quick_decrypt(encrypted, password)
        
        assert decrypted == sample_text
    
    def test_quick_encrypt_decrypt_wrong_password(self, sample_text):
        """Testa quick_decrypt con password sbagliata"""
        password1 = "correct_password"
        password2 = "wrong_password"
        
        encrypted = quick_encrypt(sample_text, password1)
        
        with pytest.raises(DecryptionError):
            quick_decrypt(encrypted, password2)
    
    def test_quick_hash(self, sample_text):
        """Testa funzione quick_hash"""
        hash_value = quick_hash(sample_text)
        
        assert isinstance(hash_value, str)
        assert len(hash_value) > 0
    
    def test_quick_hash_consistency(self, sample_text):
        """Testa che quick_hash sia consistente"""
        hash1 = quick_hash(sample_text)
        hash2 = quick_hash(sample_text)
        
        assert hash1 == hash2


class TestErrorHandling:
    """Test per la gestione degli errori"""
    
    def test_crypto_error_hierarchy(self):
        """Testa gerarchia delle eccezioni"""
        assert issubclass(KeyGenerationError, CryptoError)
        assert issubclass(EncryptionError, CryptoError)
        assert issubclass(DecryptionError, CryptoError)
        assert issubclass(SignatureError, CryptoError)
        assert issubclass(VerificationError, CryptoError)
    
    def test_invalid_algorithm_encryption(self, crypto_utils, sample_data):
        """Testa algoritmo di cifratura invalido"""
        key = crypto_utils.generate_symmetric_key(32)
        
        with pytest.raises(EncryptionError):
            crypto_utils.encrypt_symmetric(sample_data, key, "INVALID_ALGORITHM")
    
    def test_invalid_algorithm_signing(self, crypto_utils, sample_data):
        """Testa algoritmo di firma invalido"""
        key_pair = crypto_utils.generate_ed25519_keypair()
        
        with pytest.raises(SignatureError):
            crypto_utils.sign_data(sample_data, key_pair.private_key, "INVALID_ALGORITHM")
    
    def test_invalid_key_format(self, crypto_utils, sample_data):
        """Testa formato chiave invalido"""
        invalid_key = b"not_a_valid_key"
        
        with pytest.raises(EncryptionError):
            crypto_utils.encrypt_asymmetric(sample_data, invalid_key, "RSA-OAEP")


@pytest.mark.asyncio
async def test_crypto_utils_integration():
    """Test di integrazione completo per CryptoUtils"""
    crypto = CryptoUtils()
    
    # Test workflow completo di sicurezza
    
    # 1. Genera chiavi
    rsa_keys = crypto.generate_rsa_keypair(2048)
    ed25519_keys = crypto.generate_ed25519_keypair()
    symmetric_key = crypto.generate_symmetric_key(32)
    
    # 2. Dati di test
    message = b"Secret message for integration test"
    
    # 3. Cifratura simmetrica
    encrypted_symmetric = crypto.encrypt_symmetric(message, symmetric_key, "AES-GCM")
    decrypted_symmetric = crypto.decrypt_symmetric(encrypted_symmetric, symmetric_key)
    assert decrypted_symmetric == message
    
    # 4. Cifratura asimmetrica
    encrypted_asymmetric = crypto.encrypt_asymmetric(message, rsa_keys.public_key, "RSA-OAEP")
    decrypted_asymmetric = crypto.decrypt_asymmetric(encrypted_asymmetric, rsa_keys.private_key)
    assert decrypted_asymmetric == message
    
    # 5. Firma digitale
    signature = crypto.sign_data(message, ed25519_keys.private_key, "Ed25519")
    is_valid = crypto.verify_signature(message, signature)
    assert is_valid is True
    
    # 6. Hash
    hash_value = crypto.hash_data(message, "SHA-256")
    assert len(hash_value) == 32
    
    # 7. Serializzazione
    encrypted_serialized = crypto.serialize_encrypted_data(encrypted_symmetric)
    signature_serialized = crypto.serialize_digital_signature(signature)
    
    encrypted_deserialized = crypto.deserialize_encrypted_data(encrypted_serialized)
    signature_deserialized = crypto.deserialize_digital_signature(signature_serialized)
    
    # 8. Verifica deserializzazione
    final_decrypted = crypto.decrypt_symmetric(encrypted_deserialized, symmetric_key)
    assert final_decrypted == message
    
    final_verification = crypto.verify_signature(message, signature_deserialized)
    assert final_verification is True
    
    # 9. Test funzioni quick
    quick_encrypted = quick_encrypt("test message", "password")
    quick_decrypted = quick_decrypt(quick_encrypted, "password")
    assert quick_decrypted == "test message"
    
    quick_hash_value = quick_hash("test message")
    assert len(quick_hash_value) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])