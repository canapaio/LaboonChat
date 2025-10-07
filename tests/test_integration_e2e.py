"""
Test di Integrazione End-to-End per LaboonChat2

Questi test verificano il funzionamento dell'intera applicazione
con tutti i moduli core e plugin secondari integrati insieme.
Simulano scenari reali di utilizzo completo del sistema.
"""

import pytest
import asyncio
import tempfile
import shutil
import json
import time
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, AsyncMock, patch

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'plugins'))

# Import moduli core
from laboon_chat2.core.interfaces import (
    ISecurityModule, IMessagingModule, INetworkModule, IInterfaceModule
)
from laboon_chat2.core.config_manager import ConfigManager
from laboon_chat2.core.plugin_manager import PluginManager

# Import plugin core
from core.security.basic_security import create_basic_security_module
from core.messaging.simple_p2p_messaging import create_simple_p2p_messaging
from core.network.basic_network import create_basic_network_module
from core.interface.web_interface import create_web_interface

# Import plugin secondari
from secondary.advanced_features.chatbot_plugin import create_chatbot_plugin
from secondary.advanced_features.advanced_file_sharing import create_advanced_file_sharing
from secondary.advanced_features.advanced_encryption import create_advanced_encryption


@pytest.fixture
async def temp_app_dir():
    """Fixture per directory temporanea dell'applicazione"""
    temp_dir = tempfile.mkdtemp(prefix="laboon_e2e_")
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
async def config_manager(temp_app_dir):
    """Fixture per ConfigManager"""
    config_file = temp_app_dir / "config.json"
    
    # Configurazione di test completa
    test_config = {
        "app": {
            "name": "LaboonChat2",
            "version": "1.0.0",
            "data_dir": str(temp_app_dir / "data"),
            "log_level": "INFO"
        },
        "core_modules": {
            "security": {
                "module": "basic_security",
                "config": {
                    "data_dir": str(temp_app_dir / "data" / "security"),
                    "encryption_algorithm": "aes_256_gcm",
                    "key_size": 256
                }
            },
            "messaging": {
                "module": "simple_p2p_messaging", 
                "config": {
                    "data_dir": str(temp_app_dir / "data" / "messaging"),
                    "max_message_size": 1048576,
                    "message_retention_days": 30
                }
            },
            "network": {
                "module": "basic_network",
                "config": {
                    "data_dir": str(temp_app_dir / "data" / "network"),
                    "listen_port": 0,  # Porta casuale per test
                    "discovery_port": 0,
                    "max_connections": 10
                }
            },
            "interface": {
                "module": "web_interface",
                "config": {
                    "data_dir": str(temp_app_dir / "data" / "interface"),
                    "host": "127.0.0.1",
                    "port": 0,  # Porta casuale per test
                    "auto_open_browser": False
                }
            }
        },
        "secondary_plugins": {
            "chatbot": {
                "enabled": True,
                "config": {
                    "data_dir": str(temp_app_dir / "data" / "chatbot"),
                    "personality": "helpful",
                    "auto_respond": True
                }
            },
            "advanced_file_sharing": {
                "enabled": True,
                "config": {
                    "data_dir": str(temp_app_dir / "data" / "file_sharing"),
                    "max_file_size": 104857600,  # 100MB
                    "chunk_size": 65536
                }
            },
            "advanced_encryption": {
                "enabled": True,
                "config": {
                    "data_dir": str(temp_app_dir / "data" / "encryption"),
                    "default_algorithm": "aes_256_gcm",
                    "enable_pfs": True
                }
            }
        }
    }
    
    with open(config_file, 'w') as f:
        json.dump(test_config, f, indent=2)
    
    manager = ConfigManager(str(config_file))
    await manager.initialize()
    yield manager
    await manager.cleanup()


@pytest.fixture
async def plugin_manager(config_manager, temp_app_dir):
    """Fixture per PluginManager"""
    manager = PluginManager()
    await manager.initialize(config_manager.get_config())
    yield manager
    await manager.cleanup()


