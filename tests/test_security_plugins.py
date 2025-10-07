"""
Test suite per i plugin di sicurezza

Testa BasicSecurityModule: gestione identità, cifratura,
firma digitale, autenticazione peer.
"""

import pytest
import asyncio
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'plugins', 'core', 'security'))

from laboon_chat2.core.interfaces import ISecurityModule
from laboon_chat2.utils.crypto_utils import CryptoUtils, KeyPair, EncryptedData, DigitalSignature
from basic_security import BasicSecurityModule, create_basic_security_module


@pytest.fixture
def temp_dir():
    """Crea directory temporanea per i test"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def crypto_utils():
    """Crea istanza CryptoUtils per i test"""
    return CryptoUtils()


@pytest.fixture
def security_config(temp_dir):
    """Configurazione di test per BasicSecurityModule"""
    return {
        "identity_file": str(Path(temp_dir) / "identity.json"),
        "trusted_peers_file": str(Path(temp_dir) / "trusted_peers.json"),
        "backup_identity": True,
        "backup_dir": str(Path(temp_dir) / "backups"),
        "key_rotation_interval": 3600,  # 1 ora per i test
        "session_key_ttl": 1800,  # 30 minuti per i test
        "max_trusted_peers": 100,
        "enable_peer_blacklist": True,
        "blacklist_file": str(Path(temp_dir) / "blacklist.json"),
        "maintenance_interval": 300  # 5 minuti per i test
    }


@pytest.fixture
async def security_module(security_config):
    """Crea istanza BasicSecurityModule per i test"""
    module = BasicSecurityModule()
    await module.initialize(security_config)
    yield module
    await module.cleanup()


@pytest.fixture
async def security_module_with_identity(security_config):
    """Crea BasicSecurityModule con identità generata"""
    module = BasicSecurityModule()
    await module.initialize(security_config)
    await module.generate_identity()
    yield module
    await module.cleanup()


class TestBasicSecurityModuleInterface:
    """Test per l'interfaccia ISecurityModule"""
    
    def test_implements_interface(self):
        """Testa che BasicSecurityModule implementi ISecurityModule"""
        module = BasicSecurityModule()
        assert isinstance(module, ISecurityModule)
    
    def test_module_info(self):
        """Testa informazioni del modulo"""
        module = BasicSecurityModule()
        info = module.get_module_info()
        
        assert info["name"] == "BasicSecurityModule"
        assert info["version"] == "1.0.0"
        assert info["type"] == "security"
        assert "description" in info
        assert "author" in info


class TestBasicSecurityModuleInitialization:
    """Test per l'inizializzazione del modulo"""
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, security_config):
        """Testa inizializzazione corretta"""
        module = BasicSecurityModule()
        
        await module.initialize(security_config)
        
        assert module.config == security_config
        assert module.crypto_utils is not None
        assert module.identity is None  # Non ancora generata
        assert module.trusted_peers == {}
        assert module.session_keys == {}
        assert module.blacklisted_peers == set()
        
        await module.cleanup()
    
    @pytest.mark.asyncio
    async def test_initialize_with_existing_identity(self, security_config, crypto_utils):
        """Testa inizializzazione con identità esistente"""
        # Crea identità di test
        identity = crypto_utils.generate_ed25519_keypair()
        identity_data = {
            "private_key": crypto_utils.encode_base64(identity.private_key),
            "public_key": crypto_utils.encode_base64(identity.public_key),
            "algorithm": identity.algorithm,
            "created_at": "2024-01-01T00:00:00Z"
        }
        
        # Salva identità
        identity_file = Path(security_config["identity_file"])
        identity_file.parent.mkdir(parents=True, exist_ok=True)
        with open(identity_file, 'w') as f:
            json.dump(identity_data, f)
        
        module = BasicSecurityModule()
        await module.initialize(security_config)
        
        assert module.identity is not None
        assert module.identity.algorithm == "Ed25519"
        
        await module.cleanup()
    
    @pytest.mark.asyncio
    async def test_initialize_creates_directories(self, security_config):
        """Testa che l'inizializzazione crei le directory necessarie"""
        module = BasicSecurityModule()
        await module.initialize(security_config)
        
        backup_dir = Path(security_config["backup_dir"])
        assert backup_dir.exists()
        assert backup_dir.is_dir()
        
        await module.cleanup()
    
    @pytest.mark.asyncio
    async def test_cleanup(self, security_module):
        """Testa cleanup del modulo"""
        # Aggiungi alcuni dati
        await security_module.generate_identity()
        session_key = security_module.crypto_utils.generate_symmetric_key(32)
        security_module.session_keys["test_peer"] = {
            "key": session_key,
            "created_at": asyncio.get_event_loop().time()
        }
        
        await security_module.cleanup()
        
        # Verifica che i dati sensibili siano stati puliti
        assert security_module.identity is None
        assert security_module.session_keys == {}


