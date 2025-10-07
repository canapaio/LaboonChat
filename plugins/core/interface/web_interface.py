"""
Web Interface Module for LaboonChat v2.0

This module provides a modern web-based interface for LaboonChat
with real-time messaging, file transfer, and peer management.
"""

import asyncio
import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any, Set
from dataclasses import dataclass, asdict
import logging
import webbrowser
from threading import Lock

from laboon_chat2.interfaces import IInterfaceModule
from laboon_chat2.interfaces.interface_interface import (
    InterfaceError, RenderingError, EventHandlingError,
    ComponentError, LayoutError, ThemeError, FileOperationError
)


@dataclass
class WebComponent:
    """Rappresenta un componente dell'interfaccia web"""
    id: str
    type: str
    properties: Dict[str, Any]
    children: List[str] = None
    visible: bool = True
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte il componente in dizionario"""
        return asdict(self)


@dataclass
class WebTheme:
    """Rappresenta un tema dell'interfaccia web"""
    name: str
    colors: Dict[str, str]
    fonts: Dict[str, str]
    spacing: Dict[str, str]
    custom_css: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte il tema in dizionario"""
        return asdict(self)


class WebInterface(IInterfaceModule):
    """
    Implementazione di un'interfaccia web moderna per LaboonChat.
    
    Fornisce:
    - Interfaccia web responsiva
    - Chat in tempo reale
    - Gestione peer
    - Trasferimento file
    - Temi personalizzabili
    - Notifiche
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Inizializza l'interfaccia web"""
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.WebInterface")
        
        # Stato del modulo
        self._initialized = False
        self._running = False
        self._lock = Lock()
        
        # Configurazione
        self._host = self.config.get("host", "localhost")
        self._port = self.config.get("port", 8080)
        self._auto_open = self.config.get("auto_open", True)
        self._theme_name = self.config.get("theme", "default")
        
        # Storage
        self._static_dir = Path(self.config.get("static_dir", "static"))
        self._templates_dir = Path(self.config.get("templates_dir", "templates"))
        self._static_dir.mkdir(parents=True, exist_ok=True)
        self._templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Stato interno
        self._components: Dict[str, WebComponent] = {}
        self._themes: Dict[str, WebTheme] = {}
        self._current_layout = "default"
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._websocket_clients: Set[Any] = set()
        
        # Riferimenti ai moduli core
        self._security_module = None
        self._messaging_module = None
        self._network_module = None
        
        # Server web
        self._web_server = None
        self._server_task = None
        
        # Inizializza temi di default
        self._init_default_themes()
        
        # Inizializza componenti di default
        self._init_default_components()
        
        self.logger.info("WebInterface inizializzato")
    
    async def initialize(self) -> None:
        """Inizializza l'interfaccia web"""
        if self._initialized:
            return
        
        try:
            # Crea file statici
            await self._create_static_files()
            
            # Avvia server web
            await self._start_web_server()
            
            # Apri browser se richiesto
            if self._auto_open:
                await self._open_browser()
            
            self._initialized = True
            self._running = True
            self.logger.info(f"WebInterface avviato su http://{self._host}:{self._port}")
            
        except Exception as e:
            self.logger.error(f"Errore durante l'inizializzazione: {e}")
            raise InterfaceError(f"Inizializzazione fallita: {e}")
    
    async def cleanup(self) -> None:
        """Pulisce le risorse dell'interfaccia"""
        if not self._initialized:
            return
        
        try:
            self._running = False
            
            # Chiudi connessioni WebSocket
            await self._close_websocket_connections()
            
            # Ferma server web
            await self._stop_web_server()
            
            self._initialized = False
            self.logger.info("WebInterface terminato con successo")
            
        except Exception as e:
            self.logger.error(f"Errore durante la pulizia: {e}")
            raise InterfaceError(f"Pulizia fallita: {e}")
    
    def get_module_info(self) -> Dict[str, Any]:
        """Restituisce informazioni sul modulo"""
        return {
            "name": "WebInterface",
            "version": "1.0.0",
            "description": "Interfaccia web moderna per LaboonChat",
            "author": "LaboonChat Team",
            "capabilities": [
                "web_interface",
                "real_time_chat",
                "file_transfer_ui",
                "peer_management",
                "themes",
                "notifications",
                "responsive_design"
            ],
            "config_schema": {
                "host": {"type": "string", "default": "localhost"},
                "port": {"type": "integer", "default": 8080},
                "auto_open": {"type": "boolean", "default": True},
                "theme": {"type": "string", "default": "default"},
                "static_dir": {"type": "string", "default": "static"},
                "templates_dir": {"type": "string", "default": "templates"}
            }
        }
    
    # Rendering e UI
    async def render_interface(self) -> None:
        """Renderizza l'interfaccia principale"""
        if not self._running:
            raise RenderingError("Interfaccia non in esecuzione")
        
        try:
            # Notifica aggiornamento UI via WebSocket
            await self._broadcast_to_clients({
                "type": "ui_update",
                "action": "render",
                "layout": self._current_layout,
                "components": {
                    comp_id: comp.to_dict() 
                    for comp_id, comp in self._components.items()
                },
                "theme": self._themes[self._theme_name].to_dict(),
                "timestamp": time.time()
            })
            
            self.logger.debug("Interfaccia renderizzata")
            
        except Exception as e:
            self.logger.error(f"Errore rendering interfaccia: {e}")
            raise RenderingError(f"Rendering fallito: {e}")
    
    async def update_display(self, element_id: str, content: Any) -> None:
        """Aggiorna un elemento del display"""
        try:
            # Aggiorna componente se esiste
            if element_id in self._components:
                self._components[element_id].properties.update({"content": content})
            
            # Notifica aggiornamento via WebSocket
            await self._broadcast_to_clients({
                "type": "element_update",
                "element_id": element_id,
                "content": content,
                "timestamp": time.time()
            })
            
            self.logger.debug(f"Display aggiornato per elemento: {element_id}")
            
        except Exception as e:
            self.logger.error(f"Errore aggiornamento display: {e}")
            raise RenderingError(f"Aggiornamento display fallito: {e}")
    
    async def refresh_interface(self) -> None:
        """Aggiorna completamente l'interfaccia"""
        try:
            await self.render_interface()
            self.logger.info("Interfaccia aggiornata completamente")
            
        except Exception as e:
            self.logger.error(f"Errore refresh interfaccia: {e}")
            raise RenderingError(f"Refresh interfaccia fallito: {e}")
    
    # Gestione eventi
    def set_event_handler(self, event_type: str, handler: Callable) -> None:
        """Imposta un handler per un tipo di evento"""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        
        if handler not in self._event_handlers[event_type]:
            self._event_handlers[event_type].append(handler)
            self.logger.debug(f"Handler aggiunto per evento: {event_type}")
    
    async def handle_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Gestisce un evento"""
        try:
            if event_type in self._event_handlers:
                for handler in self._event_handlers[event_type]:
                    try:
                        if asyncio.iscoroutinefunction(handler):
                            await handler(event_data)
                        else:
                            handler(event_data)
                    except Exception as e:
                        self.logger.error(f"Errore handler evento {event_type}: {e}")
            
            self.logger.debug(f"Evento gestito: {event_type}")
            
        except Exception as e:
            self.logger.error(f"Errore gestione evento {event_type}: {e}")
            raise EventHandlingError(f"Gestione evento fallita: {e}")
    
    # Integrazione moduli core
    def set_security_module(self, security_module: Any) -> None:
        """Imposta il modulo di sicurezza"""
        self._security_module = security_module
        self.logger.info("Modulo sicurezza collegato")
    
    def set_messaging_module(self, messaging_module: Any) -> None:
        """Imposta il modulo di messaggistica"""
        self._messaging_module = messaging_module
        self.logger.info("Modulo messaggistica collegato")
    
    def set_network_module(self, network_module: Any) -> None:
        """Imposta il modulo di rete"""
        self._network_module = network_module
        self.logger.info("Modulo rete collegato")
    
    # Lifecycle management
    async def start_interface(self) -> None:
        """Avvia l'interfaccia"""
        if not self._initialized:
            await self.initialize()
        
        self._running = True
        self.logger.info("Interfaccia avviata")
    
    async def stop_interface(self) -> None:
        """Ferma l'interfaccia"""
        self._running = False
        await self.cleanup()
        self.logger.info("Interfaccia fermata")
    
    def get_interface_status(self) -> Dict[str, Any]:
        """Restituisce lo stato dell'interfaccia"""
        return {
            "initialized": self._initialized,
            "running": self._running,
            "url": f"http://{self._host}:{self._port}",
            "connected_clients": len(self._websocket_clients),
            "components_count": len(self._components),
            "current_theme": self._theme_name,
            "current_layout": self._current_layout
        }
    
    def get_interface_info(self) -> Dict[str, Any]:
        """Restituisce informazioni dettagliate sull'interfaccia"""
        return {
            **self.get_interface_status(),
            "available_themes": list(self._themes.keys()),
            "supported_events": list(self._event_handlers.keys()),
            "config": self.config
        }
    
    # Display management
    async def display_message(self, message: Dict[str, Any]) -> None:
        """Visualizza un messaggio"""
        try:
            await self._broadcast_to_clients({
                "type": "new_message",
                "message": message,
                "timestamp": time.time()
            })
            
            self.logger.debug(f"Messaggio visualizzato: {message.get('id', 'unknown')}")
            
        except Exception as e:
            self.logger.error(f"Errore visualizzazione messaggio: {e}")
            raise RenderingError(f"Visualizzazione messaggio fallita: {e}")
    
    async def display_peer_list(self, peers: List[Dict[str, Any]]) -> None:
        """Visualizza la lista dei peer"""
        try:
            await self._broadcast_to_clients({
                "type": "peer_list_update",
                "peers": peers,
                "timestamp": time.time()
            })
            
            self.logger.debug(f"Lista peer aggiornata: {len(peers)} peer")
            
        except Exception as e:
            self.logger.error(f"Errore visualizzazione peer: {e}")
            raise RenderingError(f"Visualizzazione peer fallita: {e}")
    
    async def display_connection_status(self, status: Dict[str, Any]) -> None:
        """Visualizza lo stato delle connessioni"""
        try:
            await self._broadcast_to_clients({
                "type": "connection_status",
                "status": status,
                "timestamp": time.time()
            })
            
            self.logger.debug("Stato connessioni aggiornato")
            
        except Exception as e:
            self.logger.error(f"Errore visualizzazione stato: {e}")
            raise RenderingError(f"Visualizzazione stato fallita: {e}")
    
    async def show_notification(self, message: str, notification_type: str = "info", 
                              duration: Optional[float] = None) -> None:
        """Mostra una notifica"""
        try:
            notification = {
                "id": str(uuid.uuid4()),
                "message": message,
                "type": notification_type,
                "duration": duration or 5.0,
                "timestamp": time.time()
            }
            
            await self._broadcast_to_clients({
                "type": "notification",
                "notification": notification
            })
            
            self.logger.debug(f"Notifica mostrata: {notification_type} - {message}")
            
        except Exception as e:
            self.logger.error(f"Errore notifica: {e}")
            raise RenderingError(f"Notifica fallita: {e}")
    
    async def clear_display(self, element_id: Optional[str] = None) -> None:
        """Pulisce il display"""
        try:
            await self._broadcast_to_clients({
                "type": "clear_display",
                "element_id": element_id,
                "timestamp": time.time()
            })
            
            self.logger.debug(f"Display pulito: {element_id or 'tutto'}")
            
        except Exception as e:
            self.logger.error(f"Errore pulizia display: {e}")
            raise RenderingError(f"Pulizia display fallita: {e}")
    
    # User input handling
    def set_input_handler(self, input_type: str, handler: Callable) -> None:
        """Imposta un handler per input utente"""
        self.set_event_handler(f"user_input_{input_type}", handler)
    
    async def get_user_input(self, prompt: str, input_type: str = "text") -> str:
        """Ottiene input dall'utente"""
        try:
            input_id = str(uuid.uuid4())
            
            # Invia richiesta input
            await self._broadcast_to_clients({
                "type": "input_request",
                "input_id": input_id,
                "prompt": prompt,
                "input_type": input_type,
                "timestamp": time.time()
            })
            
            # Simula attesa input (in implementazione reale aspetterebbe risposta WebSocket)
            await asyncio.sleep(1.0)
            
            # Simula input ricevuto
            return f"Input simulato per: {prompt}"
            
        except Exception as e:
            self.logger.error(f"Errore input utente: {e}")
            raise EventHandlingError(f"Input utente fallito: {e}")
    
    async def confirm_action(self, message: str) -> bool:
        """Richiede conferma per un'azione"""
        try:
            confirmation_id = str(uuid.uuid4())
            
            await self._broadcast_to_clients({
                "type": "confirmation_request",
                "confirmation_id": confirmation_id,
                "message": message,
                "timestamp": time.time()
            })
            
            # Simula conferma (in implementazione reale aspetterebbe risposta)
            await asyncio.sleep(0.5)
            return True  # Simula conferma positiva
            
        except Exception as e:
            self.logger.error(f"Errore conferma azione: {e}")
            raise EventHandlingError(f"Conferma azione fallita: {e}")
    
    # Component management
    def add_component(self, component_id: str, component_type: str, 
                     properties: Dict[str, Any]) -> None:
        """Aggiunge un componente"""
        try:
            component = WebComponent(
                id=component_id,
                type=component_type,
                properties=properties
            )
            
            self._components[component_id] = component
            self.logger.debug(f"Componente aggiunto: {component_id}")
            
        except Exception as e:
            self.logger.error(f"Errore aggiunta componente: {e}")
            raise ComponentError(f"Aggiunta componente fallita: {e}")
    
    def remove_component(self, component_id: str) -> None:
        """Rimuove un componente"""
        try:
            if component_id in self._components:
                del self._components[component_id]
                self.logger.debug(f"Componente rimosso: {component_id}")
            
        except Exception as e:
            self.logger.error(f"Errore rimozione componente: {e}")
            raise ComponentError(f"Rimozione componente fallita: {e}")
    
    def update_component(self, component_id: str, properties: Dict[str, Any]) -> None:
        """Aggiorna un componente"""
        try:
            if component_id in self._components:
                self._components[component_id].properties.update(properties)
                self.logger.debug(f"Componente aggiornato: {component_id}")
            
        except Exception as e:
            self.logger.error(f"Errore aggiornamento componente: {e}")
            raise ComponentError(f"Aggiornamento componente fallito: {e}")
    
    def get_component(self, component_id: str) -> Optional[Dict[str, Any]]:
        """Restituisce un componente"""
        if component_id in self._components:
            return self._components[component_id].to_dict()
        return None
    
    # Layout management
    def set_layout(self, layout_name: str, layout_config: Dict[str, Any]) -> None:
        """Imposta il layout"""
        try:
            self._current_layout = layout_name
            # In implementazione reale salverebbe la configurazione layout
            self.logger.info(f"Layout impostato: {layout_name}")
            
        except Exception as e:
            self.logger.error(f"Errore impostazione layout: {e}")
            raise LayoutError(f"Impostazione layout fallita: {e}")
    
    def get_current_layout(self) -> Dict[str, Any]:
        """Restituisce il layout corrente"""
        return {
            "name": self._current_layout,
            "components": list(self._components.keys())
        }
    
    async def refresh_layout(self) -> None:
        """Aggiorna il layout"""
        try:
            await self.render_interface()
            self.logger.debug("Layout aggiornato")
            
        except Exception as e:
            self.logger.error(f"Errore refresh layout: {e}")
            raise LayoutError(f"Refresh layout fallito: {e}")
    
    # Theme and styling
    def set_theme(self, theme_name: str) -> None:
        """Imposta il tema"""
        try:
            if theme_name in self._themes:
                self._theme_name = theme_name
                self.logger.info(f"Tema impostato: {theme_name}")
            else:
                raise ThemeError(f"Tema non trovato: {theme_name}")
            
        except Exception as e:
            self.logger.error(f"Errore impostazione tema: {e}")
            raise ThemeError(f"Impostazione tema fallita: {e}")
    
    def get_available_themes(self) -> List[str]:
        """Restituisce i temi disponibili"""
        return list(self._themes.keys())
    
    def customize_theme(self, theme_name: str, customizations: Dict[str, Any]) -> None:
        """Personalizza un tema"""
        try:
            if theme_name in self._themes:
                theme = self._themes[theme_name]
                
                if "colors" in customizations:
                    theme.colors.update(customizations["colors"])
                if "fonts" in customizations:
                    theme.fonts.update(customizations["fonts"])
                if "spacing" in customizations:
                    theme.spacing.update(customizations["spacing"])
                if "custom_css" in customizations:
                    theme.custom_css = customizations["custom_css"]
                
                self.logger.info(f"Tema personalizzato: {theme_name}")
            else:
                raise ThemeError(f"Tema non trovato: {theme_name}")
            
        except Exception as e:
            self.logger.error(f"Errore personalizzazione tema: {e}")
            raise ThemeError(f"Personalizzazione tema fallita: {e}")
    
    # File operations
    async def select_file(self, file_types: Optional[List[str]] = None) -> Optional[str]:
        """Apre dialog di selezione file"""
        try:
            # Simula selezione file (in implementazione reale userebbe dialog browser)
            await asyncio.sleep(0.5)
            return "/path/to/selected/file.txt"  # Simula file selezionato
            
        except Exception as e:
            self.logger.error(f"Errore selezione file: {e}")
            raise FileOperationError(f"Selezione file fallita: {e}")
    
    async def save_file_dialog(self, default_name: Optional[str] = None) -> Optional[str]:
        """Apre dialog di salvataggio file"""
        try:
            # Simula dialog salvataggio
            await asyncio.sleep(0.5)
            return f"/path/to/save/{default_name or 'file.txt'}"
            
        except Exception as e:
            self.logger.error(f"Errore dialog salvataggio: {e}")
            raise FileOperationError(f"Dialog salvataggio fallito: {e}")
    
    # Configuration
    def get_supported_features(self) -> List[str]:
        """Restituisce le funzionalità supportate"""
        return [
            "web_interface",
            "real_time_updates",
            "themes",
            "responsive_design",
            "file_dialogs",
            "notifications",
            "websocket_communication"
        ]
    
    def update_interface_config(self, config: Dict[str, Any]) -> None:
        """Aggiorna la configurazione dell'interfaccia"""
        self.config.update(config)
        
        # Aggiorna parametri configurabili
        self._host = self.config.get("host", self._host)
        self._port = self.config.get("port", self._port)
        self._auto_open = self.config.get("auto_open", self._auto_open)
        
        if "theme" in config and config["theme"] in self._themes:
            self._theme_name = config["theme"]
        
        self.logger.info("Configurazione interfaccia aggiornata")
    
    def export_interface_state(self) -> Dict[str, Any]:
        """Esporta lo stato dell'interfaccia"""
        return {
            "components": {
                comp_id: comp.to_dict() 
                for comp_id, comp in self._components.items()
            },
            "current_layout": self._current_layout,
            "current_theme": self._theme_name,
            "config": self.config
        }
    
    def import_interface_state(self, state: Dict[str, Any]) -> None:
        """Importa lo stato dell'interfaccia"""
        try:
            if "components" in state:
                self._components = {
                    comp_id: WebComponent(**comp_data)
                    for comp_id, comp_data in state["components"].items()
                }
            
            if "current_layout" in state:
                self._current_layout = state["current_layout"]
            
            if "current_theme" in state and state["current_theme"] in self._themes:
                self._theme_name = state["current_theme"]
            
            if "config" in state:
                self.update_interface_config(state["config"])
            
            self.logger.info("Stato interfaccia importato")
            
        except Exception as e:
            self.logger.error(f"Errore importazione stato: {e}")
            raise InterfaceError(f"Importazione stato fallita: {e}")
    
    # Metodi privati
    def _init_default_themes(self) -> None:
        """Inizializza i temi di default"""
        # Tema default
        default_theme = WebTheme(
            name="default",
            colors={
                "primary": "#007bff",
                "secondary": "#6c757d",
                "success": "#28a745",
                "danger": "#dc3545",
                "warning": "#ffc107",
                "info": "#17a2b8",
                "light": "#f8f9fa",
                "dark": "#343a40",
                "background": "#ffffff",
                "text": "#212529"
            },
            fonts={
                "primary": "system-ui, -apple-system, sans-serif",
                "monospace": "SFMono-Regular, Consolas, monospace"
            },
            spacing={
                "xs": "0.25rem",
                "sm": "0.5rem",
                "md": "1rem",
                "lg": "1.5rem",
                "xl": "3rem"
            }
        )
        
        # Tema scuro
        dark_theme = WebTheme(
            name="dark",
            colors={
                "primary": "#0d6efd",
                "secondary": "#6c757d",
                "success": "#198754",
                "danger": "#dc3545",
                "warning": "#fd7e14",
                "info": "#0dcaf0",
                "light": "#495057",
                "dark": "#212529",
                "background": "#121212",
                "text": "#ffffff"
            },
            fonts={
                "primary": "system-ui, -apple-system, sans-serif",
                "monospace": "SFMono-Regular, Consolas, monospace"
            },
            spacing={
                "xs": "0.25rem",
                "sm": "0.5rem",
                "md": "1rem",
                "lg": "1.5rem",
                "xl": "3rem"
            }
        )
        
        self._themes["default"] = default_theme
        self._themes["dark"] = dark_theme
    
    def _init_default_components(self) -> None:
        """Inizializza i componenti di default"""
        # Header
        self.add_component("header", "header", {
            "title": "LaboonChat v2.0",
            "subtitle": "Secure P2P Messaging"
        })
        
        # Chat area
        self.add_component("chat_area", "chat", {
            "messages": [],
            "auto_scroll": True
        })
        
        # Peer list
        self.add_component("peer_list", "list", {
            "title": "Connected Peers",
            "items": []
        })
        
        # Input area
        self.add_component("message_input", "input", {
            "placeholder": "Type your message...",
            "type": "text",
            "multiline": True
        })
        
        # Status bar
        self.add_component("status_bar", "status", {
            "connection_status": "disconnected",
            "peer_count": 0
        })
    
    async def _start_web_server(self) -> None:
        """Avvia il server web"""
        try:
            # Simula avvio server web (in implementazione reale userebbe aiohttp/fastapi)
            self._web_server = {
                "host": self._host,
                "port": self._port,
                "status": "running"
            }
            
            self.logger.info(f"Server web avviato su {self._host}:{self._port}")
            
        except Exception as e:
            self.logger.error(f"Errore avvio server web: {e}")
            raise
    
    async def _stop_web_server(self) -> None:
        """Ferma il server web"""
        if self._web_server:
            self._web_server["status"] = "stopped"
            self._web_server = None
            self.logger.info("Server web fermato")
    
    async def _open_browser(self) -> None:
        """Apre il browser"""
        try:
            url = f"http://{self._host}:{self._port}"
            webbrowser.open(url)
            self.logger.info(f"Browser aperto su: {url}")
            
        except Exception as e:
            self.logger.warning(f"Impossibile aprire browser: {e}")
    
    async def _create_static_files(self) -> None:
        """Crea i file statici necessari"""
        try:
            # Crea HTML principale
            html_content = self._generate_main_html()
            with open(self._templates_dir / "index.html", 'w') as f:
                f.write(html_content)
            
            # Crea CSS
            css_content = self._generate_main_css()
            with open(self._static_dir / "style.css", 'w') as f:
                f.write(css_content)
            
            # Crea JavaScript
            js_content = self._generate_main_js()
            with open(self._static_dir / "app.js", 'w') as f:
                f.write(js_content)
            
            self.logger.info("File statici creati")
            
        except Exception as e:
            self.logger.error(f"Errore creazione file statici: {e}")
            raise
    
    def _generate_main_html(self) -> str:
        """Genera l'HTML principale"""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LaboonChat v2.0</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <div id="app">
        <header id="header">
            <h1>LaboonChat v2.0</h1>
            <p>Secure P2P Messaging</p>
        </header>
        
        <main class="main-content">
            <div class="chat-container">
                <div id="chat_area" class="chat-area">
                    <div class="messages" id="messages"></div>
                </div>
                
                <div class="input-area">
                    <textarea id="message_input" placeholder="Type your message..." rows="3"></textarea>
                    <button id="send_button">Send</button>
                </div>
            </div>
            
            <aside class="sidebar">
                <div id="peer_list" class="peer-list">
                    <h3>Connected Peers</h3>
                    <ul id="peers"></ul>
                </div>
                
                <div class="controls">
                    <button id="connect_button">Connect to Peer</button>
                    <button id="discover_button">Discover Peers</button>
                    <button id="theme_button">Toggle Theme</button>
                </div>
            </aside>
        </main>
        
        <footer id="status_bar" class="status-bar">
            <span id="connection_status">Disconnected</span>
            <span id="peer_count">0 peers</span>
        </footer>
    </div>
    
    <div id="notifications" class="notifications"></div>
    
    <script src="/static/app.js"></script>
