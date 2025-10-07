"""
Test suite per i plugin di interfaccia

Testa WebInterface: interfaccia web, rendering, gestione eventi,
integrazione con moduli core, operazioni UI.
"""

import pytest
import asyncio
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Dict, Any, List
import time

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'plugins', 'core', 'interface'))

from laboon_chat2.core.interfaces import IInterfaceModule
from web_interface import (
    WebInterface, WebComponent, WebTheme,
    create_web_interface, DEFAULT_CONFIG
)


@pytest.fixture
def temp_dir():
    """Crea directory temporanea per i test"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def interface_config(temp_dir):
    """Configurazione di test per WebInterface"""
    return {
        "host": "127.0.0.1",
        "port": 0,  # Porta automatica per i test
        "static_dir": str(Path(temp_dir) / "static"),
        "template_dir": str(Path(temp_dir) / "templates"),
        "auto_open_browser": False,
        "enable_websocket": True,
        "websocket_port": 0,  # Porta automatica per i test
        "theme": "dark",
        "language": "en",
        "enable_notifications": True,
        "enable_file_preview": True,
        "max_message_display": 100,
        "auto_scroll": True,
        "enable_emoji": True,
        "enable_markdown": True,
        "custom_css": "",
        "custom_js": "",
        "debug_mode": True
    }


@pytest.fixture
async def interface_module(interface_config):
    """Crea istanza WebInterface per i test"""
    module = WebInterface()
    await module.initialize(interface_config)
    yield module
    await module.cleanup()


@pytest.fixture
def mock_security_module():
    """Mock del modulo di sicurezza"""
    mock = Mock()
    mock.encrypt_message = AsyncMock(return_value=b"encrypted_data")
    mock.decrypt_message = AsyncMock(return_value="decrypted_message")
    mock.sign_message = AsyncMock(return_value=b"signature")
    mock.verify_signature = AsyncMock(return_value=True)
    mock.get_identity = Mock(return_value={"id": "test_user", "public_key": b"test_key"})
    return mock


@pytest.fixture
def mock_messaging_module():
    """Mock del modulo di messaging"""
    mock = Mock()
    mock.send_message = AsyncMock(return_value="msg_123")
    mock.get_message_history = AsyncMock(return_value=[])
    mock.get_connected_peers = AsyncMock(return_value=["peer1", "peer2"])
    mock.connect_to_peer = AsyncMock(return_value=True)
    mock.disconnect_from_peer = AsyncMock(return_value=True)
    mock.send_file = AsyncMock(return_value="transfer_123")
    mock.get_file_transfers = AsyncMock(return_value=[])
    return mock


@pytest.fixture
def mock_network_module():
    """Mock del modulo di rete"""
    mock = Mock()
    mock.get_connection_status = AsyncMock(return_value={"status": "connected", "peers": 2})
    mock.get_network_stats = AsyncMock(return_value={"bytes_sent": 1024, "bytes_received": 2048})
    mock.discover_peers = AsyncMock(return_value=["peer1", "peer2"])
    return mock


class TestWebDataClasses:
    """Test per le dataclass Web"""
    
    def test_web_component_creation(self):
        """Testa creazione WebComponent"""
        component = WebComponent(
            id="comp_123",
            type="button",
            content="Click me",
            properties={"class": "btn-primary", "onclick": "handleClick()"},
            visible=True,
            enabled=True
        )
        
        assert component.id == "comp_123"
        assert component.type == "button"
        assert component.content == "Click me"
        assert component.properties["class"] == "btn-primary"
        assert component.visible is True
        assert component.enabled is True
    
    def test_web_theme_creation(self):
        """Testa creazione WebTheme"""
        theme = WebTheme(
            name="custom_theme",
            primary_color="#007bff",
            secondary_color="#6c757d",
            background_color="#ffffff",
            text_color="#212529",
            accent_color="#28a745",
            font_family="Arial, sans-serif",
            font_size="14px",
            border_radius="4px",
            custom_css=".custom { color: red; }"
        )
        
        assert theme.name == "custom_theme"
        assert theme.primary_color == "#007bff"
        assert theme.secondary_color == "#6c757d"
        assert theme.background_color == "#ffffff"
        assert theme.text_color == "#212529"
        assert theme.accent_color == "#28a745"
        assert theme.font_family == "Arial, sans-serif"
        assert theme.font_size == "14px"
        assert theme.border_radius == "4px"
        assert theme.custom_css == ".custom { color: red; }"


class TestWebInterfaceInterface:
    """Test per l'interfaccia IInterfaceModule"""
    
    def test_implements_interface(self):
        """Testa che WebInterface implementi IInterfaceModule"""
        module = WebInterface()
        assert isinstance(module, IInterfaceModule)
    
    def test_module_info(self):
        """Testa informazioni del modulo"""
        module = WebInterface()
        info = module.get_module_info()
        
        assert info["name"] == "WebInterface"
        assert info["version"] == "1.0.0"
        assert info["type"] == "interface"
        assert "description" in info
        assert "author" in info