class TestIdentityManagement:
    """Test per la gestione dell'identità"""
    
    @pytest.mark.asyncio
    async def test_generate_identity(self, security_module):
        """Testa generazione identità"""
        await security_module.generate_identity()
        
        assert security_module.identity is not None
        assert security_module.identity.algorithm == "Ed25519"
        assert security_module.identity.private_key is not None
        assert security_module.identity.public_key is not None
        
        # Verifica che l'identità sia salvata su file
        identity_file = Path(security_module.config["identity_file"])
        assert identity_file.exists()
    
    @pytest.mark.asyncio
    async def test_load_identity(self, security_module_with_identity):
        """Testa caricamento identità"""
        original_identity = security_module_with_identity.identity
        
        # Simula riavvio del modulo
        new_module = BasicSecurityModule()
        await new_module.initialize(security_module_with_identity.config)
        
        assert new_module.identity is not None
        assert new_module.identity.public_key == original_identity.public_key
        
        await new_module.cleanup()
    
    @pytest.mark.asyncio
    async def test_get_identity(self, security_module_with_identity):
        """Testa recupero identità"""
        identity = await security_module_with_identity.get_identity()
        
        assert identity is not None
        assert identity == security_module_with_identity.identity.public_key
    
    @pytest.mark.asyncio
    async def test_get_identity_without_generation(self, security_module):
        """Testa recupero identità senza generazione"""
        identity = await security_module.get_identity()
        
        assert identity is None
    
    @pytest.mark.asyncio
    async def test_identity_backup(self, security_module):
        """Testa backup dell'identità"""
        await security_module.generate_identity()
        
        backup_dir = Path(security_module.config["backup_dir"])
        backup_files = list(backup_dir.glob("identity_backup_*.json"))
        
        assert len(backup_files) > 0
        
        # Verifica contenuto backup
        with open(backup_files[0], 'r') as f:
            backup_data = json.load(f)
        
        assert "private_key" in backup_data
        assert "public_key" in backup_data
        assert "algorithm" in backup_data
        assert "created_at" in backup_data


class TestEncryptionDecryption:
    """Test per cifratura e decifratura"""
    
    @pytest.mark.asyncio
    async def test_encrypt_message(self, security_module_with_identity):
        """Testa cifratura messaggio"""
        message = "Test message for encryption"
        recipient_key = security_module_with_identity.crypto_utils.generate_ed25519_keypair().public_key
        
        encrypted = await security_module_with_identity.encrypt_message(message, recipient_key)
        
        assert encrypted is not None
        assert encrypted != message
        assert isinstance(encrypted, str)  # Serializzato come JSON
    
    @pytest.mark.asyncio
    async def test_decrypt_message(self, security_module_with_identity):
        """Testa decifratura messaggio"""
        message = "Test message for decryption"
        
        # Cifra con la chiave pubblica del modulo
        recipient_key = security_module_with_identity.identity.public_key
        encrypted = await security_module_with_identity.encrypt_message(message, recipient_key)
        
        # Decifra
        decrypted = await security_module_with_identity.decrypt_message(encrypted)
        
        assert decrypted == message
    
    @pytest.mark.asyncio
    async def test_encrypt_decrypt_large_message(self, security_module_with_identity):
        """Testa cifratura/decifratura messaggio grande"""
        large_message = "A" * 10000  # 10KB
        recipient_key = security_module_with_identity.identity.public_key
        
        encrypted = await security_module_with_identity.encrypt_message(large_message, recipient_key)
        decrypted = await security_module_with_identity.decrypt_message(encrypted)
        
        assert decrypted == large_message
    
    @pytest.mark.asyncio
    async def test_decrypt_invalid_message(self, security_module_with_identity):
        """Testa decifratura messaggio invalido"""
        invalid_encrypted = "invalid encrypted message"
        
        decrypted = await security_module_with_identity.decrypt_message(invalid_encrypted)
        
        assert decrypted is None