</body>
</html>'''
    
    def _generate_main_css(self) -> str:
        """Genera il CSS principale"""
        theme = self._themes[self._theme_name]
        return f'''
/* LaboonChat v2.0 Styles */
* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

body {{
    font-family: {theme.fonts["primary"]};
    background-color: {theme.colors["background"]};
    color: {theme.colors["text"]};
    height: 100vh;
    display: flex;
    flex-direction: column;
}}

#app {{
    display: flex;
    flex-direction: column;
    height: 100vh;
}}

header {{
    background-color: {theme.colors["primary"]};
    color: white;
    padding: {theme.spacing["md"]};
    text-align: center;
}}

.main-content {{
    display: flex;
    flex: 1;
    overflow: hidden;
}}

.chat-container {{
    flex: 1;
    display: flex;
    flex-direction: column;
    padding: {theme.spacing["md"]};
}}

.chat-area {{
    flex: 1;
    border: 1px solid {theme.colors["light"]};
    border-radius: 8px;
    overflow-y: auto;
    padding: {theme.spacing["md"]};
    margin-bottom: {theme.spacing["md"]};
}}

.messages {{
    display: flex;
    flex-direction: column;
    gap: {theme.spacing["sm"]};
}}

.message {{
    padding: {theme.spacing["sm"]};
    border-radius: 8px;
    max-width: 70%;
}}

