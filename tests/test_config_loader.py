"""
Test suite per ConfigLoader

Testa il caricamento, validazione, salvataggio e gestione
delle configurazioni dell'applicazione.
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, mock_open
from typing import Dict, Any

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from laboon_chat2.utils.config_loader import (
    ConfigLoader, LoggingConfig, PluginConfig, SecurityConfig,
    NetworkConfig, InterfaceConfig, ApplicationConfig,
    ConfigValidationError, ConfigLoadError, ConfigSaveError
)


@pytest.fixture
def temp_config_dir():
    """Crea una directory temporanea per i test"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def valid_config():
    """Configurazione valida per i test"""
    return {
        "application": {
            "name": "LaboonChat2",
            "version": "2.0.0",
            "debug": False,
            "data_dir": "./data",
            "max_connections": 100,
            "timeout": 30.0
        },
        "logging": {
            "level": "INFO",
            "file_rotation": True,
            "max_file_size": "10MB",
            "backup_count": 5,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "console_output": True,
            "json_format": False
        },
        "security": {
            "encryption_algorithm": "AES-256-GCM",
            "key_size": 256,
            "enable_signatures": True,
            "signature_algorithm": "Ed25519",
            "key_rotation_interval": 86400,
            "max_key_age": 604800,
            "trusted_peers_file": "trusted_peers.json",
            "blacklist_file": "blacklist.json"
        },
        "network": {
            "listen_port": 8888,
            "max_peers": 50,
            "connection_timeout": 10.0,
            "heartbeat_interval": 30.0,
            "discovery_enabled": True,
            "discovery_port": 8889,
            "bind_address": "0.0.0.0"
        },
        "interface": {
            "type": "web",
            "host": "localhost",
            "port": 8080,
            "auto_open_browser": True,
            "theme": "dark",
            "language": "en",
            "enable_notifications": True,
            "max_message_history": 1000
        },
        "plugins": {
            "core": {
                "security": {
                    "module": "basic_security",
                    "enabled": True,
                    "config": {
                        "encryption": "AES-256",
                        "key_rotation": True
                    }
                },
                "messaging": {
                    "module": "simple_p2p_messaging",
                    "enabled": True,
                    "config": {
                        "port": 8888,
                        "max_message_size": 1048576
                    }
                },
                "interface": {
                    "module": "web_interface",
                    "enabled": True,
                    "config": {
                        "theme": "modern",
                        "auto_refresh": True
                    }
                }
            },
            "secondary": {
                "logger": {
                    "module": "advanced_logger",
                    "enabled": True,
                    "config": {
                        "level": "DEBUG",
                        "file_output": True
                    }
                },
                "metrics": {
                    "module": "system_metrics",
                    "enabled": False,
                    "config": {
                        "interval": 60,
                        "export_format": "json"
                    }
                }
            }
        }
    }


@pytest.fixture
def config_loader():
    """Crea un'istanza di ConfigLoader"""
    return ConfigLoader()