class TestDigitalSignatures:
    """Test per le firme digitali"""
    
    @pytest.mark.asyncio
    async def test_sign_message(self, security_module_with_identity):
        """Testa firma messaggio"""
        message = "Test message for signing"
        
        signature = await security_module_with_identity.sign_message(message)
        
        assert signature is not None
        assert isinstance(signature, str)  # Serializzato come JSON
    
    @pytest.mark.asyncio
    async def test_verify_signature(self, security_module_with_identity):
        """Testa verifica firma"""
        message = "Test message for verification"
        
        signature = await security_module_with_identity.sign_message(message)
        is_valid = await security_module_with_identity.verify_signature(message, signature)
        
        assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_verify_signature_wrong_message(self, security_module_with_identity):
        """Testa verifica firma con messaggio modificato"""
        original_message = "Original message"
        modified_message = "Modified message"
        
        signature = await security_module_with_identity.sign_message(original_message)
        is_valid = await security_module_with_identity.verify_signature(modified_message, signature)
        
        assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_verify_invalid_signature(self, security_module_with_identity):
        """Testa verifica firma invalida"""
        message = "Test message"
        invalid_signature = "invalid signature"
        
        is_valid = await security_module_with_identity.verify_signature(message, invalid_signature)
        
        assert is_valid is False


class TestSessionKeyManagement:
    """Test per la gestione delle chiavi di sessione"""
    
    @pytest.mark.asyncio
    async def test_generate_session_key(self, security_module):
        """Testa generazione chiave di sessione"""
        peer_id = "test_peer_123"
        
        session_key = await security_module.generate_session_key(peer_id)
        
        assert session_key is not None
        assert isinstance(session_key, bytes)
        assert len(session_key) == 32  # AES-256
        assert peer_id in security_module.session_keys
    
    @pytest.mark.asyncio
    async def test_get_session_key(self, security_module):
        """Testa recupero chiave di sessione"""
        peer_id = "test_peer_123"
        
        # Genera chiave
        original_key = await security_module.generate_session_key(peer_id)
        
        # Recupera chiave
        retrieved_key = await security_module.get_session_key(peer_id)
        
        assert retrieved_key == original_key
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_session_key(self, security_module):
        """Testa recupero chiave di sessione inesistente"""
        peer_id = "nonexistent_peer"
        
        session_key = await security_module.get_session_key(peer_id)
        
        assert session_key is None
    
    @pytest.mark.asyncio
    async def test_revoke_session_key(self, security_module):
        """Testa revoca chiave di sessione"""
        peer_id = "test_peer_123"
        
        # Genera chiave
        await security_module.generate_session_key(peer_id)
        assert peer_id in security_module.session_keys
        
        # Revoca chiave
        await security_module.revoke_session_key(peer_id)
        assert peer_id not in security_module.session_keys
    
    @pytest.mark.asyncio
    async def test_session_key_ttl(self, security_module):
        """Testa TTL delle chiavi di sessione"""
        peer_id = "test_peer_123"
        
        # Genera chiave con TTL breve
        security_module.config["session_key_ttl"] = 0.1  # 100ms
        await security_module.generate_session_key(peer_id)
        
        # Aspetta scadenza
        await asyncio.sleep(0.2)
        
        # Verifica che la chiave sia scaduta
        session_key = await security_module.get_session_key(peer_id)
        assert session_key is None


class TestPeerAuthentication:
    """Test per l'autenticazione dei peer"""
    
    @pytest.mark.asyncio
    async def test_authenticate_peer(self, security_module_with_identity, crypto_utils):
        """Testa autenticazione peer"""
        # Crea peer di test
        peer_identity = crypto_utils.generate_ed25519_keypair()
        peer_id = "test_peer_123"
        challenge = "authentication_challenge"
        
        # Firma la challenge con la chiave del peer
        signature = crypto_utils.sign_data(
            challenge.encode(),
            peer_identity.private_key,
            "Ed25519"
        )
        signature_str = crypto_utils.serialize_digital_signature(signature)
        
        # Autentica
        is_authenticated = await security_module_with_identity.authenticate_peer(
            peer_id, peer_identity.public_key, challenge, signature_str
        )
        
        assert is_authenticated is True
    
    @pytest.mark.asyncio
    async def test_authenticate_peer_wrong_signature(self, security_module_with_identity, crypto_utils):
        """Testa autenticazione peer con firma sbagliata"""
        peer_identity = crypto_utils.generate_ed25519_keypair()
        wrong_identity = crypto_utils.generate_ed25519_keypair()
        peer_id = "test_peer_123"
        challenge = "authentication_challenge"
        
        # Firma con chiave sbagliata
        signature = crypto_utils.sign_data(
            challenge.encode(),
            wrong_identity.private_key,
            "Ed25519"
        )
        signature_str = crypto_utils.serialize_digital_signature(signature)
        
        # Autentica
        is_authenticated = await security_module_with_identity.authenticate_peer(
            peer_id, peer_identity.public_key, challenge, signature_str
        )
        
        assert is_authenticated is False


