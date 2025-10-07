"""
Test suite per LaboonChat2Application

Testa l'orchestrazione dell'applicazione, gestione del ciclo di vita,
caricamento configurazioni e coordinamento dei plugin.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, Optional

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from laboon_chat2.core.application import (
    LaboonChat2Application, ApplicationState, ApplicationError,
    create_application, run_application
)
from laboon_chat2.core.plugin_manager import ModularPluginManager, PluginStatus
from laboon_chat2.utils.config_loader import ConfigLoader
from laboon_chat2.utils.logger import LoggerManager


class MockPluginManager:
    """Mock del plugin manager per i test"""
    
    def __init__(self):
        self._initialized = False
        self._core_plugins = {}
        self._secondary_plugins = {}
    
    async def initialize(self):
        self._initialized = True
    
    async def cleanup(self):
        self._initialized = False
    
    async def load_core_plugin(self, plugin_type: str, module_name: str, config: Dict = None):
        self._core_plugins[plugin_type] = {
            "module_name": module_name,
            "config": config or {},
            "status": PluginStatus.LOADED
        }
        return True
    
    async def unload_core_plugin(self, plugin_type: str):
        if plugin_type in self._core_plugins:
            del self._core_plugins[plugin_type]
            return True
        return False
    
    async def load_secondary_plugin(self, plugin_id: str, module_name: str, config: Dict = None):
        self._secondary_plugins[plugin_id] = {
            "module_name": module_name,
            "config": config or {},
            "status": PluginStatus.LOADED
        }
        return True
    
    async def activate_secondary_plugin(self, plugin_id: str):
        if plugin_id in self._secondary_plugins:
            self._secondary_plugins[plugin_id]["status"] = PluginStatus.ACTIVE
            return True
        return False
    
    async def deactivate_secondary_plugin(self, plugin_id: str):
        if plugin_id in self._secondary_plugins:
            self._secondary_plugins[plugin_id]["status"] = PluginStatus.LOADED
            return True
        return False
    
    async def unload_secondary_plugin(self, plugin_id: str):
        if plugin_id in self._secondary_plugins:
            del self._secondary_plugins[plugin_id]
            return True
        return False
    
    def get_core_plugin_instance(self, plugin_type: str):
        if plugin_type in self._core_plugins:
            return Mock()
        return None
    
    def get_secondary_plugin_instance(self, plugin_id: str):
        if plugin_id in self._secondary_plugins:
            return Mock()
        return None
    
    def list_plugins(self):
        return {
            "core": list(self._core_plugins.keys()),
            "secondary": list(self._secondary_plugins.keys())
        }
    
    def get_plugin_status(self, plugin_id: str):
        if plugin_id in self._core_plugins:
            return self._core_plugins[plugin_id]["status"]
        if plugin_id in self._secondary_plugins:
            return self._secondary_plugins[plugin_id]["status"]
        return None


class MockConfigLoader:
    """Mock del config loader per i test"""
    
    def __init__(self):
        self.config = {
            "application": {
                "name": "LaboonChat2",
                "version": "2.0.0",
                "debug": True
            },
            "plugins": {
                "core": {
                    "security": {
                        "module": "basic_security",
                        "config": {"encryption": "AES-256"}
                    },
                    "messaging": {
                        "module": "simple_p2p_messaging",
                        "config": {"port": 8888}
                    }
                },
                "secondary": {
                    "logger": {
                        "module": "advanced_logger",
                        "config": {"level": "INFO"}
                    }
                }
            },
            "logging": {
                "level": "INFO",
                "file_rotation": True
            }
        }
    
    def load_config(self, config_path: str = None):
        return self.config
    
    def save_config(self, config: Dict[str, Any], config_path: str = None):
        self.config = config
    
    def validate_config(self, config: Dict[str, Any]):
        return True
    
    def get_plugin_config(self, plugin_type: str, plugin_id: str):
        if plugin_type == "core":
            return self.config["plugins"]["core"].get(plugin_id, {})
        elif plugin_type == "secondary":
            return self.config["plugins"]["secondary"].get(plugin_id, {})
        return {}


@pytest.fixture
def temp_config_dir():
    """Crea una directory temporanea per le configurazioni"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_config_loader():
    """Crea un mock config loader"""
    return MockConfigLoader()