class TestConfigDataClasses:
    """Test per le dataclass di configurazione"""
    
    def test_logging_config_creation(self):
        """Testa creazione LoggingConfig"""
        config = LoggingConfig(
            level="DEBUG",
            file_rotation=True,
            max_file_size="5MB",
            backup_count=3
        )
        
        assert config.level == "DEBUG"
        assert config.file_rotation is True
        assert config.max_file_size == "5MB"
        assert config.backup_count == 3
    
    def test_plugin_config_creation(self):
        """Testa creazione PluginConfig"""
        config = PluginConfig(
            module="test_module",
            enabled=True,
            config={"setting": "value"}
        )
        
        assert config.module == "test_module"
        assert config.enabled is True
        assert config.config == {"setting": "value"}
    
    def test_security_config_creation(self):
        """Testa creazione SecurityConfig"""
        config = SecurityConfig(
            encryption_algorithm="AES-256-GCM",
            key_size=256,
            enable_signatures=True
        )
        
        assert config.encryption_algorithm == "AES-256-GCM"
        assert config.key_size == 256
        assert config.enable_signatures is True
    
    def test_network_config_creation(self):
        """Testa creazione NetworkConfig"""
        config = NetworkConfig(
            listen_port=8888,
            max_peers=50,
            connection_timeout=10.0
        )
        
        assert config.listen_port == 8888
        assert config.max_peers == 50
        assert config.connection_timeout == 10.0
    
    def test_interface_config_creation(self):
        """Testa creazione InterfaceConfig"""
        config = InterfaceConfig(
            type="web",
            host="localhost",
            port=8080
        )
        
        assert config.type == "web"
        assert config.host == "localhost"
        assert config.port == 8080
    
    def test_application_config_creation(self):
        """Testa creazione ApplicationConfig completa"""
        logging_config = LoggingConfig(level="INFO")
        security_config = SecurityConfig(encryption_algorithm="AES-256-GCM")
        network_config = NetworkConfig(listen_port=8888)
        interface_config = InterfaceConfig(type="web", host="localhost", port=8080)
        
        app_config = ApplicationConfig(
            name="TestApp",
            version="1.0.0",
            logging=logging_config,
            security=security_config,
            network=network_config,
            interface=interface_config,
            plugins={}
        )
        
        assert app_config.name == "TestApp"
        assert app_config.version == "1.0.0"
        assert app_config.logging.level == "INFO"
        assert app_config.security.encryption_algorithm == "AES-256-GCM"


