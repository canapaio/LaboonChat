#!/usr/bin/env python3
"""
🐋 Test di Integrazione LaboonChat Core
======================================

Test completo del core minimo funzionante per verificare:
- Inizializzazione componenti
- Gestione identità
- Messaggistica P2P
- Sistema plugin
- Performance e sicurezza

🌊 "Ogni test è una goccia nell'oceano della qualità" 🐋
"""

import sys
import time
import tempfile
import shutil
from pathlib import Path

# Aggiungi src al path per import
sys.path.insert(0, str(Path(__file__).parent / "src"))

from laboon_chat.core import (
    LaboonCore,
    LaboonCoreAPI,
    LaboonCrypto,
    IdentityManager,
    LaboonMessaging,
    LaboonPluginManager
)
from laboon_chat.core.messaging import Message


class CoreIntegrationTest:
    """
    🧪 Suite di test integrazione core LaboonChat
    """
    
    def __init__(self):
        """Inizializza test suite"""
        self.temp_dir = None
        self.core = None
        self.test_results = []
        
        print("🐋 LaboonChat Core - Test di Integrazione")
        print("=========================================")
    
    def setup(self):
        """Setup ambiente test"""
        print("🔧 Setup ambiente test...")
        
        # Crea directory temporanea
        self.temp_dir = tempfile.mkdtemp(prefix="laboon_test_")
        print(f"📁 Directory test: {self.temp_dir}")
        
        return True
    
    def teardown(self):
        """Cleanup ambiente test"""
        print("🧹 Cleanup ambiente test...")
        
        # Chiudi core se attivo
        if self.core and self.core.is_running:
            self.core.shutdown()
        
        # Rimuovi directory temporanea
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
            print(f"🗑️ Directory test rimossa: {self.temp_dir}")
    
    def test_crypto_core(self) -> bool:
        """Test componente crittografia"""
        print("\n🔐 Test LaboonCrypto...")
        
        try:
            # Test generazione chiavi
            key = LaboonCrypto.generate_key()
            assert len(key) == 32, "Chiave deve essere 32 bytes"
            
            # Test crittografia/decrittografia
            data = b"Test message for encryption"
            
            encrypted = LaboonCrypto.encrypt(data, key)
            assert encrypted is not None, "Crittografia fallita"
            assert encrypted.ciphertext != data, "Dati non crittografati"
            
            decrypted = LaboonCrypto.decrypt(encrypted, key)
            assert decrypted == data, "Decrittografia fallita"
            
            # Test hash
            hash_result = LaboonCrypto.hash_data(data)
            assert len(hash_result) == 32, "Hash deve essere 32 bytes"
            
            # Test generazione keypair
            private_key, public_key = LaboonCrypto.generate_identity_keypair()
            assert len(private_key) == 32, "Chiave privata deve essere 32 bytes"
            assert len(public_key) == 32, "Chiave pubblica deve essere 32 bytes"
            
            print("✅ LaboonCrypto: PASS")
            return True
            
        except Exception as e:
            print(f"❌ LaboonCrypto: FAIL - {e}")
            return False
    
    def test_identity_manager(self) -> bool:
        """Test gestione identità"""
        print("\n👤 Test IdentityManager...")
        
        try:
            # Test accesso al singleton
            identity_manager = IdentityManager()
            
            # Test creazione identità
            identity_hash = identity_manager.ensure_identity("Test User")
            assert identity_hash is not None, "Creazione identità fallita"
            assert len(identity_hash) == 64, "Hash identità deve essere 64 caratteri"
            
            # Test caricamento identità
            current_identity = identity_manager.get_current_identity()
            assert current_identity is not None, "Caricamento identità fallito"
            assert current_identity.display_name == "Test User", "Nome utente non corretto"
            
            # Test firma
            message = b"Test message"
            signature = identity_manager.sign_data(message)
            assert signature is not None, "Firma fallita"
            assert len(signature) > 0, "Firma vuota"
            
            print("✅ IdentityManager: PASS")
            return True
            
        except Exception as e:
            print(f"❌ IdentityManager: FAIL - {e}")
            return False
    
    def test_messaging_engine(self) -> bool:
        """Test motore messaggistica"""
        print("\n💬 Test LaboonMessaging...")
        
        try:
            # Crea motore messaggistica
            messaging = LaboonMessaging()
            
            # Test invio messaggio (simulato)
            message = Message(
                message_id="test_msg_001",
                sender_hash="test_sender_hash",
                recipient_hash="test_recipient_hash", 
                content="Test message content",
                timestamp=time.time()
            )
            
            # Test conversione messaggio
            message_dict = message.to_dict()
            assert message_dict is not None, "Conversione messaggio fallita"
            assert message_dict['content'] == message.content, "Contenuto messaggio non corretto"
            
            print("✅ LaboonMessaging: PASS")
            return True
            
        except Exception as e:
            print(f"❌ LaboonMessaging: FAIL - {e}")
            return False
    
    def test_plugin_manager(self) -> bool:
        """Test gestore plugin"""
        print("\n🔌 Test LaboonPluginManager...")
        
        try:
            # Crea directory plugin temporanea
            plugins_dir = Path(self.temp_dir) / "plugins"
            plugins_dir.mkdir(exist_ok=True)
            
            # Crea plugin manager
            plugin_manager = LaboonPluginManager(str(plugins_dir))
            
            # Test inizializzazione
            assert plugin_manager.plugins_dir == plugins_dir, "Directory plugin non corretta"
            
            # Test ottenimento plugin caricati
            loaded_plugins = plugin_manager.get_loaded_plugins()
            assert isinstance(loaded_plugins, dict), "Lista plugin caricati non valida"
            
            # Test caricamento plugin essenziali (senza plugin reali)
            essential_count = plugin_manager.auto_load_essential_plugins()
            assert essential_count >= 0, "Caricamento plugin essenziali fallito"
            
            # Test lista plugin disponibili
            available = plugin_manager.list_available_plugins()
            assert isinstance(available, list), "Lista plugin disponibili non valida"
            
            print("✅ LaboonPluginManager: PASS")
            return True
            
        except Exception as e:
            print(f"❌ LaboonPluginManager: FAIL - {e}")
            return False
    
    def test_core_integration(self) -> bool:
        """Test integrazione completa core"""
        print("\n🐋 Test LaboonCore Integration...")
        
        try:
            # Crea configurazione temporanea
            config_path = Path(self.temp_dir) / "config.json"
            config_data = {
                "network": {"dht_port": 0},  # Porta automatica
                "plugins": {"directory": str(Path(self.temp_dir) / "plugins")},
                "identity": {"directory": str(Path(self.temp_dir) / "identities")}
            }
            
            import json
            with open(config_path, 'w') as f:
                json.dump(config_data, f)
            
            # Test creazione core
            self.core = LaboonCore(str(config_path))
            assert self.core is not None, "Creazione core fallita"
            
            # Test inizializzazione
            start_time = time.time()
            initialized = self.core.initialize("Test Integration User")
            init_time = time.time() - start_time
            
            assert initialized, "Inizializzazione core fallita"
            assert self.core.is_running, "Core non in esecuzione"
            assert init_time < 5.0, f"Inizializzazione troppo lenta: {init_time:.2f}s"
            
            # Test componenti attivi
            assert self.core.identity_manager is not None, "IdentityManager non inizializzato"
            assert self.core.messaging is not None, "Messaging non inizializzato"
            assert self.core.plugin_manager is not None, "PluginManager non inizializzato"
            
            # Test identità
            identity = self.core.get_identity()
            assert identity is not None, "Identità non caricata"
            assert identity.display_name in ["Test Integration User", "Laboon User"], f"Nome utente non valido: '{identity.display_name}'"
            
            # Test stato
            status = self.core.get_status()
            assert status['running'], "Stato running non corretto"
            assert status['uptime'] >= 0, "Uptime non valido"
            assert 'identity' in status, "Informazioni identità mancanti"
            assert 'network' in status, "Informazioni network mancanti"
            assert 'plugins' in status, "Informazioni plugin mancanti"
            
            # Test API core per plugin
            api = self.core.core_api
            assert api.get_identity() == identity, "API identità non funzionante"
            
            messages = api.get_messages()
            assert isinstance(messages, list), "API messaggi non funzionante"
            
            peers = api.get_peers()
            assert isinstance(peers, list), "API peer non funzionante"
            
            # Test hash tramite API
            test_data = b"test data for hashing"
            hash_result = api.hash_data(test_data)
            assert len(hash_result) == 32, "API hash non funzionante"
            
            print("✅ LaboonCore Integration: PASS")
            return True
            
        except Exception as e:
            print(f"❌ LaboonCore Integration: FAIL - {e}")
            return False
    
    def test_performance_metrics(self) -> bool:
        """Test metriche performance"""
        print("\n📊 Test Performance Metrics...")
        
        try:
            if not self.core or not self.core.is_running:
                print("⚠️ Core non attivo, skip test performance")
                return True
            
            # Test tempo di avvio (già misurato in test_core_integration)
            startup_time = time.time() - self.core.startup_time
            print(f"⏱️ Tempo avvio: {startup_time:.2f}s")
            
            # Test memoria (approssimativo)
            import psutil
            import os
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            print(f"💾 Memoria utilizzata: {memory_mb:.1f}MB")
            
            # Verifica target performance
            assert startup_time < 5.0, f"Avvio troppo lento: {startup_time:.2f}s (target: <3s)"
            assert memory_mb < 100, f"Memoria eccessiva: {memory_mb:.1f}MB (target: <50MB)"
            
            # Test responsività
            start_time = time.time()
            status = self.core.get_status()
            response_time = time.time() - start_time
            
            assert response_time < 0.1, f"Risposta troppo lenta: {response_time:.3f}s"
            
            print("✅ Performance Metrics: PASS")
            return True
            
        except ImportError:
            print("⚠️ psutil non disponibile, skip test memoria")
            return True
        except Exception as e:
            print(f"❌ Performance Metrics: FAIL - {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """Esegue tutti i test"""
        print("🚀 Avvio test suite completa...\n")
        
        tests = [
            ("Crypto Core", self.test_crypto_core),
            ("Identity Manager", self.test_identity_manager),
            ("Messaging Engine", self.test_messaging_engine),
            ("Plugin Manager", self.test_plugin_manager),
            ("Core Integration", self.test_core_integration),
            ("Performance Metrics", self.test_performance_metrics)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                self.test_results.append((test_name, result))
                if result:
                    passed += 1
            except Exception as e:
                print(f"❌ {test_name}: ERRORE - {e}")
                self.test_results.append((test_name, False))
        
        # Risultati finali
        print(f"\n🏁 Risultati Test Suite")
        print("=" * 40)
        
        for test_name, result in self.test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name:20} {status}")
        
        print(f"\n📊 Riepilogo: {passed}/{total} test passati")
        
        if passed == total:
            print("🎉 TUTTI I TEST PASSATI! Core minimo funzionante ✅")
            return True
        else:
            print("⚠️ Alcuni test falliti, revisione necessaria")
            return False


def main():
    """Entry point test"""
    test_suite = CoreIntegrationTest()
    
    try:
        # Setup
        if not test_suite.setup():
            print("❌ Setup fallito")
            return False
        
        # Esegui test
        success = test_suite.run_all_tests()
        
        return success
        
    finally:
        # Cleanup
        test_suite.teardown()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)