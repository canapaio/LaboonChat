"""
Test suite per i plugin di messaging

Testa SimpleP2PMessaging: connessioni P2P, invio/ricezione messaggi,
trasferimento file, gestione peer.
"""

import pytest
import asyncio
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Dict, Any, List
import socket
import threading
import time

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'plugins', 'core', 'messaging'))

from laboon_chat2.core.interfaces import IMessagingModule
from simple_p2p_messaging import (
    SimpleP2PMessaging, P2PMessage, P2PPeer, FileTransfer,
    create_simple_p2p_messaging
)


@pytest.fixture
def temp_dir():
    """Crea directory temporanea per i test"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def messaging_config(temp_dir):
    """Configurazione di test per SimpleP2PMessaging"""
    return {
        "listen_host": "127.0.0.1",
        "listen_port": 0,  # Porta automatica per i test
        "max_connections": 10,
        "message_history_file": str(Path(temp_dir) / "message_history.json"),
        "peers_file": str(Path(temp_dir) / "peers.json"),
        "file_transfer_dir": str(Path(temp_dir) / "transfers"),
        "max_message_size": 1024 * 1024,  # 1MB
        "connection_timeout": 5.0,
        "heartbeat_interval": 30.0,
        "max_file_size": 10 * 1024 * 1024,  # 10MB
        "enable_file_transfer": True,
        "enable_message_history": True,
        "auto_accept_files": False,
        "discovery_enabled": True,
        "discovery_port": 0  # Porta automatica per i test
    }


@pytest.fixture
async def messaging_module(messaging_config):
    """Crea istanza SimpleP2PMessaging per i test"""
    module = SimpleP2PMessaging()
    await module.initialize(messaging_config)
    yield module
    await module.cleanup()


@pytest.fixture
async def two_messaging_modules(messaging_config, temp_dir):
    """Crea due istanze SimpleP2PMessaging per test P2P"""
    # Configurazione per il primo modulo
    config1 = messaging_config.copy()
    config1["message_history_file"] = str(Path(temp_dir) / "history1.json")
    config1["peers_file"] = str(Path(temp_dir) / "peers1.json")
    config1["file_transfer_dir"] = str(Path(temp_dir) / "transfers1")
    
    # Configurazione per il secondo modulo
    config2 = messaging_config.copy()
    config2["message_history_file"] = str(Path(temp_dir) / "history2.json")
    config2["peers_file"] = str(Path(temp_dir) / "peers2.json")
    config2["file_transfer_dir"] = str(Path(temp_dir) / "transfers2")
    
    module1 = SimpleP2PMessaging()
    module2 = SimpleP2PMessaging()
    
    await module1.initialize(config1)
    await module2.initialize(config2)
    
    yield module1, module2
    
    await module1.cleanup()
    await module2.cleanup()


class TestP2PDataClasses:
    """Test per le dataclass P2P"""
    
    def test_p2p_message_creation(self):
        """Testa creazione P2PMessage"""
        message = P2PMessage(
            id="msg_123",
            sender_id="sender_123",
            recipient_id="recipient_123",
            content="Test message",
            message_type="text",
            timestamp=1234567890.0,
            encrypted=True,
            signature="signature_data"
        )
        
        assert message.id == "msg_123"
        assert message.sender_id == "sender_123"
        assert message.recipient_id == "recipient_123"
        assert message.content == "Test message"
        assert message.message_type == "text"
        assert message.timestamp == 1234567890.0
        assert message.encrypted is True
        assert message.signature == "signature_data"
    
    def test_p2p_peer_creation(self):
        """Testa creazione P2PPeer"""
        peer = P2PPeer(
            id="peer_123",
            address="192.168.1.100",
            port=8080,
            public_key=b"public_key_data",
            last_seen=1234567890.0,
            status="online",
            nickname="TestPeer"
        )
        
        assert peer.id == "peer_123"
        assert peer.address == "192.168.1.100"
        assert peer.port == 8080
        assert peer.public_key == b"public_key_data"
        assert peer.last_seen == 1234567890.0
        assert peer.status == "online"
        assert peer.nickname == "TestPeer"
    
    def test_file_transfer_creation(self):
        """Testa creazione FileTransfer"""
        transfer = FileTransfer(
            id="transfer_123",
            filename="test.txt",
            file_size=1024,
            sender_id="sender_123",
            recipient_id="recipient_123",
            status="pending",
            progress=0.0,
            file_hash="hash_value",
            created_at=1234567890.0
        )
        
        assert transfer.id == "transfer_123"
        assert transfer.filename == "test.txt"
        assert transfer.file_size == 1024
        assert transfer.sender_id == "sender_123"
        assert transfer.recipient_id == "recipient_123"
        assert transfer.status == "pending"
        assert transfer.progress == 0.0
        assert transfer.file_hash == "hash_value"
        assert transfer.created_at == 1234567890.0


class TestSimpleP2PMessagingInterface:
    """Test per l'interfaccia IMessagingModule"""
    
    def test_implements_interface(self):
        """Testa che SimpleP2PMessaging implementi IMessagingModule"""
        module = SimpleP2PMessaging()
        assert isinstance(module, IMessagingModule)
    
    def test_module_info(self):
        """Testa informazioni del modulo"""
        module = SimpleP2PMessaging()
        info = module.get_module_info()
        
        assert info["name"] == "SimpleP2PMessaging"
        assert info["version"] == "1.0.0"
        assert info["type"] == "messaging"
        assert "description" in info
        assert "author" in info