.message.sent {{
    background-color: {theme.colors["primary"]};
    color: white;
    align-self: flex-end;
}}

.message.received {{
    background-color: {theme.colors["light"]};
    align-self: flex-start;
}}

.input-area {{
    display: flex;
    gap: {theme.spacing["sm"]};
}}

#message_input {{
    flex: 1;
    padding: {theme.spacing["sm"]};
    border: 1px solid {theme.colors["light"]};
    border-radius: 4px;
    resize: vertical;
    font-family: inherit;
}}

button {{
    padding: {theme.spacing["sm"]} {theme.spacing["md"]};
    background-color: {theme.colors["primary"]};
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-family: inherit;
}}

button:hover {{
    opacity: 0.9;
}}

.sidebar {{
    width: 300px;
    background-color: {theme.colors["light"]};
    padding: {theme.spacing["md"]};
    display: flex;
    flex-direction: column;
    gap: {theme.spacing["md"]};
}}

.peer-list {{
    flex: 1;
}}

.peer-list ul {{
    list-style: none;
    margin-top: {theme.spacing["sm"]};
}}

.peer-list li {{
    padding: {theme.spacing["sm"]};
    border-bottom: 1px solid {theme.colors["background"]};
}}

.controls {{
    display: flex;
    flex-direction: column;
    gap: {theme.spacing["sm"]};
}}