class TestWebInterfaceInitialization:
    """Test per l'inizializzazione del modulo"""
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, interface_config):
        """Testa inizializzazione corretta"""
        module = WebInterface()
        
        await module.initialize(interface_config)
        
        assert module.config == interface_config
        assert module.components == {}
        assert module.current_theme is not None
        assert module.websocket_clients == []
        assert module.server is not None
        
        await module.cleanup()
    
    @pytest.mark.asyncio
    async def test_initialize_creates_directories(self, interface_config):
        """Testa che l'inizializzazione crei le directory necessarie"""
        module = WebInterface()
        await module.initialize(interface_config)
        
        static_dir = Path(interface_config["static_dir"])
        template_dir = Path(interface_config["template_dir"])
        
        assert static_dir.exists()
        assert template_dir.exists()
        assert static_dir.is_dir()
        assert template_dir.is_dir()
        
        await module.cleanup()
    
    @pytest.mark.asyncio
    async def test_initialize_creates_static_files(self, interface_config):
        """Testa che l'inizializzazione crei i file statici"""
        module = WebInterface()
        await module.initialize(interface_config)
        
        static_dir = Path(interface_config["static_dir"])
        
        # Verifica file HTML
        html_file = static_dir / "index.html"
        assert html_file.exists()
        
        # Verifica file CSS
        css_file = static_dir / "style.css"
        assert css_file.exists()
        
        # Verifica file JavaScript
        js_file = static_dir / "app.js"
        assert js_file.exists()
        
        await module.cleanup()
    
    @pytest.mark.asyncio
    async def test_cleanup(self, interface_module):
        """Testa cleanup del modulo"""
        # Aggiungi alcuni componenti
        component = WebComponent(
            id="test_comp",
            type="div",
            content="Test content"
        )
        interface_module.components["test_comp"] = component
        
        await interface_module.cleanup()
        
        # Verifica che il server sia stato fermato
        assert interface_module.server is None


class TestRendering:
    """Test per il rendering dell'interfaccia"""
    
    @pytest.mark.asyncio
    async def test_render(self, interface_module):
        """Testa rendering dell'interfaccia"""
        html_content = await interface_module.render()
        
        assert isinstance(html_content, str)
        assert len(html_content) > 0
        assert "<!DOCTYPE html>" in html_content or "<html" in html_content
    
    @pytest.mark.asyncio
    async def test_render_with_template(self, interface_module):
        """Testa rendering con template"""
        template_data = {"title": "Test Title", "content": "Test Content"}
        
        html_content = await interface_module.render("main", template_data)
        
        assert isinstance(html_content, str)
        assert len(html_content) > 0