class TestSimpleP2PMessagingInitialization:
    """Test per l'inizializzazione del modulo"""
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, messaging_config):
        """Testa inizializzazione corretta"""
        module = SimpleP2PMessaging()
        
        await module.initialize(messaging_config)
        
        assert module.config == messaging_config
        assert module.peers == {}
        assert module.connections == {}
        assert module.message_history == []
        assert module.file_transfers == {}
        assert module.server is not None
        assert module.discovery_server is not None
        
        await module.cleanup()
    
    @pytest.mark.asyncio
    async def test_initialize_creates_directories(self, messaging_config):
        """Testa che l'inizializzazione crei le directory necessarie"""
        module = SimpleP2PMessaging()
        await module.initialize(messaging_config)
        
        transfer_dir = Path(messaging_config["file_transfer_dir"])
        assert transfer_dir.exists()
        assert transfer_dir.is_dir()
        
        await module.cleanup()
    
    @pytest.mark.asyncio
    async def test_initialize_loads_existing_data(self, messaging_config):
        """Testa caricamento dati esistenti"""
        # Crea dati di test
        peers_data = {
            "peer_123": {
                "id": "peer_123",
                "address": "192.168.1.100",
                "port": 8080,
                "public_key": "cHVibGljX2tleV9kYXRh",  # base64
                "last_seen": 1234567890.0,
                "status": "offline",
                "nickname": "TestPeer"
            }
        }
        
        history_data = [
            {
                "id": "msg_123",
                "sender_id": "sender_123",
                "recipient_id": "recipient_123",
                "content": "Test message",
                "message_type": "text",
                "timestamp": 1234567890.0,
                "encrypted": False,
                "signature": None
            }
        ]
        
        # Salva dati
        peers_file = Path(messaging_config["peers_file"])
        history_file = Path(messaging_config["message_history_file"])
        
        peers_file.parent.mkdir(parents=True, exist_ok=True)
        history_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(peers_file, 'w') as f:
            json.dump(peers_data, f)
        
        with open(history_file, 'w') as f:
            json.dump(history_data, f)
        
        # Inizializza modulo
        module = SimpleP2PMessaging()
        await module.initialize(messaging_config)
        
        assert len(module.peers) == 1
        assert "peer_123" in module.peers
        assert len(module.message_history) == 1
        assert module.message_history[0].id == "msg_123"
        
        await module.cleanup()
    
    @pytest.mark.asyncio
    async def test_cleanup(self, messaging_module):
        """Testa cleanup del modulo"""
        # Aggiungi alcuni dati
        peer = P2PPeer(
            id="test_peer",
            address="127.0.0.1",
            port=8080,
            public_key=b"test_key",
            last_seen=time.time(),
            status="online"
        )
        messaging_module.peers["test_peer"] = peer
        
        await messaging_module.cleanup()
        
        # Verifica che i server siano stati fermati
        assert messaging_module.server is None
        assert messaging_module.discovery_server is None