.status-bar {{
    background-color: {theme.colors["dark"]};
    color: white;
    padding: {theme.spacing["sm"]} {theme.spacing["md"]};
    display: flex;
    justify-content: space-between;
}}

.notifications {{
    position: fixed;
    top: {theme.spacing["md"]};
    right: {theme.spacing["md"]};
    z-index: 1000;
}}

.notification {{
    background-color: {theme.colors["info"]};
    color: white;
    padding: {theme.spacing["md"]};
    border-radius: 4px;
    margin-bottom: {theme.spacing["sm"]};
    animation: slideIn 0.3s ease-out;
}}

.notification.success {{
    background-color: {theme.colors["success"]};
}}

.notification.error {{
    background-color: {theme.colors["danger"]};
}}

.notification.warning {{
    background-color: {theme.colors["warning"]};
}}

@keyframes slideIn {{
    from {{
        transform: translateX(100%);
        opacity: 0;
    }}
    to {{
        transform: translateX(0);
        opacity: 1;
    }}
}}

@media (max-width: 768px) {{
    .main-content {{
        flex-direction: column;
    }}
    
    .sidebar {{
        width: 100%;
        order: -1;
    }}
}}
'''
    
    def _generate_main_js(self) -> str:
        """Genera il JavaScript principale"""
        return '''