class TestConfigLoader:
    """Test per ConfigLoader"""
    
    def test_initialization(self, config_loader):
        """Testa inizializzazione ConfigLoader"""
        assert config_loader is not None
        assert hasattr(config_loader, 'load_config')
        assert hasattr(config_loader, 'save_config')
        assert hasattr(config_loader, 'validate_config')
    
    def test_load_config_from_file(self, config_loader, temp_config_dir, valid_config):
        """Testa caricamento configurazione da file"""
        config_file = temp_config_dir / "config.json"
        
        # Salva configurazione valida
        with open(config_file, 'w') as f:
            json.dump(valid_config, f, indent=2)
        
        # Carica configurazione
        loaded_config = config_loader.load_config(str(config_file))
        
        assert loaded_config == valid_config
        assert loaded_config["application"]["name"] == "LaboonChat2"
        assert loaded_config["logging"]["level"] == "INFO"
    
    def test_load_config_file_not_found(self, config_loader):
        """Testa caricamento con file non esistente"""
        with pytest.raises(ConfigLoadError, match="File di configurazione non trovato"):
            config_loader.load_config("nonexistent.json")
    
    def test_load_config_invalid_json(self, config_loader, temp_config_dir):
        """Testa caricamento con JSON invalido"""
        config_file = temp_config_dir / "invalid.json"
        
        # Crea file JSON invalido
        with open(config_file, 'w') as f:
            f.write("{ invalid json }")
        
        with pytest.raises(ConfigLoadError, match="Errore nel parsing del JSON"):
            config_loader.load_config(str(config_file))
    
    def test_load_config_default(self, config_loader):
        """Testa caricamento configurazione di default"""
        with patch('os.path.exists', return_value=False):
            config = config_loader.load_config()
            
            # Verifica che sia stata caricata configurazione di default
            assert "application" in config
            assert "logging" in config
            assert "plugins" in config
    
    def test_save_config(self, config_loader, temp_config_dir, valid_config):
        """Testa salvataggio configurazione"""
        config_file = temp_config_dir / "save_test.json"
        
        config_loader.save_config(valid_config, str(config_file))
        
        # Verifica che il file sia stato creato
        assert config_file.exists()
        
        # Verifica contenuto
        with open(config_file, 'r') as f:
            saved_config = json.load(f)
        
        assert saved_config == valid_config
    
    def test_save_config_permission_error(self, config_loader, valid_config):
        """Testa salvataggio con errore di permessi"""
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            with pytest.raises(ConfigSaveError, match="Errore di permessi"):
                config_loader.save_config(valid_config, "/invalid/path/config.json")
    
    def test_validate_config_valid(self, config_loader, valid_config):
        """Testa validazione configurazione valida"""
        result = config_loader.validate_config(valid_config)
        assert result is True
    
    def test_validate_config_missing_required(self, config_loader):
        """Testa validazione con campi obbligatori mancanti"""
        invalid_config = {
            "application": {
                # Manca "name"
                "version": "1.0.0"
            }
        }
        
        with pytest.raises(ConfigValidationError, match="Campo obbligatorio mancante"):
            config_loader.validate_config(invalid_config)
    
    def test_validate_config_invalid_type(self, config_loader):
        """Testa validazione con tipo invalido"""
        invalid_config = {
            "application": {
                "name": "TestApp",
                "version": "1.0.0",
                "debug": "not_a_boolean"  # Dovrebbe essere boolean
            },
            "logging": {
                "level": "INFO"
            },
            "plugins": {
                "core": {},
                "secondary": {}
            }
        }
        
        with pytest.raises(ConfigValidationError, match="Tipo di dato non valido"):
            config_loader.validate_config(invalid_config)
    
    def test_merge_configs(self, config_loader):
        """Testa merge di configurazioni"""
        base_config = {
            "application": {
                "name": "BaseApp",
                "version": "1.0.0",
                "debug": False
            },
            "logging": {
                "level": "INFO"
            }
        }
        
        override_config = {
            "application": {
                "debug": True,
                "new_setting": "value"
            },
            "new_section": {
                "setting": "value"
            }
        }
        
        merged = config_loader.merge_configs(base_config, override_config)
        
        # Verifica merge
        assert merged["application"]["name"] == "BaseApp"  # Mantenuto da base
        assert merged["application"]["debug"] is True  # Sovrascritto
        assert merged["application"]["new_setting"] == "value"  # Aggiunto
        assert merged["logging"]["level"] == "INFO"  # Mantenuto da base
        assert merged["new_section"]["setting"] == "value"  # Nuova sezione
    
    def test_get_plugin_config_core(self, config_loader, valid_config):
        """Testa recupero configurazione plugin core"""
        config_loader._config = valid_config
        
        plugin_config = config_loader.get_plugin_config("core", "security")
        
        assert plugin_config["module"] == "basic_security"
        assert plugin_config["enabled"] is True
        assert "config" in plugin_config
    
    def test_get_plugin_config_secondary(self, config_loader, valid_config):
        """Testa recupero configurazione plugin secondario"""
        config_loader._config = valid_config
        
        plugin_config = config_loader.get_plugin_config("secondary", "logger")
        
        assert plugin_config["module"] == "advanced_logger"
        assert plugin_config["enabled"] is True
    
    def test_get_plugin_config_not_found(self, config_loader, valid_config):
        """Testa recupero configurazione plugin non esistente"""
        config_loader._config = valid_config
        
        plugin_config = config_loader.get_plugin_config("core", "nonexistent")
        
        assert plugin_config == {}
    
    def test_update_plugin_config(self, config_loader, valid_config):
        """Testa aggiornamento configurazione plugin"""
        config_loader._config = valid_config
        
        new_config = {
            "module": "updated_security",
            "enabled": False,
            "config": {"new_setting": "value"}
        }
        
        config_loader.update_plugin_config("core", "security", new_config)
        
        updated = config_loader.get_plugin_config("core", "security")
        assert updated["module"] == "updated_security"
        assert updated["enabled"] is False
        assert updated["config"]["new_setting"] == "value"
    
    def test_get_default_config(self, config_loader):
        """Testa generazione configurazione di default"""
        default_config = config_loader.get_default_config()
        
        # Verifica struttura base
        assert "application" in default_config
        assert "logging" in default_config
        assert "security" in default_config
        assert "network" in default_config
        assert "interface" in default_config
        assert "plugins" in default_config
        
        # Verifica valori di default
        assert default_config["application"]["name"] == "LaboonChat2"
        assert default_config["logging"]["level"] == "INFO"
        assert default_config["network"]["listen_port"] == 8888
    
    def test_config_schema_validation(self, config_loader, valid_config):
        """Testa validazione schema JSON"""
        # Test con configurazione valida
        assert config_loader._validate_schema(valid_config) is True
        
        # Test con configurazione invalida
        invalid_config = {"invalid": "structure"}
        assert config_loader._validate_schema(invalid_config) is False
    
    def test_backup_and_restore_config(self, config_loader, temp_config_dir, valid_config):
        """Testa backup e ripristino configurazione"""
        config_file = temp_config_dir / "config.json"
        backup_file = temp_config_dir / "config.json.backup"
        
        # Salva configurazione originale
        config_loader.save_config(valid_config, str(config_file))
        
        # Crea backup
        config_loader.backup_config(str(config_file))
        
        assert backup_file.exists()
        
        # Modifica configurazione originale
        modified_config = valid_config.copy()
        modified_config["application"]["name"] = "Modified"
        config_loader.save_config(modified_config, str(config_file))
        
        # Ripristina da backup
        config_loader.restore_config(str(config_file))
        
        # Verifica ripristino
        restored_config = config_loader.load_config(str(config_file))
        assert restored_config["application"]["name"] == "LaboonChat2"
    
    def test_config_environment_variables(self, config_loader):
        """Testa sostituzione variabili d'ambiente"""
        config_with_env = {
            "application": {
                "name": "${APP_NAME}",
                "debug": "${DEBUG_MODE}"
            },
            "network": {
                "listen_port": "${LISTEN_PORT}"
            }
        }
        
        env_vars = {
            "APP_NAME": "TestApp",
            "DEBUG_MODE": "true",
            "LISTEN_PORT": "9999"
        }
        
        with patch.dict('os.environ', env_vars):
            resolved_config = config_loader.resolve_environment_variables(config_with_env)
            
            assert resolved_config["application"]["name"] == "TestApp"
            assert resolved_config["application"]["debug"] == "true"
            assert resolved_config["network"]["listen_port"] == "9999"
    
    def test_config_validation_edge_cases(self, config_loader):
        """Testa casi limite nella validazione"""
        # Configurazione vuota
        with pytest.raises(ConfigValidationError):
            config_loader.validate_config({})
        
        # Configurazione None
        with pytest.raises(ConfigValidationError):
            config_loader.validate_config(None)
        
        # Configurazione con valori None
        config_with_none = {
            "application": {
                "name": None,
                "version": "1.0.0"
            }
        }
        
        with pytest.raises(ConfigValidationError):
            config_loader.validate_config(config_with_none)