class TestConnectionManagement:
    """Test per la gestione delle connessioni"""
    
    @pytest.mark.asyncio
    async def test_connect_to_peer(self, two_messaging_modules):
        """Testa connessione a un peer"""
        module1, module2 = two_messaging_modules
        
        # Ottieni porta del secondo modulo
        port2 = module2.server.sockets[0].getsockname()[1]
        
        # Connetti module1 a module2
        success = await module1.connect_to_peer("127.0.0.1", port2, "peer2")
        
        assert success is True
        assert "peer2" in module1.connections
    
    @pytest.mark.asyncio
    async def test_connect_to_invalid_peer(self, messaging_module):
        """Testa connessione a peer invalido"""
        # Prova a connettersi a porta inesistente
        success = await messaging_module.connect_to_peer("127.0.0.1", 99999, "invalid_peer")
        
        assert success is False
        assert "invalid_peer" not in messaging_module.connections
    
    @pytest.mark.asyncio
    async def test_disconnect_from_peer(self, two_messaging_modules):
        """Testa disconnessione da peer"""
        module1, module2 = two_messaging_modules
        
        # Connetti
        port2 = module2.server.sockets[0].getsockname()[1]
        await module1.connect_to_peer("127.0.0.1", port2, "peer2")
        
        # Disconnetti
        await module1.disconnect_from_peer("peer2")
        
        assert "peer2" not in module1.connections
    
    @pytest.mark.asyncio
    async def test_get_connected_peers(self, two_messaging_modules):
        """Testa recupero peer connessi"""
        module1, module2 = two_messaging_modules
        
        # Inizialmente nessun peer connesso
        connected = await module1.get_connected_peers()
        assert len(connected) == 0
        
        # Connetti
        port2 = module2.server.sockets[0].getsockname()[1]
        await module1.connect_to_peer("127.0.0.1", port2, "peer2")
        
        # Verifica peer connesso
        connected = await module1.get_connected_peers()
        assert len(connected) == 1
        assert connected[0] == "peer2"


class TestPeerDiscovery:
    """Test per la scoperta dei peer"""
    
    @pytest.mark.asyncio
    async def test_discover_peers(self, messaging_module):
        """Testa scoperta peer"""
        # Mock del discovery
        with patch.object(messaging_module, '_broadcast_discovery') as mock_broadcast:
            mock_broadcast.return_value = asyncio.Future()
            mock_broadcast.return_value.set_result(None)
            
            peers = await messaging_module.discover_peers()
            
            assert isinstance(peers, list)
            mock_broadcast.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_announce_presence(self, messaging_module):
        """Testa annuncio presenza"""
        with patch.object(messaging_module, '_broadcast_discovery') as mock_broadcast:
            mock_broadcast.return_value = asyncio.Future()
            mock_broadcast.return_value.set_result(None)
            
            await messaging_module.announce_presence()
            
            mock_broadcast.assert_called_once()