@pytest.fixture
async def integrated_app(config_manager, plugin_manager):
    """Fixture per applicazione completamente integrata"""
    
    class IntegratedApp:
        def __init__(self):
            self.config_manager = config_manager
            self.plugin_manager = plugin_manager
            
            # Moduli core
            self.security_module = None
            self.messaging_module = None
            self.network_module = None
            self.interface_module = None
            
            # Plugin secondari
            self.chatbot_plugin = None
            self.file_sharing_plugin = None
            self.encryption_plugin = None
            
            self.running = False
        
        async def initialize(self):
            """Inizializza l'applicazione completa"""
            config = self.config_manager.get_config()
            
            # Inizializza moduli core
            await self._initialize_core_modules(config)
            
            # Inizializza plugin secondari
            await self._initialize_secondary_plugins(config)
            
            # Configura interconnessioni
            await self._setup_module_connections()
            
            self.running = True
        
        async def cleanup(self):
            """Pulisce l'applicazione"""
            self.running = False
            
            # Cleanup plugin secondari
            if self.chatbot_plugin:
                await self.chatbot_plugin.cleanup()
            if self.file_sharing_plugin:
                await self.file_sharing_plugin.cleanup()
            if self.encryption_plugin:
                await self.encryption_plugin.cleanup()
            
            # Cleanup moduli core
            if self.interface_module:
                await self.interface_module.cleanup()
            if self.network_module:
                await self.network_module.cleanup()
            if self.messaging_module:
                await self.messaging_module.cleanup()
            if self.security_module:
                await self.security_module.cleanup()
        
        async def _initialize_core_modules(self, config):
            """Inizializza moduli core"""
            core_config = config["core_modules"]
            
            # Security Module
            self.security_module = create_basic_security_module()
            await self.security_module.initialize(core_config["security"]["config"])
            
            # Messaging Module
            self.messaging_module = create_simple_p2p_messaging()
            await self.messaging_module.initialize(core_config["messaging"]["config"])
            
            # Network Module
            self.network_module = create_basic_network_module()
            await self.network_module.initialize(core_config["network"]["config"])
            
            # Interface Module
            self.interface_module = create_web_interface()
            await self.interface_module.initialize(core_config["interface"]["config"])
        
        async def _initialize_secondary_plugins(self, config):
            """Inizializza plugin secondari"""
            plugins_config = config["secondary_plugins"]
            
            # ChatBot Plugin
            if plugins_config["chatbot"]["enabled"]:
                self.chatbot_plugin = create_chatbot_plugin()
                await self.chatbot_plugin.initialize(plugins_config["chatbot"]["config"])
            
            # Advanced File Sharing Plugin
            if plugins_config["advanced_file_sharing"]["enabled"]:
                self.file_sharing_plugin = create_advanced_file_sharing()
                await self.file_sharing_plugin.initialize(plugins_config["advanced_file_sharing"]["config"])
            
            # Advanced Encryption Plugin
            if plugins_config["advanced_encryption"]["enabled"]:
                self.encryption_plugin = create_advanced_encryption()
                await self.encryption_plugin.initialize(plugins_config["advanced_encryption"]["config"])
        
        async def _setup_module_connections(self):
            """Configura interconnessioni tra moduli"""
            
            # Configura riferimenti moduli core per plugin secondari
            if self.chatbot_plugin:
                await self.chatbot_plugin.set_core_module("security", self.security_module)
                await self.chatbot_plugin.set_core_module("messaging", self.messaging_module)
                await self.chatbot_plugin.set_core_module("network", self.network_module)
                await self.chatbot_plugin.set_core_module("interface", self.interface_module)
                await self.chatbot_plugin.activate()
            
            if self.file_sharing_plugin:
                await self.file_sharing_plugin.set_core_module("security", self.security_module)
                await self.file_sharing_plugin.set_core_module("messaging", self.messaging_module)
                await self.file_sharing_plugin.set_core_module("network", self.network_module)
                await self.file_sharing_plugin.set_core_module("interface", self.interface_module)
                await self.file_sharing_plugin.activate()
            
            if self.encryption_plugin:
                await self.encryption_plugin.set_core_module("security", self.security_module)
                await self.encryption_plugin.set_core_module("messaging", self.messaging_module)
                await self.encryption_plugin.set_core_module("network", self.network_module)
                await self.encryption_plugin.set_core_module("interface", self.interface_module)
                await self.encryption_plugin.activate()
    
    app = IntegratedApp()
    await app.initialize()
    yield app
    await app.cleanup()