@pytest.mark.asyncio
async def test_config_loader_integration():
    """Test di integrazione completo per ConfigLoader"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = Path(temp_dir) / "integration_test.json"
        
        loader = ConfigLoader()
        
        # Test ciclo completo: default -> save -> load -> validate -> update
        
        # 1. Genera configurazione di default
        default_config = loader.get_default_config()
        assert loader.validate_config(default_config)
        
        # 2. Salva configurazione
        loader.save_config(default_config, str(config_path))
        assert config_path.exists()
        
        # 3. Carica configurazione
        loaded_config = loader.load_config(str(config_path))
        assert loaded_config == default_config
        
        # 4. Aggiorna configurazione plugin
        loader._config = loaded_config
        new_plugin_config = {
            "module": "new_module",
            "enabled": True,
            "config": {"test": "value"}
        }
        loader.update_plugin_config("core", "test_plugin", new_plugin_config)
        
        # 5. Verifica aggiornamento
        updated_plugin = loader.get_plugin_config("core", "test_plugin")
        assert updated_plugin["module"] == "new_module"
        
        # 6. Salva configurazione aggiornata
        loader.save_config(loader._config, str(config_path))
        
        # 7. Ricarica e verifica persistenza
        final_config = loader.load_config(str(config_path))
        final_plugin = ConfigLoader()
        final_plugin._config = final_config
        final_plugin_config = final_plugin.get_plugin_config("core", "test_plugin")
        assert final_plugin_config["module"] == "new_module"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])