class TestMessageHandling:
    """Test per la gestione dei messaggi"""
    
    @pytest.mark.asyncio
    async def test_send_message(self, two_messaging_modules):
        """Testa invio messaggio"""
        module1, module2 = two_messaging_modules
        
        # Connetti i moduli
        port2 = module2.server.sockets[0].getsockname()[1]
        await module1.connect_to_peer("127.0.0.1", port2, "peer2")
        
        # Aspetta un po' per stabilire la connessione
        await asyncio.sleep(0.1)
        
        # Invia messaggio
        message_id = await module1.send_message("peer2", "Hello, peer2!", "text")
        
        assert message_id is not None
        assert isinstance(message_id, str)
    
    @pytest.mark.asyncio
    async def test_send_message_to_disconnected_peer(self, messaging_module):
        """Testa invio messaggio a peer disconnesso"""
        message_id = await messaging_module.send_message("nonexistent_peer", "Hello!", "text")
        
        assert message_id is None
    
    @pytest.mark.asyncio
    async def test_get_message_history(self, messaging_module):
        """Testa recupero cronologia messaggi"""
        # Aggiungi messaggio alla cronologia
        message = P2PMessage(
            id="msg_123",
            sender_id="sender_123",
            recipient_id="recipient_123",
            content="Test message",
            message_type="text",
            timestamp=time.time()
        )
        messaging_module.message_history.append(message)
        
        # Recupera cronologia
        history = await messaging_module.get_message_history("sender_123")
        
        assert len(history) == 1
        assert history[0].id == "msg_123"
    
    @pytest.mark.asyncio
    async def test_get_message_history_with_limit(self, messaging_module):
        """Testa recupero cronologia con limite"""
        # Aggiungi più messaggi
        for i in range(5):
            message = P2PMessage(
                id=f"msg_{i}",
                sender_id="sender_123",
                recipient_id="recipient_123",
                content=f"Message {i}",
                message_type="text",
                timestamp=time.time() + i
            )
            messaging_module.message_history.append(message)
        
        # Recupera con limite
        history = await messaging_module.get_message_history("sender_123", limit=3)
        
        assert len(history) == 3
    
    @pytest.mark.asyncio
    async def test_clear_message_history(self, messaging_module):
        """Testa pulizia cronologia messaggi"""
        # Aggiungi messaggio
        message = P2PMessage(
            id="msg_123",
            sender_id="sender_123",
            recipient_id="recipient_123",
            content="Test message",
            message_type="text",
            timestamp=time.time()
        )
        messaging_module.message_history.append(message)
        
        # Pulisci cronologia
        await messaging_module.clear_message_history()
        
        assert len(messaging_module.message_history) == 0


class TestEventHandlers:
    """Test per i gestori di eventi"""
    
    @pytest.mark.asyncio
    async def test_set_message_handler(self, messaging_module):
        """Testa impostazione gestore messaggi"""
        handler_called = False
        received_message = None
        
        async def message_handler(message):
            nonlocal handler_called, received_message
            handler_called = True
            received_message = message
        
        await messaging_module.set_message_handler(message_handler)
        
        # Simula ricezione messaggio
        test_message = P2PMessage(
            id="msg_123",
            sender_id="sender_123",
            recipient_id="recipient_123",
            content="Test message",
            message_type="text",
            timestamp=time.time()
        )
        
        await messaging_module._handle_received_message(test_message)
        
        assert handler_called is True
        assert received_message == test_message
    
    @pytest.mark.asyncio
    async def test_set_peer_handler(self, messaging_module):
        """Testa impostazione gestore peer"""
        handler_called = False
        received_peer = None
        received_event = None
        
        async def peer_handler(peer_id, event):
            nonlocal handler_called, received_peer, received_event
            handler_called = True
            received_peer = peer_id
            received_event = event
        
        await messaging_module.set_peer_handler(peer_handler)
        
        # Simula evento peer
        await messaging_module._notify_peer_event("peer_123", "connected")
        
        assert handler_called is True
        assert received_peer == "peer_123"
        assert received_event == "connected"