class TestTrustedPeerManagement:
    """Test per la gestione dei peer fidati"""
    
    @pytest.mark.asyncio
    async def test_add_trusted_peer(self, security_module, crypto_utils):
        """Testa aggiunta peer fidato"""
        peer_id = "trusted_peer_123"
        peer_key = crypto_utils.generate_ed25519_keypair().public_key
        
        await security_module.add_trusted_peer(peer_id, peer_key)
        
        assert peer_id in security_module.trusted_peers
        assert security_module.trusted_peers[peer_id]["public_key"] == peer_key
        
        # Verifica salvataggio su file
        trusted_peers_file = Path(security_module.config["trusted_peers_file"])
        assert trusted_peers_file.exists()
    
    @pytest.mark.asyncio
    async def test_remove_trusted_peer(self, security_module, crypto_utils):
        """Testa rimozione peer fidato"""
        peer_id = "trusted_peer_123"
        peer_key = crypto_utils.generate_ed25519_keypair().public_key
        
        # Aggiungi peer
        await security_module.add_trusted_peer(peer_id, peer_key)
        assert peer_id in security_module.trusted_peers
        
        # Rimuovi peer
        await security_module.remove_trusted_peer(peer_id)
        assert peer_id not in security_module.trusted_peers
    
    @pytest.mark.asyncio
    async def test_is_trusted_peer(self, security_module, crypto_utils):
        """Testa verifica peer fidato"""
        peer_id = "trusted_peer_123"
        peer_key = crypto_utils.generate_ed25519_keypair().public_key
        
        # Prima dell'aggiunta
        is_trusted = await security_module.is_trusted_peer(peer_id)
        assert is_trusted is False
        
        # Dopo l'aggiunta
        await security_module.add_trusted_peer(peer_id, peer_key)
        is_trusted = await security_module.is_trusted_peer(peer_id)
        assert is_trusted is True
    
    @pytest.mark.asyncio
    async def test_max_trusted_peers_limit(self, security_module, crypto_utils):
        """Testa limite massimo peer fidati"""
        security_module.config["max_trusted_peers"] = 2
        
        # Aggiungi peer fino al limite
        for i in range(2):
            peer_id = f"peer_{i}"
            peer_key = crypto_utils.generate_ed25519_keypair().public_key
            await security_module.add_trusted_peer(peer_id, peer_key)
        
        # Prova ad aggiungere oltre il limite
        peer_id = "peer_overflow"
        peer_key = crypto_utils.generate_ed25519_keypair().public_key
        
        with pytest.raises(Exception):  # Dovrebbe sollevare eccezione
            await security_module.add_trusted_peer(peer_id, peer_key)


class TestPeerBlacklist:
    """Test per la blacklist dei peer"""
    
    @pytest.mark.asyncio
    async def test_blacklist_peer(self, security_module):
        """Testa blacklist peer"""
        peer_id = "bad_peer_123"
        
        await security_module.blacklist_peer(peer_id)
        
        assert peer_id in security_module.blacklisted_peers
        
        # Verifica salvataggio su file
        blacklist_file = Path(security_module.config["blacklist_file"])
        assert blacklist_file.exists()
    
    @pytest.mark.asyncio
    async def test_unblacklist_peer(self, security_module):
        """Testa rimozione dalla blacklist"""
        peer_id = "bad_peer_123"
        
        # Aggiungi alla blacklist
        await security_module.blacklist_peer(peer_id)
        assert peer_id in security_module.blacklisted_peers
        
        # Rimuovi dalla blacklist
        await security_module.unblacklist_peer(peer_id)
        assert peer_id not in security_module.blacklisted_peers
    
    @pytest.mark.asyncio
    async def test_is_blacklisted(self, security_module):
        """Testa verifica blacklist"""
        peer_id = "bad_peer_123"
        
        # Prima della blacklist
        is_blacklisted = await security_module.is_blacklisted(peer_id)
        assert is_blacklisted is False
        
        # Dopo la blacklist
        await security_module.blacklist_peer(peer_id)
        is_blacklisted = await security_module.is_blacklisted(peer_id)
        assert is_blacklisted is True