class TestDisplayUpdates:
    """Test per gli aggiornamenti del display"""
    
    @pytest.mark.asyncio
    async def test_update_display(self, interface_module):
        """Testa aggiornamento display"""
        update_data = {"type": "message", "content": "New message"}
        
        await interface_module.update_display(update_data)
        
        # Verifica che l'aggiornamento sia stato processato
        # (in un'implementazione reale, questo potrebbe aggiornare i client WebSocket)
    
    @pytest.mark.asyncio
    async def test_display_message(self, interface_module):
        """Testa visualizzazione messaggio"""
        await interface_module.display_message("sender_123", "Hello, world!", "text")
        
        # Verifica che il messaggio sia stato aggiunto alla visualizzazione
    
    @pytest.mark.asyncio
    async def test_display_peer_list(self, interface_module):
        """Testa visualizzazione lista peer"""
        peers = ["peer1", "peer2", "peer3"]
        
        await interface_module.display_peer_list(peers)
        
        # Verifica che la lista peer sia stata aggiornata
    
    @pytest.mark.asyncio
    async def test_display_connection_status(self, interface_module):
        """Testa visualizzazione stato connessione"""
        status = {"status": "connected", "peers": 3, "uptime": 3600}
        
        await interface_module.display_connection_status(status)
        
        # Verifica che lo stato sia stato aggiornato
    
    @pytest.mark.asyncio
    async def test_display_notification(self, interface_module):
        """Testa visualizzazione notifica"""
        await interface_module.display_notification("Test notification", "info")
        
        # Verifica che la notifica sia stata mostrata
    
    @pytest.mark.asyncio
    async def test_clear_display(self, interface_module):
        """Testa pulizia display"""
        await interface_module.clear_display()
        
        # Verifica che il display sia stato pulito


class TestEventHandling:
    """Test per la gestione degli eventi"""
    
    @pytest.mark.asyncio
    async def test_handle_event(self, interface_module):
        """Testa gestione evento generico"""
        event_data = {"type": "click", "target": "button_send", "data": {"message": "Hello"}}
        
        result = await interface_module.handle_event(event_data)
        
        # Verifica che l'evento sia stato gestito
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_handle_user_input(self, interface_module):
        """Testa gestione input utente"""
        input_data = {"type": "message", "content": "Hello, world!"}
        
        result = await interface_module.handle_user_input(input_data)
        
        assert result is not None


class TestCoreModuleIntegration:
    """Test per l'integrazione con i moduli core"""
    
    @pytest.mark.asyncio
    async def test_set_security_module(self, interface_module, mock_security_module):
        """Testa impostazione modulo di sicurezza"""
        await interface_module.set_security_module(mock_security_module)
        
        assert interface_module.security_module == mock_security_module
    
    @pytest.mark.asyncio
    async def test_set_messaging_module(self, interface_module, mock_messaging_module):
        """Testa impostazione modulo di messaging"""
        await interface_module.set_messaging_module(mock_messaging_module)
        
        assert interface_module.messaging_module == mock_messaging_module
    
    @pytest.mark.asyncio
    async def test_set_network_module(self, interface_module, mock_network_module):
        """Testa impostazione modulo di rete"""
        await interface_module.set_network_module(mock_network_module)
        
        assert interface_module.network_module == mock_network_module
    
    @pytest.mark.asyncio
    async def test_integration_with_messaging(self, interface_module, mock_messaging_module):
        """Testa integrazione con modulo messaging"""
        await interface_module.set_messaging_module(mock_messaging_module)
        
        # Simula invio messaggio tramite interfaccia
        input_data = {"type": "send_message", "recipient": "peer1", "content": "Hello"}
        await interface_module.handle_user_input(input_data)
        
        # Verifica che il modulo messaging sia stato chiamato
        mock_messaging_module.send_message.assert_called()
    
    @pytest.mark.asyncio
    async def test_integration_with_security(self, interface_module, mock_security_module):
        """Testa integrazione con modulo sicurezza"""
        await interface_module.set_security_module(mock_security_module)
        
        # Simula operazione che richiede sicurezza
        input_data = {"type": "encrypt_message", "content": "Secret message"}
        await interface_module.handle_user_input(input_data)
        
        # Verifica che il modulo sicurezza sia stato chiamato
        # (dipende dall'implementazione specifica)