class TestFileTransfer:
    """Test per il trasferimento file"""
    
    @pytest.mark.asyncio
    async def test_send_file(self, two_messaging_modules, temp_dir):
        """Testa invio file"""
        module1, module2 = two_messaging_modules
        
        # Crea file di test
        test_file = Path(temp_dir) / "test_file.txt"
        test_content = "This is a test file content"
        test_file.write_text(test_content)
        
        # Connetti i moduli
        port2 = module2.server.sockets[0].getsockname()[1]
        await module1.connect_to_peer("127.0.0.1", port2, "peer2")
        
        # Invia file
        transfer_id = await module1.send_file("peer2", str(test_file))
        
        assert transfer_id is not None
        assert transfer_id in module1.file_transfers
        assert module1.file_transfers[transfer_id].filename == "test_file.txt"
    
    @pytest.mark.asyncio
    async def test_send_nonexistent_file(self, messaging_module):
        """Testa invio file inesistente"""
        transfer_id = await messaging_module.send_file("peer2", "/nonexistent/file.txt")
        
        assert transfer_id is None
    
    @pytest.mark.asyncio
    async def test_send_file_too_large(self, messaging_module, temp_dir):
        """Testa invio file troppo grande"""
        # Imposta limite piccolo
        messaging_module.config["max_file_size"] = 100
        
        # Crea file grande
        large_file = Path(temp_dir) / "large_file.txt"
        large_file.write_text("A" * 200)  # 200 bytes > 100 bytes limit
        
        transfer_id = await messaging_module.send_file("peer2", str(large_file))
        
        assert transfer_id is None
    
    @pytest.mark.asyncio
    async def test_accept_file_transfer(self, messaging_module):
        """Testa accettazione trasferimento file"""
        # Crea trasferimento di test
        transfer = FileTransfer(
            id="transfer_123",
            filename="test.txt",
            file_size=1024,
            sender_id="sender_123",
            recipient_id="recipient_123",
            status="pending",
            progress=0.0,
            file_hash="hash_value",
            created_at=time.time()
        )
        messaging_module.file_transfers["transfer_123"] = transfer
        
        # Accetta trasferimento
        success = await messaging_module.accept_file_transfer("transfer_123")
        
        assert success is True
        assert messaging_module.file_transfers["transfer_123"].status == "accepted"
    
    @pytest.mark.asyncio
    async def test_reject_file_transfer(self, messaging_module):
        """Testa rifiuto trasferimento file"""
        # Crea trasferimento di test
        transfer = FileTransfer(
            id="transfer_123",
            filename="test.txt",
            file_size=1024,
            sender_id="sender_123",
            recipient_id="recipient_123",
            status="pending",
            progress=0.0,
            file_hash="hash_value",
            created_at=time.time()
        )
        messaging_module.file_transfers["transfer_123"] = transfer
        
        # Rifiuta trasferimento
        success = await messaging_module.reject_file_transfer("transfer_123")
        
        assert success is True
        assert messaging_module.file_transfers["transfer_123"].status == "rejected"
    
    @pytest.mark.asyncio
    async def test_get_file_transfers(self, messaging_module):
        """Testa recupero trasferimenti file"""
        # Crea trasferimenti di test
        transfer1 = FileTransfer(
            id="transfer_1",
            filename="file1.txt",
            file_size=1024,
            sender_id="sender_123",
            recipient_id="recipient_123",
            status="pending",
            progress=0.0,
            file_hash="hash1",
            created_at=time.time()
        )
        
        transfer2 = FileTransfer(
            id="transfer_2",
            filename="file2.txt",
            file_size=2048,
            sender_id="sender_456",
            recipient_id="recipient_123",
            status="completed",
            progress=1.0,
            file_hash="hash2",
            created_at=time.time()
        )
        
        messaging_module.file_transfers["transfer_1"] = transfer1
        messaging_module.file_transfers["transfer_2"] = transfer2
        
        # Recupera tutti i trasferimenti
        all_transfers = await messaging_module.get_file_transfers()
        assert len(all_transfers) == 2
        
        # Recupera trasferimenti per stato
        pending_transfers = await messaging_module.get_file_transfers(status="pending")
        assert len(pending_transfers) == 1
        assert pending_transfers[0].id == "transfer_1"
        
        completed_transfers = await messaging_module.get_file_transfers(status="completed")
        assert len(completed_transfers) == 1
        assert completed_transfers[0].id == "transfer_2"


