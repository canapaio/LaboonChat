"""
Test suite per ModularPluginManager

Testa tutte le funzionalità del sistema di gestione plugin modulare
inclusi caricamento, scaricamento, hot-swapping e gestione eventi.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, Optional

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from laboon_chat2.core.plugin_manager import (
    ModularPluginManager, PluginType, PluginStatus, PluginInfo,
    PluginError, PluginLoadError, PluginUnloadError, PluginNotFoundError
)
from laboon_chat2.interfaces import (
    ISecurityModule, IMessagingModule, IInterfaceModule, INetworkModule
)
from laboon_chat2.interfaces.secondary_plugin_interface import ISecondaryPlugin


class MockSecurityModule(ISecurityModule):
    """Mock del modulo di sicurezza per i test"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._initialized = False
    
    async def initialize(self) -> None:
        self._initialized = True
    
    async def cleanup(self) -> None:
        self._initialized = False
    
    def get_module_info(self) -> Dict[str, Any]:
        return {
            "name": "MockSecurity",
            "version": "1.0.0",
            "description": "Mock security module for testing"
        }
    
    # Implementazioni mock per tutti i metodi richiesti
    async def generate_identity(self, identity_name: str) -> str:
        return f"mock_identity_{identity_name}"
    
    async def load_identity(self, identity_path: str) -> bool:
        return True
    
    def get_current_identity(self) -> Optional[Dict[str, Any]]:
        return {"id": "mock_identity", "public_key": "mock_key"}
    
    async def encrypt_message(self, message: str, recipient_id: str) -> bytes:
        return b"encrypted_mock"
    
    async def decrypt_message(self, encrypted_data: bytes, sender_id: str) -> str:
        return "decrypted_mock"
    
    async def sign_data(self, data: bytes) -> bytes:
        return b"signature_mock"
    
    async def verify_signature(self, data: bytes, signature: bytes, signer_id: str) -> bool:
        return True
    
    async def generate_session_key(self, peer_id: str) -> str:
        return f"session_key_{peer_id}"
    
    async def get_session_key(self, peer_id: str) -> Optional[str]:
        return f"session_key_{peer_id}"
    
    async def revoke_session_key(self, peer_id: str) -> bool:
        return True
    
    async def rotate_keys(self) -> bool:
        return True
    
    async def authenticate_peer(self, peer_id: str, challenge: bytes) -> bool:
        return True
    
    async def add_trusted_peer(self, peer_id: str, public_key: str) -> bool:
        return True
    
    async def remove_trusted_peer(self, peer_id: str) -> bool:
        return True
    
    async def is_trusted_peer(self, peer_id: str) -> bool:
        return True
    
    async def blacklist_peer(self, peer_id: str, reason: str) -> bool:
        return True
    
    async def unblacklist_peer(self, peer_id: str) -> bool:
        return True
    
    async def is_blacklisted_peer(self, peer_id: str) -> bool:
        return False
    
    def update_security_config(self, config: Dict[str, Any]) -> None:
        self.config.update(config)


class MockSecondaryPlugin(ISecondaryPlugin):
    """Mock del plugin secondario per i test"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._initialized = False
        self._active = False
    
    async def initialize(self) -> None:
        self._initialized = True
    
    async def cleanup(self) -> None:
        self._initialized = False
        self._active = False
    
    def get_plugin_metadata(self) -> Dict[str, Any]:
        return {
            "name": "MockSecondaryPlugin",
            "version": "1.0.0",
            "description": "Mock secondary plugin for testing",
            "category": "utility",
            "priority": "medium"
        }
    
    async def activate(self) -> None:
        self._active = True
    
    async def deactivate(self) -> None:
        self._active = False
    
    async def reload(self) -> None:
        await self.deactivate()
        await self.activate()
    
    async def handle_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        pass
    
    def register_event_handler(self, event_type: str, handler) -> None:
        pass
    
    async def emit_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        pass
    
    def get_supported_events(self) -> list:
        return ["test_event"]
    
    async def call_plugin_method(self, plugin_id: str, method_name: str, *args, **kwargs) -> Any:
        return None
    
    def get_plugin_api(self) -> Dict[str, Any]:
        return {}
    
    async def share_data(self, key: str, data: Any) -> None:
        pass
    
    async def get_shared_data(self, key: str) -> Any:
        return None
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {}
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        return True
    
    def update_config(self, config: Dict[str, Any]) -> None:
        self.config.update(config)
    
    def get_current_config(self) -> Dict[str, Any]:
        return self.config
    
    def get_resource_usage(self) -> Dict[str, Any]:
        return {"memory": 0, "cpu": 0}
    
    def set_resource_limits(self, limits: Dict[str, Any]) -> None:
        pass
    
    async def optimize_resources(self) -> None:
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        return {"status": "healthy"}
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        return {}
    
    def reset_metrics(self) -> None:
        pass
    
    async def execute_feature(self, feature_name: str, *args, **kwargs) -> Any:
        return f"executed_{feature_name}"
    
    def get_available_features(self) -> list:
        return ["test_feature"]
    
    async def schedule_task(self, task_name: str, interval: float, callback) -> str:
        return f"task_{task_name}"
    
    async def cancel_task(self, task_id: str) -> bool:
        return True


@pytest.fixture
def temp_plugin_dir():
    """Crea una directory temporanea per i plugin"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def plugin_manager(temp_plugin_dir):
    """Crea un'istanza di ModularPluginManager per i test"""
    config = {
        "core_plugins_dir": str(temp_plugin_dir / "core"),
        "secondary_plugins_dir": str(temp_plugin_dir / "secondary"),
        "auto_discover": False
    }
    return ModularPluginManager(config)