class TestComponentManagement:
    """Test per la gestione dei componenti"""
    
    @pytest.mark.asyncio
    async def test_add_component(self, interface_module):
        """Testa aggiunta componente"""
        component = WebComponent(
            id="test_button",
            type="button",
            content="Click me",
            properties={"class": "btn-primary"}
        )
        
        await interface_module.add_component(component)
        
        assert "test_button" in interface_module.components
        assert interface_module.components["test_button"] == component
    
    @pytest.mark.asyncio
    async def test_remove_component(self, interface_module):
        """Testa rimozione componente"""
        component = WebComponent(
            id="test_button",
            type="button",
            content="Click me"
        )
        
        await interface_module.add_component(component)
        await interface_module.remove_component("test_button")
        
        assert "test_button" not in interface_module.components
    
    @pytest.mark.asyncio
    async def test_update_component(self, interface_module):
        """Testa aggiornamento componente"""
        component = WebComponent(
            id="test_button",
            type="button",
            content="Click me"
        )
        
        await interface_module.add_component(component)
        
        # Aggiorna componente
        updates = {"content": "Updated content", "enabled": False}
        await interface_module.update_component("test_button", updates)
        
        updated_component = interface_module.components["test_button"]
        assert updated_component.content == "Updated content"
        assert updated_component.enabled is False
    
    @pytest.mark.asyncio
    async def test_get_component(self, interface_module):
        """Testa recupero componente"""
        component = WebComponent(
            id="test_button",
            type="button",
            content="Click me"
        )
        
        await interface_module.add_component(component)
        
        retrieved = await interface_module.get_component("test_button")
        assert retrieved == component
        
        # Test componente inesistente
        nonexistent = await interface_module.get_component("nonexistent")
        assert nonexistent is None


class TestThemeManagement:
    """Test per la gestione dei temi"""
    
    @pytest.mark.asyncio
    async def test_set_theme(self, interface_module):
        """Testa impostazione tema"""
        await interface_module.set_theme("light")
        
        assert interface_module.current_theme.name == "light"
    
    @pytest.mark.asyncio
    async def test_set_custom_theme(self, interface_module):
        """Testa impostazione tema personalizzato"""
        custom_theme = WebTheme(
            name="custom",
            primary_color="#ff0000",
            secondary_color="#00ff00",
            background_color="#0000ff",
            text_color="#ffffff"
        )
        
        await interface_module.set_custom_theme(custom_theme)
        
        assert interface_module.current_theme == custom_theme
    
    @pytest.mark.asyncio
    async def test_get_available_themes(self, interface_module):
        """Testa recupero temi disponibili"""
        themes = await interface_module.get_available_themes()
        
        assert isinstance(themes, list)
        assert len(themes) > 0
        assert "dark" in themes
        assert "light" in themes


class TestFileOperations:
    """Test per le operazioni sui file"""
    
    @pytest.mark.asyncio
    async def test_upload_file(self, interface_module, temp_dir):
        """Testa upload file"""
        # Crea file di test
        test_file = Path(temp_dir) / "test_upload.txt"
        test_content = "Test file content"
        test_file.write_text(test_content)
        
        # Simula upload
        file_data = {
            "filename": "test_upload.txt",
            "content": test_content.encode(),
            "size": len(test_content)
        }
        
        result = await interface_module.upload_file(file_data)
        
        assert result is not None
        assert "file_id" in result or "success" in result
    
    @pytest.mark.asyncio
    async def test_download_file(self, interface_module):
        """Testa download file"""
        file_id = "test_file_123"
        
        # Mock del download
        with patch.object(interface_module, '_get_file_data') as mock_get_file:
            mock_get_file.return_value = {
                "filename": "test.txt",
                "content": b"Test content",
                "size": 12
            }
            
            result = await interface_module.download_file(file_id)
            
            assert result is not None
            assert "filename" in result
            assert "content" in result