class TestKeyRotation:
    """Test per la rotazione delle chiavi"""
    
    @pytest.mark.asyncio
    async def test_rotate_identity_key(self, security_module_with_identity):
        """Testa rotazione chiave identità"""
        original_identity = security_module_with_identity.identity
        
        await security_module_with_identity.rotate_identity_key()
        
        new_identity = security_module_with_identity.identity
        
        assert new_identity is not None
        assert new_identity.public_key != original_identity.public_key
        assert new_identity.algorithm == original_identity.algorithm
    
    @pytest.mark.asyncio
    async def test_periodic_maintenance(self, security_module_with_identity):
        """Testa manutenzione periodica"""
        # Aggiungi chiave di sessione scaduta
        peer_id = "test_peer"
        security_module_with_identity.session_keys[peer_id] = {
            "key": b"test_key",
            "created_at": asyncio.get_event_loop().time() - 10000  # Molto vecchia
        }
        
        # Esegui manutenzione
        await security_module_with_identity._periodic_maintenance()
        
        # Verifica che la chiave scaduta sia stata rimossa
        assert peer_id not in security_module_with_identity.session_keys


class TestConfigurationUpdate:
    """Test per l'aggiornamento della configurazione"""
    
    @pytest.mark.asyncio
    async def test_update_config(self, security_module):
        """Testa aggiornamento configurazione"""
        new_config = {
            "session_key_ttl": 7200,  # 2 ore
            "max_trusted_peers": 200
        }
        
        await security_module.update_config(new_config)
        
        assert security_module.config["session_key_ttl"] == 7200
        assert security_module.config["max_trusted_peers"] == 200


class TestFactoryFunction:
    """Test per la funzione factory"""
    
    @pytest.mark.asyncio
    async def test_create_basic_security_module(self, security_config):
        """Testa funzione factory create_basic_security_module"""
        module = await create_basic_security_module(security_config)
        
        assert isinstance(module, BasicSecurityModule)
        assert module.config == security_config
        
        await module.cleanup()


@pytest.mark.asyncio
async def test_basic_security_module_integration():
    """Test di integrazione completo per BasicSecurityModule"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = {
            "identity_file": str(Path(temp_dir) / "identity.json"),
            "trusted_peers_file": str(Path(temp_dir) / "trusted_peers.json"),
            "backup_identity": True,
            "backup_dir": str(Path(temp_dir) / "backups"),
            "key_rotation_interval": 3600,
            "session_key_ttl": 1800,
            "max_trusted_peers": 100,
            "enable_peer_blacklist": True,
            "blacklist_file": str(Path(temp_dir) / "blacklist.json"),
            "maintenance_interval": 300
        }
        
        # Crea due moduli per simulare comunicazione peer-to-peer
        module1 = BasicSecurityModule()
        module2 = BasicSecurityModule()
        
        await module1.initialize(config)
        await module2.initialize(config)
        
        # Genera identità
        await module1.generate_identity()
        await module2.generate_identity()
        
        # Test comunicazione sicura
        message = "Secret message between peers"
        
        # Module1 cifra per Module2
        encrypted = await module1.encrypt_message(message, module2.identity.public_key)
        
        # Module2 decifra
        decrypted = await module2.decrypt_message(encrypted)
        assert decrypted == message
        
        # Test firma digitale
        signature = await module1.sign_message(message)
        is_valid = await module1.verify_signature(message, signature)
        assert is_valid is True
        
        # Test gestione peer fidati
        peer_id = "module2"
        await module1.add_trusted_peer(peer_id, module2.identity.public_key)
        is_trusted = await module1.is_trusted_peer(peer_id)
        assert is_trusted is True
        
        # Test autenticazione
        challenge = "auth_challenge_123"
        signature = module2.crypto_utils.sign_data(
            challenge.encode(),
            module2.identity.private_key,
            "Ed25519"
        )
        signature_str = module2.crypto_utils.serialize_digital_signature(signature)
        
        is_authenticated = await module1.authenticate_peer(
            peer_id, module2.identity.public_key, challenge, signature_str
        )
        assert is_authenticated is True
        
        # Test chiavi di sessione
        session_key = await module1.generate_session_key(peer_id)
        retrieved_key = await module1.get_session_key(peer_id)
        assert session_key == retrieved_key
        
        # Cleanup
        await module1.cleanup()
        await module2.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])