@pytest.fixture
def mock_plugin_manager():
    """Crea un mock plugin manager"""
    return MockPluginManager()


@pytest.fixture
def application(temp_config_dir, mock_config_loader, mock_plugin_manager):
    """Crea un'istanza di LaboonChat2Application per i test"""
    with patch('laboon_chat2.core.application.ConfigLoader', return_value=mock_config_loader), \
         patch('laboon_chat2.core.application.ModularPluginManager', return_value=mock_plugin_manager), \
         patch('laboon_chat2.core.application.LoggerManager'):
        
        app = LaboonChat2Application(str(temp_config_dir / "config.json"))
        app._plugin_manager = mock_plugin_manager
        app._config_loader = mock_config_loader
        return app


@pytest.fixture
async def initialized_application(application):
    """Applicazione inizializzata"""
    await application.initialize()
    yield application
    if application._state != ApplicationState.STOPPED:
        await application.shutdown()


class TestLaboonChat2Application:
    """Test per LaboonChat2Application"""
    
    def test_initialization(self, application):
        """Testa l'inizializzazione dell'applicazione"""
        assert application._state == ApplicationState.STOPPED
        assert application._config_path is not None
        assert application._plugin_manager is not None
        assert application._config_loader is not None
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, application):
        """Testa inizializzazione con successo"""
        await application.initialize()
        
        assert application._state == ApplicationState.INITIALIZED
        assert application._plugin_manager._initialized
    
    @pytest.mark.asyncio
    async def test_initialize_already_initialized(self, initialized_application):
        """Testa inizializzazione quando già inizializzata"""
        # Dovrebbe essere idempotente
        await initialized_application.initialize()
        assert initialized_application._state == ApplicationState.INITIALIZED
    
    @pytest.mark.asyncio
    async def test_run_application(self, initialized_application):
        """Testa avvio dell'applicazione"""
        # Simula run in background
        run_task = asyncio.create_task(initialized_application.run())
        
        # Aspetta un po' per permettere l'avvio
        await asyncio.sleep(0.1)
        
        assert initialized_application._state == ApplicationState.RUNNING
        
        # Ferma l'applicazione
        await initialized_application.shutdown()
        
        # Aspetta che il task finisca
        await run_task
    
    @pytest.mark.asyncio
    async def test_shutdown_graceful(self, initialized_application):
        """Testa shutdown graceful"""
        # Avvia applicazione
        run_task = asyncio.create_task(initialized_application.run())
        await asyncio.sleep(0.1)
        
        # Shutdown
        await initialized_application.shutdown()
        
        assert initialized_application._state == ApplicationState.STOPPED
        
        # Aspetta che il task finisca
        await run_task
    
    @pytest.mark.asyncio
    async def test_load_core_plugins(self, initialized_application):
        """Testa caricamento plugin core"""
        result = await initialized_application.load_core_plugins()
        
        assert result is True
        # Verifica che i plugin configurati siano stati caricati
        plugins = initialized_application._plugin_manager.list_plugins()
        assert "security" in plugins["core"]
        assert "messaging" in plugins["core"]
    
    @pytest.mark.asyncio
    async def test_unload_core_plugins(self, initialized_application):
        """Testa scaricamento plugin core"""
        # Carica prima i plugin
        await initialized_application.load_core_plugins()
        
        # Scarica i plugin
        result = await initialized_application.unload_core_plugins()
        
        assert result is True
        plugins = initialized_application._plugin_manager.list_plugins()
        assert len(plugins["core"]) == 0
    
    @pytest.mark.asyncio
    async def test_load_secondary_plugins(self, initialized_application):
        """Testa caricamento plugin secondari"""
        result = await initialized_application.load_secondary_plugins()
        
        assert result is True
        plugins = initialized_application._plugin_manager.list_plugins()
        assert "logger" in plugins["secondary"]
    
    @pytest.mark.asyncio
    async def test_unload_secondary_plugins(self, initialized_application):
        """Testa scaricamento plugin secondari"""
        # Carica prima i plugin
        await initialized_application.load_secondary_plugins()
        
        # Scarica i plugin
        result = await initialized_application.unload_secondary_plugins()
        
        assert result is True
        plugins = initialized_application._plugin_manager.list_plugins()
        assert len(plugins["secondary"]) == 0
    
    def test_get_core_plugin_instance(self, initialized_application):
        """Testa recupero istanza plugin core"""
        # Test plugin non esistente
        instance = initialized_application.get_core_plugin_instance("nonexistent")
        assert instance is None
    
    def test_get_secondary_plugin_instance(self, initialized_application):
        """Testa recupero istanza plugin secondario"""
        # Test plugin non esistente
        instance = initialized_application.get_secondary_plugin_instance("nonexistent")
        assert instance is None
    
    def test_get_application_status(self, initialized_application):
        """Testa recupero stato applicazione"""
        status = initialized_application.get_application_status()
        
        assert "state" in status
        assert "uptime" in status
        assert "loaded_plugins" in status
        assert status["state"] == ApplicationState.INITIALIZED
    
    @pytest.mark.asyncio
    async def test_get_detailed_health_check(self, initialized_application):
        """Testa health check dettagliato"""
        health = await initialized_application.get_detailed_health_check()
        
        assert "application" in health
        assert "plugins" in health
        assert "system" in health
        assert health["application"]["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_load_configuration(self, initialized_application):
        """Testa caricamento configurazione"""
        result = await initialized_application.load_configuration()
        
        assert result is True
        assert initialized_application._config is not None
    
    @pytest.mark.asyncio
    async def test_reload_configuration(self, initialized_application):
        """Testa ricaricamento configurazione"""
        # Modifica configurazione
        new_config = {"test": "value"}
        initialized_application._config_loader.config.update(new_config)
        
        result = await initialized_application.reload_configuration()
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_update_plugin_config(self, initialized_application):
        """Testa aggiornamento configurazione plugin"""
        new_config = {"new_setting": "value"}
        
        result = await initialized_application.update_plugin_config(
            "core", "security", new_config
        )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_error_handling_initialization(self, application):
        """Testa gestione errori durante inizializzazione"""
        # Simula errore nel plugin manager
        application._plugin_manager.initialize = AsyncMock(side_effect=Exception("Init error"))
        
        with pytest.raises(ApplicationError, match="Errore durante l'inizializzazione"):
            await application.initialize()
    
    @pytest.mark.asyncio
    async def test_error_handling_plugin_loading(self, initialized_application):
        """Testa gestione errori durante caricamento plugin"""
        # Simula errore nel caricamento
        initialized_application._plugin_manager.load_core_plugin = AsyncMock(
            side_effect=Exception("Load error")
        )
        
        result = await initialized_application.load_core_plugins()
        assert result is False
    
    def test_application_state_enum(self):
        """Testa enum ApplicationState"""
        assert ApplicationState.STOPPED == "stopped"
        assert ApplicationState.INITIALIZED == "initialized"
        assert ApplicationState.RUNNING == "running"
        assert ApplicationState.SHUTTING_DOWN == "shutting_down"
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, initialized_application):
        """Testa operazioni concorrenti"""
        # Avvia operazioni concorrenti
        tasks = [
            initialized_application.load_core_plugins(),
            initialized_application.load_secondary_plugins(),
            initialized_application.get_detailed_health_check()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verifica che non ci siano eccezioni
        for result in results:
            assert not isinstance(result, Exception)
    
    @pytest.mark.asyncio
    async def test_plugin_lifecycle_integration(self, initialized_application):
        """Test integrazione completa del ciclo di vita plugin"""
        # Carica plugin core
        await initialized_application.load_core_plugins()
        
        # Verifica caricamento
        security_instance = initialized_application.get_core_plugin_instance("security")
        assert security_instance is not None
        
        # Carica plugin secondari
        await initialized_application.load_secondary_plugins()
        
        # Verifica stato
        status = initialized_application.get_application_status()
        assert len(status["loaded_plugins"]["core"]) > 0
        assert len(status["loaded_plugins"]["secondary"]) > 0
        
        # Scarica tutto
        await initialized_application.unload_secondary_plugins()
        await initialized_application.unload_core_plugins()
        
        # Verifica pulizia
        final_status = initialized_application.get_application_status()
        assert len(final_status["loaded_plugins"]["core"]) == 0
        assert len(final_status["loaded_plugins"]["secondary"]) == 0


class TestApplicationFactoryFunctions:
    """Test per le funzioni factory dell'applicazione"""
    
    @pytest.mark.asyncio
    async def test_create_application(self, temp_config_dir):
        """Testa creazione applicazione tramite factory"""
        config_path = str(temp_config_dir / "test_config.json")
        
        with patch('laboon_chat2.core.application.ConfigLoader'), \
             patch('laboon_chat2.core.application.ModularPluginManager'), \
             patch('laboon_chat2.core.application.LoggerManager'):
            
            app = create_application(config_path)
            
            assert isinstance(app, LaboonChat2Application)
            assert app._config_path == config_path
    
    @pytest.mark.asyncio
    async def test_run_application_function(self, temp_config_dir):
        """Testa funzione run_application"""
        config_path = str(temp_config_dir / "test_config.json")
        
        with patch('laboon_chat2.core.application.ConfigLoader'), \
             patch('laboon_chat2.core.application.ModularPluginManager'), \
             patch('laboon_chat2.core.application.LoggerManager'):
            
            # Mock dell'applicazione per evitare loop infinito
            mock_app = Mock()
            mock_app.initialize = AsyncMock()
            mock_app.run = AsyncMock()
            
            with patch('laboon_chat2.core.application.create_application', return_value=mock_app):
                await run_application(config_path)
                
                mock_app.initialize.assert_called_once()
                mock_app.run.assert_called_once()


@pytest.mark.asyncio
async def test_application_integration_complete():
    """Test di integrazione completo dell'applicazione"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = Path(temp_dir) / "config.json"
        
        # Crea configurazione di test
        test_config = {
            "application": {
                "name": "TestApp",
                "version": "1.0.0"
            },
            "plugins": {
                "core": {},
                "secondary": {}
            }
        }
        
        with patch('laboon_chat2.core.application.ConfigLoader') as mock_config_class, \
             patch('laboon_chat2.core.application.ModularPluginManager') as mock_manager_class, \
             patch('laboon_chat2.core.application.LoggerManager'):
            
            # Setup mocks
            mock_config = MockConfigLoader()
            mock_config.config = test_config
            mock_config_class.return_value = mock_config
            
            mock_manager = MockPluginManager()
            mock_manager_class.return_value = mock_manager
            
            # Crea e testa applicazione
            app = LaboonChat2Application(str(config_path))
            
            try:
                # Test ciclo di vita completo
                await app.initialize()
                assert app._state == ApplicationState.INITIALIZED
                
                # Test caricamento configurazione
                await app.load_configuration()
                
                # Test health check
                health = await app.get_detailed_health_check()
                assert health["application"]["status"] == "healthy"
                
                # Test stato
                status = app.get_application_status()
                assert status["state"] == ApplicationState.INITIALIZED
                
            finally:
                if app._state != ApplicationState.STOPPED:
                    await app.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])