// LaboonChat v2.0 Client
class LaboonChatClient {
    constructor() {
        this.ws = null;
        this.currentTheme = 'default';
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.connectWebSocket();
    }
    
    setupEventListeners() {
        const sendButton = document.getElementById('send_button');
        const messageInput = document.getElementById('message_input');
        const connectButton = document.getElementById('connect_button');
        const discoverButton = document.getElementById('discover_button');
        const themeButton = document.getElementById('theme_button');
        
        sendButton.addEventListener('click', () => this.sendMessage());
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        connectButton.addEventListener('click', () => this.connectToPeer());
        discoverButton.addEventListener('click', () => this.discoverPeers());
        themeButton.addEventListener('click', () => this.toggleTheme());
    }
    
    connectWebSocket() {
        // Simula connessione WebSocket
        console.log('WebSocket connected (simulated)');
        this.updateConnectionStatus('Connected');
        
        // Simula messaggi periodici
        setInterval(() => {
            if (Math.random() < 0.1) {
                this.receiveMessage({
                    id: Date.now(),
                    sender_id: 'peer_1',
                    content: 'Hello from peer!',
                    timestamp: Date.now() / 1000
                });
            }
        }, 5000);
    }
    
    sendMessage() {
        const input = document.getElementById('message_input');
        const content = input.value.trim();
        
        if (!content) return;
        
        const message = {
            id: Date.now(),
            sender_id: 'self',
            content: content,
            timestamp: Date.now() / 1000
        };
        
        this.displayMessage(message, true);
        input.value = '';
        
        // Simula invio via WebSocket
        console.log('Message sent:', message);
    }
    