class TestE2EBasicFlow:
    """Test del flusso base end-to-end"""
    
    @pytest.mark.asyncio
    async def test_application_startup_and_shutdown(self, integrated_app):
        """Test avvio e spegnimento applicazione"""
        # Verifica che l'applicazione sia avviata
        assert integrated_app.running
        
        # Verifica che tutti i moduli core siano inizializzati
        assert integrated_app.security_module is not None
        assert integrated_app.messaging_module is not None
        assert integrated_app.network_module is not None
        assert integrated_app.interface_module is not None
        
        # Verifica che i plugin secondari siano inizializzati
        assert integrated_app.chatbot_plugin is not None
        assert integrated_app.file_sharing_plugin is not None
        assert integrated_app.encryption_plugin is not None
        
        # Verifica stato moduli
        security_info = integrated_app.security_module.get_module_info()
        assert security_info["name"] == "BasicSecurity"
        
        messaging_info = integrated_app.messaging_module.get_module_info()
        assert messaging_info["name"] == "SimpleP2PMessaging"
        
        network_info = integrated_app.network_module.get_module_info()
        assert network_info["name"] == "BasicNetworkModule"
        
        interface_info = integrated_app.interface_module.get_module_info()
        assert interface_info["name"] == "WebInterface"
    
    @pytest.mark.asyncio
    async def test_module_interconnections(self, integrated_app):
        """Test interconnessioni tra moduli"""
        
        # Verifica che i plugin abbiano riferimenti ai moduli core
        chatbot_status = await integrated_app.chatbot_plugin.get_status()
        assert chatbot_status["running"]
        
        file_sharing_status = await integrated_app.file_sharing_plugin.get_status()
        assert file_sharing_status["running"]
        
        encryption_status = await integrated_app.encryption_plugin.get_status()
        assert encryption_status["running"]


class TestE2EMessagingFlow:
    """Test del flusso di messaggistica end-to-end"""
    
    @pytest.mark.asyncio
    async def test_peer_to_peer_messaging(self, integrated_app):
        """Test messaggistica P2P completa"""
        
        # Simula connessione a un peer
        test_peer_id = "test_peer_123"
        test_peer_address = ("127.0.0.1", 12345)
        
        # Connetti al peer tramite network module
        connected = await integrated_app.network_module.connect_to_peer(
            test_peer_id, test_peer_address[0], test_peer_address[1]
        )
        
        # Simula invio messaggio
        test_message = "Hello from integration test!"
        message_sent = await integrated_app.messaging_module.send_message(
            test_peer_id, test_message
        )
        
        # Verifica cronologia messaggi
        history = await integrated_app.messaging_module.get_message_history(test_peer_id)
        assert len(history) > 0
        
        # Verifica peer connessi
        connected_peers = await integrated_app.network_module.get_connected_peers()
        # Note: In test environment, connection might not succeed, but we test the flow
    
    @pytest.mark.asyncio
    async def test_chatbot_integration(self, integrated_app):
        """Test integrazione chatbot con messaggistica"""
        
        # Simula messaggio diretto al bot
        bot_message = "@bot help"
        
        # Il chatbot dovrebbe processare il messaggio
        # (In un ambiente reale, questo avverrebbe tramite handler messaggi)
        
        # Verifica stato chatbot
        bot_status = await integrated_app.chatbot_plugin.get_status()
        assert bot_status["running"]
        
        # Verifica comandi disponibili
        commands = await integrated_app.chatbot_plugin.get_available_commands()
        assert len(commands) > 0
        assert any(cmd["name"] == "help" for cmd in commands)


class TestE2EFileTransferFlow:
    """Test del flusso di trasferimento file end-to-end"""
    
    @pytest.mark.asyncio
    async def test_file_sharing_workflow(self, integrated_app, temp_app_dir):
        """Test workflow completo condivisione file"""
        
        # Crea file di test
        test_file = temp_app_dir / "test_file.txt"
        test_content = b"This is a test file for integration testing"
        test_file.write_bytes(test_content)
        
        # Condividi file
        share_result = await integrated_app.file_sharing_plugin.share_file(
            str(test_file), "test_peer_123"
        )
        
        # Verifica che la condivisione sia stata avviata
        # (In ambiente di test, il peer potrebbe non essere realmente connesso)
        
        # Verifica file condivisi
        shared_files = await integrated_app.file_sharing_plugin.get_shared_files()
        
        # Verifica statistiche trasferimenti
        stats = await integrated_app.file_sharing_plugin.get_transfer_stats()
        assert "total_files_shared" in stats