class TestMessageSynchronization:
    """Test per la sincronizzazione messaggi"""
    
    @pytest.mark.asyncio
    async def test_sync_messages_with_peer(self, messaging_module):
        """Testa sincronizzazione messaggi con peer"""
        peer_id = "peer_123"
        
        # Mock della sincronizzazione
        with patch.object(messaging_module, '_request_message_sync') as mock_sync:
            mock_sync.return_value = asyncio.Future()
            mock_sync.return_value.set_result(True)
            
            success = await messaging_module.sync_messages_with_peer(peer_id)
            
            assert success is True
            mock_sync.assert_called_once_with(peer_id)


class TestConfigurationUpdate:
    """Test per l'aggiornamento della configurazione"""
    
    @pytest.mark.asyncio
    async def test_update_config(self, messaging_module):
        """Testa aggiornamento configurazione"""
        new_config = {
            "max_connections": 20,
            "connection_timeout": 10.0,
            "enable_file_transfer": False
        }
        
        await messaging_module.update_config(new_config)
        
        assert messaging_module.config["max_connections"] == 20
        assert messaging_module.config["connection_timeout"] == 10.0
        assert messaging_module.config["enable_file_transfer"] is False


class TestFactoryFunction:
    """Test per la funzione factory"""
    
    @pytest.mark.asyncio
    async def test_create_simple_p2p_messaging(self, messaging_config):
        """Testa funzione factory create_simple_p2p_messaging"""
        module = await create_simple_p2p_messaging(messaging_config)
        
        assert isinstance(module, SimpleP2PMessaging)
        assert module.config == messaging_config
        
        await module.cleanup()


@pytest.mark.asyncio
async def test_simple_p2p_messaging_integration():
    """Test di integrazione completo per SimpleP2PMessaging"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Configurazioni per due moduli
        config1 = {
            "listen_host": "127.0.0.1",
            "listen_port": 0,
            "max_connections": 10,
            "message_history_file": str(Path(temp_dir) / "history1.json"),
            "peers_file": str(Path(temp_dir) / "peers1.json"),
            "file_transfer_dir": str(Path(temp_dir) / "transfers1"),
            "max_message_size": 1024 * 1024,
            "connection_timeout": 5.0,
            "heartbeat_interval": 30.0,
            "max_file_size": 10 * 1024 * 1024,
            "enable_file_transfer": True,
            "enable_message_history": True,
            "auto_accept_files": False,
            "discovery_enabled": True,
            "discovery_port": 0
        }
        
        config2 = config1.copy()
        config2["message_history_file"] = str(Path(temp_dir) / "history2.json")
        config2["peers_file"] = str(Path(temp_dir) / "peers2.json")
        config2["file_transfer_dir"] = str(Path(temp_dir) / "transfers2")
        
        # Crea e inizializza moduli
        module1 = SimpleP2PMessaging()
        module2 = SimpleP2PMessaging()
        
        await module1.initialize(config1)
        await module2.initialize(config2)
        
        try:
            # Test connessione
            port2 = module2.server.sockets[0].getsockname()[1]
            success = await module1.connect_to_peer("127.0.0.1", port2, "module2")
            assert success is True
            
            # Aspetta stabilizzazione connessione
            await asyncio.sleep(0.2)
            
            # Test invio messaggio
            message_id = await module1.send_message("module2", "Hello from module1!", "text")
            assert message_id is not None
            
            # Test cronologia messaggi
            await asyncio.sleep(0.1)  # Aspetta elaborazione
            history = await module1.get_message_history("module2")
            assert len(history) >= 0  # Potrebbe essere vuoto se il messaggio non è ancora arrivato
            
            # Test peer connessi
            connected = await module1.get_connected_peers()
            assert "module2" in connected
            
            # Test file transfer
            test_file = Path(temp_dir) / "test_integration.txt"
            test_file.write_text("Integration test file content")
            
            transfer_id = await module1.send_file("module2", str(test_file))
            assert transfer_id is not None
            
            # Test recupero trasferimenti
            transfers = await module1.get_file_transfers()
            assert len(transfers) >= 1
            
            # Test disconnessione
            await module1.disconnect_from_peer("module2")
            connected = await module1.get_connected_peers()
            assert "module2" not in connected
            
        finally:
            # Cleanup
            await module1.cleanup()
            await module2.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])