@pytest.fixture
async def initialized_manager(plugin_manager):
    """Plugin manager inizializzato"""
    await plugin_manager.initialize()
    yield plugin_manager
    await plugin_manager.cleanup()


class TestModularPluginManager:
    """Test per ModularPluginManager"""
    
    def test_initialization(self, plugin_manager):
        """Testa l'inizializzazione del plugin manager"""
        assert not plugin_manager._initialized
        assert plugin_manager._core_plugins == {}
        assert plugin_manager._secondary_plugins == {}
        assert plugin_manager._event_handlers == {}
    
    @pytest.mark.asyncio
    async def test_initialize_and_cleanup(self, plugin_manager):
        """Testa inizializzazione e pulizia"""
        # Test inizializzazione
        await plugin_manager.initialize()
        assert plugin_manager._initialized
        
        # Test pulizia
        await plugin_manager.cleanup()
        assert not plugin_manager._initialized
    
    @pytest.mark.asyncio
    async def test_load_core_plugin_success(self, initialized_manager):
        """Testa caricamento plugin core con successo"""
        mock_plugin = MockSecurityModule()
        
        with patch.object(initialized_manager, '_import_plugin_class', return_value=MockSecurityModule):
            result = await initialized_manager.load_core_plugin(
                "security", "mock_security", {"test": "config"}
            )
            
            assert result is True
            assert "security" in initialized_manager._core_plugins
            
            plugin_info = initialized_manager._core_plugins["security"]
            assert plugin_info.plugin_id == "security"
            assert plugin_info.plugin_type == PluginType.CORE
            assert plugin_info.status == PluginStatus.LOADED
    
    @pytest.mark.asyncio
    async def test_load_core_plugin_duplicate(self, initialized_manager):
        """Testa caricamento plugin core duplicato"""
        with patch.object(initialized_manager, '_import_plugin_class', return_value=MockSecurityModule):
            # Carica il primo plugin
            await initialized_manager.load_core_plugin("security", "mock_security")
            
            # Tenta di caricare lo stesso tipo
            with pytest.raises(PluginLoadError, match="Plugin core .* già caricato"):
                await initialized_manager.load_core_plugin("security", "mock_security2")
    
    @pytest.mark.asyncio
    async def test_unload_core_plugin_success(self, initialized_manager):
        """Testa scaricamento plugin core con successo"""
        with patch.object(initialized_manager, '_import_plugin_class', return_value=MockSecurityModule):
            # Carica plugin
            await initialized_manager.load_core_plugin("security", "mock_security")
            
            # Scarica plugin
            result = await initialized_manager.unload_core_plugin("security")
            assert result is True
            assert "security" not in initialized_manager._core_plugins
    
    @pytest.mark.asyncio
    async def test_unload_core_plugin_not_found(self, initialized_manager):
        """Testa scaricamento plugin core non esistente"""
        with pytest.raises(PluginNotFoundError):
            await initialized_manager.unload_core_plugin("nonexistent")
    
    @pytest.mark.asyncio
    async def test_load_secondary_plugin_success(self, initialized_manager):
        """Testa caricamento plugin secondario con successo"""
        with patch.object(initialized_manager, '_import_plugin_class', return_value=MockSecondaryPlugin):
            result = await initialized_manager.load_secondary_plugin(
                "test_plugin", "mock_secondary", {"test": "config"}
            )
            
            assert result is True
            assert "test_plugin" in initialized_manager._secondary_plugins
            
            plugin_info = initialized_manager._secondary_plugins["test_plugin"]
            assert plugin_info.plugin_id == "test_plugin"
            assert plugin_info.plugin_type == PluginType.SECONDARY
            assert plugin_info.status == PluginStatus.LOADED
    
    @pytest.mark.asyncio
    async def test_activate_secondary_plugin(self, initialized_manager):
        """Testa attivazione plugin secondario"""
        with patch.object(initialized_manager, '_import_plugin_class', return_value=MockSecondaryPlugin):
            # Carica plugin
            await initialized_manager.load_secondary_plugin("test_plugin", "mock_secondary")
            
            # Attiva plugin
            result = await initialized_manager.activate_secondary_plugin("test_plugin")
            assert result is True
            
            plugin_info = initialized_manager._secondary_plugins["test_plugin"]
            assert plugin_info.status == PluginStatus.ACTIVE
    
    @pytest.mark.asyncio
    async def test_deactivate_secondary_plugin(self, initialized_manager):
        """Testa disattivazione plugin secondario"""
        with patch.object(initialized_manager, '_import_plugin_class', return_value=MockSecondaryPlugin):
            # Carica e attiva plugin
            await initialized_manager.load_secondary_plugin("test_plugin", "mock_secondary")
            await initialized_manager.activate_secondary_plugin("test_plugin")
            
            # Disattiva plugin
            result = await initialized_manager.deactivate_secondary_plugin("test_plugin")
            assert result is True
            
            plugin_info = initialized_manager._secondary_plugins["test_plugin"]
            assert plugin_info.status == PluginStatus.LOADED
    
    @pytest.mark.asyncio
    async def test_hot_swap_core_plugin(self, initialized_manager):
        """Testa hot-swap di plugin core"""
        with patch.object(initialized_manager, '_import_plugin_class', return_value=MockSecurityModule):
            # Carica plugin iniziale
            await initialized_manager.load_core_plugin("security", "mock_security")
            
            # Hot-swap con nuovo plugin
            result = await initialized_manager.hot_swap_core_plugin(
                "security", "new_mock_security", {"new": "config"}
            )
            
            assert result is True
            plugin_info = initialized_manager._core_plugins["security"]
            assert plugin_info.module_name == "new_mock_security"
    
    def test_get_core_plugin_instance(self, initialized_manager):
        """Testa recupero istanza plugin core"""
        # Test plugin non esistente
        instance = initialized_manager.get_core_plugin_instance("nonexistent")
        assert instance is None
    
    def test_get_secondary_plugin_instance(self, initialized_manager):
        """Testa recupero istanza plugin secondario"""
        # Test plugin non esistente
        instance = initialized_manager.get_secondary_plugin_instance("nonexistent")
        assert instance is None
    
    def test_list_plugins(self, initialized_manager):
        """Testa listing dei plugin"""
        plugins = initialized_manager.list_plugins()
        assert "core" in plugins
        assert "secondary" in plugins
        assert isinstance(plugins["core"], list)
        assert isinstance(plugins["secondary"], list)
    
    def test_get_plugin_status(self, initialized_manager):
        """Testa recupero stato plugin"""
        # Test plugin non esistente
        status = initialized_manager.get_plugin_status("nonexistent")
        assert status is None
    
    @pytest.mark.asyncio
    async def test_discover_plugins(self, initialized_manager, temp_plugin_dir):
        """Testa scoperta automatica plugin"""
        # Crea struttura directory plugin
        core_dir = temp_plugin_dir / "core" / "security"
        core_dir.mkdir(parents=True)
        
        # Crea file __init__.py mock
        init_file = core_dir / "__init__.py"
        init_file.write_text('''
PLUGIN_REGISTRY = {
    "MockSecurity": {
        "class": "MockSecurityModule",
        "factory": "create_mock_security",
        "type": "core",
        "category": "security"
    }
}
''')
        
        # Testa scoperta
        plugins = await initialized_manager.discover_plugins()
        assert "core" in plugins
    
    @pytest.mark.asyncio
    async def test_register_plugin_discovery(self, initialized_manager):
        """Testa registrazione plugin per scoperta"""
        plugin_info = {
            "name": "TestPlugin",
            "version": "1.0.0",
            "type": "secondary",
            "module_path": "test.plugin"
        }
        
        initialized_manager.register_plugin_for_discovery("test_plugin", plugin_info)
        
        # Verifica registrazione
        assert "test_plugin" in initialized_manager._plugin_registry
        assert initialized_manager._plugin_registry["test_plugin"] == plugin_info
    
    @pytest.mark.asyncio
    async def test_emit_event(self, initialized_manager):
        """Testa emissione eventi"""
        # Registra handler mock
        handler = AsyncMock()
        initialized_manager.register_event_handler("test_event", handler)
        
        # Emetti evento
        await initialized_manager.emit_event("test_event", {"data": "test"})
        
        # Verifica chiamata handler
        handler.assert_called_once_with({"data": "test"})
    
    def test_register_event_handler(self, initialized_manager):
        """Testa registrazione handler eventi"""
        handler = Mock()
        
        initialized_manager.register_event_handler("test_event", handler)
        
        assert "test_event" in initialized_manager._event_handlers
        assert handler in initialized_manager._event_handlers["test_event"]
    
    def test_unregister_event_handler(self, initialized_manager):
        """Testa deregistrazione handler eventi"""
        handler = Mock()
        
        # Registra handler
        initialized_manager.register_event_handler("test_event", handler)
        
        # Deregistra handler
        initialized_manager.unregister_event_handler("test_event", handler)
        
        assert handler not in initialized_manager._event_handlers.get("test_event", [])
    
    @pytest.mark.asyncio
    async def test_error_handling_load_plugin(self, initialized_manager):
        """Testa gestione errori durante caricamento plugin"""
        with patch.object(initialized_manager, '_import_plugin_class', side_effect=ImportError("Module not found")):
            with pytest.raises(PluginLoadError, match="Errore importazione"):
                await initialized_manager.load_core_plugin("security", "nonexistent_module")
    
    @pytest.mark.asyncio
    async def test_plugin_initialization_error(self, initialized_manager):
        """Testa gestione errori durante inizializzazione plugin"""
        class FailingPlugin(MockSecurityModule):
            async def initialize(self):
                raise Exception("Initialization failed")
        
        with patch.object(initialized_manager, '_import_plugin_class', return_value=FailingPlugin):
            with pytest.raises(PluginLoadError, match="Errore inizializzazione"):
                await initialized_manager.load_core_plugin("security", "failing_plugin")
    
    def test_plugin_info_dataclass(self):
        """Testa dataclass PluginInfo"""
        info = PluginInfo(
            plugin_id="test",
            plugin_type=PluginType.CORE,
            module_name="test_module",
            status=PluginStatus.LOADED,
            instance=Mock(),
            config={"test": "config"}
        )
        
        assert info.plugin_id == "test"
        assert info.plugin_type == PluginType.CORE
        assert info.status == PluginStatus.LOADED
        assert info.config == {"test": "config"}
    
    def test_plugin_enums(self):
        """Testa enum PluginType e PluginStatus"""
        # Test PluginType
        assert PluginType.CORE == "core"
        assert PluginType.SECONDARY == "secondary"
        
        # Test PluginStatus
        assert PluginStatus.LOADED == "loaded"
        assert PluginStatus.ACTIVE == "active"
        assert PluginStatus.INACTIVE == "inactive"
        assert PluginStatus.ERROR == "error"


@pytest.mark.asyncio
async def test_plugin_manager_integration():
    """Test di integrazione completo del plugin manager"""
    config = {
        "core_plugins_dir": "test_core",
        "secondary_plugins_dir": "test_secondary",
        "auto_discover": False
    }
    
    manager = ModularPluginManager(config)
    
    try:
        # Inizializza
        await manager.initialize()
        
        # Simula caricamento plugin
        with patch.object(manager, '_import_plugin_class', return_value=MockSecurityModule):
            await manager.load_core_plugin("security", "mock_security")
            
            # Verifica stato
            assert manager.get_plugin_status("security") == PluginStatus.LOADED
            
            # Verifica istanza
            instance = manager.get_core_plugin_instance("security")
            assert instance is not None
            assert isinstance(instance, MockSecurityModule)
        
        # Test eventi
        handler_called = False
        
        async def test_handler(data):
            nonlocal handler_called
            handler_called = True
        
        manager.register_event_handler("test", test_handler)
        await manager.emit_event("test", {})
        
        assert handler_called
        
    finally:
        await manager.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])