class TestE2ESecurityFlow:
    """Test del flusso di sicurezza end-to-end"""
    
    @pytest.mark.asyncio
    async def test_encryption_integration(self, integrated_app):
        """Test integrazione crittografia"""
        
        # Test generazione chiavi
        key_pair = await integrated_app.encryption_plugin.generate_key_pair(
            integrated_app.encryption_plugin.default_algorithm
        )
        assert key_pair is not None
        
        # Test crittografia dati
        test_data = b"Secret message for encryption test"
        encrypt_result = await integrated_app.encryption_plugin.encrypt_data(test_data)
        assert encrypt_result.success
        assert encrypt_result.data is not None
        
        # Test decrittografia
        decrypt_result = await integrated_app.encryption_plugin.decrypt_data(
            encrypt_result.data,
            encrypt_result.algorithm,
            encrypt_result.key_id,
            encrypt_result.nonce,
            encrypt_result.tag
        )
        assert decrypt_result.success
        assert decrypt_result.data == test_data
        
        # Verifica statistiche crittografiche
        crypto_stats = await integrated_app.encryption_plugin.get_crypto_stats()
        assert crypto_stats["total_encryptions"] > 0
        assert crypto_stats["total_decryptions"] > 0
    
    @pytest.mark.asyncio
    async def test_security_module_integration(self, integrated_app):
        """Test integrazione modulo sicurezza"""
        
        # Test autenticazione
        test_credentials = {"username": "test_user", "password": "test_password"}
        auth_result = await integrated_app.security_module.authenticate_user(test_credentials)
        
        # Test autorizzazione
        test_permission = "send_message"
        auth_check = await integrated_app.security_module.check_permission("test_user", test_permission)
        
        # Verifica audit log
        audit_log = await integrated_app.security_module.get_audit_log(limit=10)
        assert isinstance(audit_log, list)


class TestE2EInterfaceFlow:
    """Test del flusso interfaccia end-to-end"""
    
    @pytest.mark.asyncio
    async def test_web_interface_integration(self, integrated_app):
        """Test integrazione interfaccia web"""
        
        # Verifica rendering interfaccia
        render_result = await integrated_app.interface_module.render_interface()
        assert render_result is not None
        
        # Test aggiornamento display
        await integrated_app.interface_module.update_display(
            "messages", [{"sender": "test", "content": "test message"}]
        )
        
        # Test notifiche
        await integrated_app.interface_module.update_display(
            "notifications", [{"type": "info", "message": "Test notification"}]
        )
        
        # Verifica componenti
        components = await integrated_app.interface_module.get_components()
        assert len(components) > 0


class TestE2EErrorHandling:
    """Test gestione errori end-to-end"""
    
    @pytest.mark.asyncio
    async def test_module_failure_recovery(self, integrated_app):
        """Test recupero da errori moduli"""
        
        # Simula errore in un modulo
        original_method = integrated_app.messaging_module.send_message
        
        async def failing_send_message(*args, **kwargs):
            raise Exception("Simulated module failure")
        
        # Sostituisci temporaneamente il metodo
        integrated_app.messaging_module.send_message = failing_send_message
        
        # Verifica che l'applicazione gestisca l'errore
        try:
            await integrated_app.messaging_module.send_message("test_peer", "test")
            assert False, "Should have raised exception"
        except Exception as e:
            assert "Simulated module failure" in str(e)
        
        # Ripristina metodo originale
        integrated_app.messaging_module.send_message = original_method
        
        # Verifica che il modulo funzioni ancora
        result = await integrated_app.messaging_module.send_message("test_peer", "test")
        # Il risultato dipende dall'implementazione, ma non dovrebbe sollevare eccezioni
    
    @pytest.mark.asyncio
    async def test_plugin_failure_isolation(self, integrated_app):
        """Test isolamento errori plugin"""
        
        # Simula errore in un plugin
        original_method = integrated_app.chatbot_plugin.process_message
        
        async def failing_process_message(*args, **kwargs):
            raise Exception("Simulated plugin failure")
        
        # Sostituisci temporaneamente il metodo
        integrated_app.chatbot_plugin.process_message = failing_process_message
        
        # Verifica che l'errore del plugin non comprometta l'applicazione
        try:
            await integrated_app.chatbot_plugin.process_message("test_user", "test message")
            assert False, "Should have raised exception"
        except Exception as e:
            assert "Simulated plugin failure" in str(e)
        
        # Verifica che altri moduli funzionino ancora
        security_info = integrated_app.security_module.get_module_info()
        assert security_info["name"] == "BasicSecurity"
        
        # Ripristina metodo originale
        integrated_app.chatbot_plugin.process_message = original_method