    receiveMessage(message) {
        this.displayMessage(message, false);
        this.showNotification(`New message from ${message.sender_id}`, 'info');
    }
    
    displayMessage(message, sent) {
        const messagesContainer = document.getElementById('messages');
        const messageElement = document.createElement('div');
        messageElement.className = `message ${sent ? 'sent' : 'received'}`;
        
        const time = new Date(message.timestamp * 1000).toLocaleTimeString();
        messageElement.innerHTML = `
            <div class="message-content">${message.content}</div>
            <div class="message-time">${time}</div>
        `;
        
        messagesContainer.appendChild(messageElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    connectToPeer() {
        const address = prompt('Enter peer address:', 'localhost:8889');
        if (address) {
            this.showNotification(`Connecting to ${address}...`, 'info');
            
            // Simula connessione
            setTimeout(() => {
                this.addPeer({
                    peer_id: `peer_${Date.now()}`,
                    address: address,
                    status: 'online'
                });
                this.showNotification(`Connected to ${address}`, 'success');
            }, 1000);
        }
    }
    
    discoverPeers() {
        this.showNotification('Discovering peers...', 'info');
        
        // Simula scoperta
        setTimeout(() => {
            const peers = [
                { peer_id: 'peer_1', address: '192.168.1.100:8888', status: 'online' },
                { peer_id: 'peer_2', address: '192.168.1.101:8888', status: 'online' }
            ];
            
            peers.forEach(peer => this.addPeer(peer));
            this.showNotification(`Found ${peers.length} peers`, 'success');
        }, 1500);
    }
    
    addPeer(peer) {
        const peersList = document.getElementById('peers');
        const peerElement = document.createElement('li');
        peerElement.innerHTML = `
            <strong>${peer.peer_id}</strong><br>
            <small>${peer.address}</small>
            <span class="status ${peer.status}">${peer.status}</span>
        `;
        
        peersList.appendChild(peerElement);
        this.updatePeerCount();
    }
    
    updatePeerCount() {
        const peerCount = document.getElementById('peers').children.length;
        document.getElementById('peer_count').textContent = `${peerCount} peers`;
    }
    
    updateConnectionStatus(status) {
        document.getElementById('connection_status').textContent = status;
    }
    
    toggleTheme() {
        this.currentTheme = this.currentTheme === 'default' ? 'dark' : 'default';
        document.body.className = `theme-${this.currentTheme}`;
        this.showNotification(`Theme changed to ${this.currentTheme}`, 'info');
    }
    
    showNotification(message, type = 'info') {
        const container = document.getElementById('notifications');
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        container.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
}

// Inizializza l'applicazione
document.addEventListener('DOMContentLoaded', () => {
    new LaboonChatClient();
});
'''
    
    async def _broadcast_to_clients(self, message: Dict[str, Any]) -> None:
        """Invia un messaggio a tutti i client WebSocket connessi"""
        # In implementazione reale invierebbe via WebSocket
        self.logger.debug(f"Broadcast simulato: {message['type']}")
    
    async def _close_websocket_connections(self) -> None:
        """Chiude tutte le connessioni WebSocket"""
        self._websocket_clients.clear()
        self.logger.info("Connessioni WebSocket chiuse")


def create_web_interface(config: Optional[Dict[str, Any]] = None) -> WebInterface:
    """
    Factory function per creare un'istanza di WebInterface.
    
    Args:
        config: Configurazione opzionale per il modulo
        
    Returns:
        Istanza di WebInterface configurata
    """
    return WebInterface(config)


# Configurazione di default per il modulo
DEFAULT_CONFIG = {
    "host": "localhost",
    "port": 8080,
    "auto_open": True,
    "theme": "default",
    "static_dir": "static",
    "templates_dir": "templates"
}