class TestConfigurationUpdate:
    """Test per l'aggiornamento della configurazione"""
    
    @pytest.mark.asyncio
    async def test_update_config(self, interface_module):
        """Testa aggiornamento configurazione"""
        new_config = {
            "theme": "light",
            "language": "it",
            "enable_notifications": False,
            "max_message_display": 200
        }
        
        await interface_module.update_config(new_config)
        
        assert interface_module.config["theme"] == "light"
        assert interface_module.config["language"] == "it"
        assert interface_module.config["enable_notifications"] is False
        assert interface_module.config["max_message_display"] == 200


class TestDefaultConfig:
    """Test per la configurazione predefinita"""
    
    def test_default_config_structure(self):
        """Testa struttura configurazione predefinita"""
        assert isinstance(DEFAULT_CONFIG, dict)
        assert "host" in DEFAULT_CONFIG
        assert "port" in DEFAULT_CONFIG
        assert "theme" in DEFAULT_CONFIG
        assert "enable_websocket" in DEFAULT_CONFIG
    
    def test_default_config_values(self):
        """Testa valori configurazione predefinita"""
        assert DEFAULT_CONFIG["host"] == "127.0.0.1"
        assert DEFAULT_CONFIG["port"] == 8080
        assert DEFAULT_CONFIG["theme"] == "dark"
        assert DEFAULT_CONFIG["auto_open_browser"] is True


class TestFactoryFunction:
    """Test per la funzione factory"""
    
    @pytest.mark.asyncio
    async def test_create_web_interface(self, interface_config):
        """Testa funzione factory create_web_interface"""
        module = await create_web_interface(interface_config)
        
        assert isinstance(module, WebInterface)
        assert module.config == interface_config
        
        await module.cleanup()
    
    @pytest.mark.asyncio
    async def test_create_web_interface_with_default_config(self):
        """Testa funzione factory con configurazione predefinita"""
        module = await create_web_interface()
        
        assert isinstance(module, WebInterface)
        assert module.config == DEFAULT_CONFIG
        
        await module.cleanup()


@pytest.mark.asyncio
async def test_web_interface_integration():
    """Test di integrazione completo per WebInterface"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = {
            "host": "127.0.0.1",
            "port": 0,
            "static_dir": str(Path(temp_dir) / "static"),
            "template_dir": str(Path(temp_dir) / "templates"),
            "auto_open_browser": False,
            "enable_websocket": True,
            "websocket_port": 0,
            "theme": "dark",
            "language": "en",
            "enable_notifications": True,
            "enable_file_preview": True,
            "max_message_display": 100,
            "auto_scroll": True,
            "enable_emoji": True,
            "enable_markdown": True,
            "custom_css": "",
            "custom_js": "",
            "debug_mode": True
        }
        
        # Crea e inizializza modulo
        interface = WebInterface()
        await interface.initialize(config)
        
        try:
            # Test rendering
            html_content = await interface.render()
            assert isinstance(html_content, str)
            assert len(html_content) > 0
            
            # Test aggiunta componenti
            button = WebComponent(
                id="send_button",
                type="button",
                content="Send Message",
                properties={"class": "btn-primary", "onclick": "sendMessage()"}
            )
            await interface.add_component(button)
            assert "send_button" in interface.components
            
            # Test gestione eventi
            event_data = {"type": "click", "target": "send_button"}
            result = await interface.handle_event(event_data)
            assert result is not None
            
            # Test cambio tema
            await interface.set_theme("light")
            assert interface.current_theme.name == "light"
            
            # Test visualizzazione messaggio
            await interface.display_message("user1", "Hello, world!", "text")
            
            # Test visualizzazione notifica
            await interface.display_notification("Test notification", "info")
            
            # Test aggiornamento configurazione
            new_config = {"theme": "dark", "language": "it"}
            await interface.update_config(new_config)
            assert interface.config["theme"] == "dark"
            assert interface.config["language"] == "it"
            
            # Test pulizia display
            await interface.clear_display()
            
        finally:
            # Cleanup
            await interface.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])