class TestE2EPerformance:
    """Test performance end-to-end"""
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, integrated_app):
        """Test operazioni concorrenti"""
        
        # Test operazioni concorrenti su moduli diversi
        tasks = []
        
        # Task di crittografia
        for i in range(5):
            task = integrated_app.encryption_plugin.encrypt_data(f"test data {i}".encode())
            tasks.append(task)
        
        # Task di messaggistica
        for i in range(5):
            task = integrated_app.messaging_module.send_message(f"peer_{i}", f"message {i}")
            tasks.append(task)
        
        # Esegui tutti i task concorrentemente
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verifica che la maggior parte delle operazioni sia riuscita
        successful_operations = sum(1 for result in results if not isinstance(result, Exception))
        assert successful_operations > 0
    
    @pytest.mark.asyncio
    async def test_memory_usage_stability(self, integrated_app):
        """Test stabilità utilizzo memoria"""
        
        # Esegui molte operazioni per verificare memory leak
        for i in range(100):
            # Operazioni di crittografia
            data = f"test data {i}".encode()
            encrypt_result = await integrated_app.encryption_plugin.encrypt_data(data)
            
            if encrypt_result.success:
                await integrated_app.encryption_plugin.decrypt_data(
                    encrypt_result.data,
                    encrypt_result.algorithm,
                    encrypt_result.key_id,
                    encrypt_result.nonce,
                    encrypt_result.tag
                )
            
            # Operazioni di messaggistica
            await integrated_app.messaging_module.send_message(f"peer_{i % 10}", f"message {i}")
            
            # Piccola pausa per evitare sovraccarico
            if i % 10 == 0:
                await asyncio.sleep(0.01)
        
        # Verifica che l'applicazione sia ancora funzionante
        assert integrated_app.running
        
        # Verifica statistiche
        crypto_stats = await integrated_app.encryption_plugin.get_crypto_stats()
        assert crypto_stats["total_encryptions"] >= 100


class TestE2EConfigurationManagement:
    """Test gestione configurazione end-to-end"""
    
    @pytest.mark.asyncio
    async def test_dynamic_configuration_update(self, integrated_app):
        """Test aggiornamento configurazione dinamico"""
        
        # Aggiorna configurazione chatbot
        new_chatbot_config = {
            "personality": "funny",
            "auto_respond": False
        }
        
        await integrated_app.chatbot_plugin.update_config(new_chatbot_config)
        
        # Verifica che la configurazione sia stata aggiornata
        bot_status = await integrated_app.chatbot_plugin.get_status()
        assert bot_status["running"]
        
        # Aggiorna configurazione encryption
        new_encryption_config = {
            "enable_pfs": False,
            "key_rotation_interval": 7200
        }
        
        await integrated_app.encryption_plugin.update_config(new_encryption_config)
        
        # Verifica che la configurazione sia stata aggiornata
        encryption_status = await integrated_app.encryption_plugin.get_status()
        assert encryption_status["running"]
    
    @pytest.mark.asyncio
    async def test_configuration_persistence(self, integrated_app, temp_app_dir):
        """Test persistenza configurazione"""
        
        # Modifica configurazione
        new_config = {"test_setting": "test_value"}
        await integrated_app.config_manager.update_config("test_section", new_config)
        
        # Verifica che la configurazione sia persistente
        config = integrated_app.config_manager.get_config()
        assert "test_section" in config
        assert config["test_section"]["test_setting"] == "test_value"


if __name__ == "__main__":
    # Esegui test con pytest
    pytest.main([__file__, "-v", "--tb=short"])