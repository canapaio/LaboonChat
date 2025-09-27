"""
Integrazione Sistema Configurazioni con LaboonChat
Connette il sistema di configurazioni dinamiche con l'architettura esistente.

Fornisce API unificate per gestire configurazioni plugin e interfacce web.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import threading
from datetime import datetime

try:
    from .plugin_config_system import PluginConfigManager
    from .config_ui_generator import ConfigUIGenerator
except ImportError:
    from plugin_config_system import PluginConfigManager
    from config_ui_generator import ConfigUIGenerator

logger = logging.getLogger(__name__)

class LaboonConfigIntegration:
    """Integrazione principale del sistema configurazioni con LaboonChat."""
    
    def __init__(self, core_instance=None):
        self.core = core_instance
        self.config_manager = PluginConfigManager()
        self.ui_generator = ConfigUIGenerator(self.config_manager)
        self.web_server_port = 8081
        self.web_server_thread = None
        self.is_web_server_running = False
        
        # Directory per configurazioni
        self.config_root = Path("plugin_configs")
        self.config_root.mkdir(exist_ok=True)
        
        # Cache configurazioni attive
        self._active_configs = {}
        self._config_lock = threading.RLock()
        
        # Inizializza sistema
        self._initialize_system()
        
    def _initialize_system(self) -> None:
        """Inizializza il sistema di configurazioni."""
        try:
            # Carica configurazioni esistenti
            self._load_existing_configs()
            
            # Registra plugin di default se non esistenti
            self._register_default_plugins()
            
            logger.info("Sistema configurazioni inizializzato con successo")
            
        except Exception as e:
            logger.error(f"Errore nell'inizializzazione sistema configurazioni: {e}")
            
    def _load_existing_configs(self) -> None:
        """Carica le configurazioni esistenti."""
        with self._config_lock:
            for plugin_id in self.config_manager.list_plugins():
                try:
                    config = self.config_manager.load_plugin_config(plugin_id)
                    self._active_configs[plugin_id] = config
                    logger.debug(f"Configurazione caricata per plugin: {plugin_id}")
                except Exception as e:
                    logger.warning(f"Errore nel caricamento configurazione {plugin_id}: {e}")
                    
    def _register_default_plugins(self) -> None:
        """Registra plugin di default per dimostrare il sistema."""
        
        # Plugin Chat Settings
        if not self.config_manager.has_plugin("chat_settings"):
            try:
                from .plugin_config_system import PluginConfigSchema, ConfigField, ConfigFieldType
            except ImportError:
                from plugin_config_system import PluginConfigSchema, ConfigField, ConfigFieldType
            
            chat_schema = PluginConfigSchema(
                plugin_id="chat_settings",
                plugin_name="Impostazioni Chat",
                description="Configurazioni generali per la chat",
                version="1.0.0"
            )
            
            # Campi di configurazione
            chat_schema.add_field(ConfigField(
                name="max_message_length",
                field_type=ConfigFieldType.INTEGER,
                title="Lunghezza Massima Messaggio",
                description="Numero massimo di caratteri per messaggio",
                default=1000,
                min_value=100,
                max_value=5000,
                required=True
            ))
            
            chat_schema.add_field(ConfigField(
                name="enable_emoji",
                field_type=ConfigFieldType.BOOLEAN,
                title="Abilita Emoji",
                description="Permetti l'uso di emoji nei messaggi",
                default=True
            ))
            
            chat_schema.add_field(ConfigField(
                name="theme_color",
                field_type=ConfigFieldType.STRING,
                title="Colore Tema",
                description="Colore principale dell'interfaccia",
                default="#007bff",
                ui_widget="color"
            ))
            
            chat_schema.add_field(ConfigField(
                name="notification_sound",
                field_type=ConfigFieldType.ENUM,
                title="Suono Notifica",
                description="Suono per le notifiche",
                default="default",
                enum_values=["default", "bell", "chime", "none"]
            ))
            
            self.config_manager.register_plugin_schema(chat_schema)
            
        # Plugin Security Settings
        if not self.config_manager.has_plugin("security_settings"):
            security_schema = PluginConfigSchema(
                plugin_id="security_settings",
                plugin_name="Impostazioni Sicurezza",
                description="Configurazioni di sicurezza e privacy",
                version="1.0.0"
            )
            
            security_schema.add_field(ConfigField(
                name="auto_logout_minutes",
                field_type=ConfigFieldType.INTEGER,
                title="Logout Automatico (minuti)",
                description="Tempo di inattività prima del logout automatico",
                default=30,
                min_value=5,
                max_value=480
            ))
            
            security_schema.add_field(ConfigField(
                name="require_password",
                field_type=ConfigFieldType.BOOLEAN,
                title="Richiedi Password",
                description="Richiedi password per accedere alla chat",
                default=False
            ))
            
            security_schema.add_field(ConfigField(
                name="allowed_file_types",
                field_type=ConfigFieldType.ARRAY,
                title="Tipi File Consentiti",
                description="Estensioni file permesse per upload",
                default=["jpg", "png", "gif", "pdf", "txt"]
            ))
            
            security_schema.add_field(ConfigField(
                name="encryption_level",
                field_type=ConfigFieldType.ENUM,
                title="Livello Crittografia",
                description="Livello di crittografia per i messaggi",
                default="standard",
                enum_values=["none", "basic", "standard", "high"]
            ))
            
            self.config_manager.register_plugin_schema(security_schema)
            
        # Plugin Minor Protection Settings
        if not self.config_manager.has_plugin("minor_protection"):
            minor_protection_schema = PluginConfigSchema(
                plugin_id="minor_protection",
                plugin_name="Protezione Minori",
                description="Sistema semplificato di protezione minori con notifiche email periodiche",
                version="1.0.0"
            )
            
            minor_protection_schema.add_field(ConfigField(
                name="is_minor",
                field_type=ConfigFieldType.BOOLEAN,
                title="Sono minorenne",
                description="Indica se l'utente è minorenne (da configurare durante la creazione dell'identità)",
                default=False
            ))
            
            minor_protection_schema.add_field(ConfigField(
                name="enabled",
                field_type=ConfigFieldType.BOOLEAN,
                title="Abilita Protezione Minori",
                description="Attiva il sistema di notifiche email periodiche",
                default=False
            ))
            
            minor_protection_schema.add_field(ConfigField(
                name="interval_minutes",
                field_type=ConfigFieldType.INTEGER,
                title="Intervallo Notifiche (minuti)",
                description="Frequenza di invio delle email di riepilogo",
                default=60,
                min_value=15,
                max_value=1440  # 24 ore
            ))
            
            minor_protection_schema.add_field(ConfigField(
                name="parent_email",
                field_type=ConfigFieldType.STRING,
                title="Email Genitore/Tutore",
                description="Indirizzo email per ricevere i riepiloghi di utilizzo",
                default="",
                required=False
            ))
            
            minor_protection_schema.add_field(ConfigField(
                name="user_name",
                field_type=ConfigFieldType.STRING,
                title="Nome Utente",
                description="Nome da includere nelle notifiche email",
                default="",
                required=False
            ))
            
            minor_protection_schema.add_field(ConfigField(
                name="smtp_server",
                field_type=ConfigFieldType.STRING,
                title="Server SMTP",
                description="Server email per l'invio delle notifiche",
                default="localhost"
            ))
            
            minor_protection_schema.add_field(ConfigField(
                name="smtp_port",
                field_type=ConfigFieldType.INTEGER,
                title="Porta SMTP",
                description="Porta del server SMTP",
                default=587,
                min_value=1,
                max_value=65535
            ))
            
            minor_protection_schema.add_field(ConfigField(
                name="smtp_username",
                field_type=ConfigFieldType.STRING,
                title="Username SMTP",
                description="Nome utente per autenticazione SMTP (opzionale)",
                default="",
                required=False
            ))
            
            minor_protection_schema.add_field(ConfigField(
                name="smtp_password",
                field_type=ConfigFieldType.STRING,
                title="Password SMTP",
                description="Password per autenticazione SMTP (opzionale)",
                default="",
                required=False,
                ui_widget="password"
            ))
            
            self.config_manager.register_plugin_schema(minor_protection_schema)
    def register_plugin_config(self, schema: 'PluginConfigSchema') -> bool:
        """Registra la configurazione di un plugin."""
        try:
            success = self.config_manager.register_plugin_schema(schema)
            if success:
                # Carica configurazione di default
                config = self.config_manager.load_plugin_config(schema.plugin_id)
                with self._config_lock:
                    self._active_configs[schema.plugin_id] = config
                    
                # Genera UI
                self.ui_generator.generate_plugin_ui(schema.plugin_id)
                
                logger.info(f"Plugin {schema.plugin_id} registrato con successo")
                
            return success
            
        except Exception as e:
            logger.error(f"Errore nella registrazione plugin {schema.plugin_id}: {e}")
            return False
            
    def get_plugin_config(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Ottieni la configurazione corrente di un plugin."""
        with self._config_lock:
            return self._active_configs.get(plugin_id)
            
    def update_plugin_config(self, plugin_id: str, config: Dict[str, Any]) -> bool:
        """Aggiorna la configurazione di un plugin."""
        try:
            # Valida configurazione
            if not self.config_manager.validate_plugin_config(plugin_id, config):
                logger.error(f"Configurazione non valida per plugin {plugin_id}")
                return False
                
            # Salva configurazione
            success = self.config_manager.save_plugin_config(plugin_id, config)
            if success:
                with self._config_lock:
                    self._active_configs[plugin_id] = config
                    
                # Notifica il core se disponibile
                if self.core and hasattr(self.core, 'on_plugin_config_changed'):
                    self.core.on_plugin_config_changed(plugin_id, config)
                    
                logger.info(f"Configurazione aggiornata per plugin {plugin_id}")
                
            return success
            
        except Exception as e:
            logger.error(f"Errore nell'aggiornamento configurazione {plugin_id}: {e}")
            return False
            
    def get_all_plugin_configs(self) -> Dict[str, Dict[str, Any]]:
        """Ottieni tutte le configurazioni plugin."""
        with self._config_lock:
            return self._active_configs.copy()
            
    def generate_config_ui(self, plugin_id: str = None) -> Optional[str]:
        """Genera l'interfaccia di configurazione."""
        try:
            if plugin_id:
                return self.ui_generator.generate_plugin_ui(plugin_id)
            else:
                # Genera menu principale
                return self.ui_generator.generate_plugin_menu()
                
        except Exception as e:
            logger.error(f"Errore nella generazione UI: {e}")
            return None
            
    def start_config_web_server(self, port: int = None) -> bool:
        """Avvia server web per interfacce di configurazione."""
        if self.is_web_server_running:
            logger.warning("Server web già in esecuzione")
            return True
            
        if port:
            self.web_server_port = port
            
        try:
            import http.server
            import socketserver
            import threading
            
            # Cambia directory di lavoro per servire file UI
            ui_dir = self.ui_generator.output_dir
            
            def run_server():
                os.chdir(ui_dir)
                handler = http.server.SimpleHTTPRequestHandler
                with socketserver.TCPServer(("", self.web_server_port), handler) as httpd:
                    logger.info(f"Server configurazioni avviato su porta {self.web_server_port}")
                    logger.info(f"Accedi a: http://localhost:{self.web_server_port}/plugin_menu.html")
                    self.is_web_server_running = True
                    httpd.serve_forever()
                    
            self.web_server_thread = threading.Thread(target=run_server, daemon=True)
            self.web_server_thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"Errore nell'avvio server web: {e}")
            return False
            
    def stop_config_web_server(self) -> None:
        """Ferma il server web."""
        self.is_web_server_running = False
        if self.web_server_thread:
            # Il thread daemon si fermerà automaticamente
            self.web_server_thread = None
            logger.info("Server web configurazioni fermato")
            
    def export_all_configs(self, export_path: str = None) -> Optional[str]:
        """Esporta tutte le configurazioni in un file."""
        try:
            if not export_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                export_path = f"laboon_configs_export_{timestamp}.json"
                
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "laboon_version": "1.0.0",
                "configs": self.get_all_plugin_configs()
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Configurazioni esportate in: {export_path}")
            return export_path
            
        except Exception as e:
            logger.error(f"Errore nell'esportazione configurazioni: {e}")
            return None
            
    def import_configs(self, import_path: str) -> bool:
        """Importa configurazioni da file."""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
                
            configs = import_data.get('configs', {})
            success_count = 0
            
            for plugin_id, config in configs.items():
                if self.update_plugin_config(plugin_id, config):
                    success_count += 1
                    
            logger.info(f"Importate {success_count}/{len(configs)} configurazioni")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Errore nell'importazione configurazioni: {e}")
            return False
            
    def get_system_status(self) -> Dict[str, Any]:
        """Ottieni lo stato del sistema configurazioni."""
        return {
            "initialized": True,
            "plugins_registered": len(self._active_configs),
            "web_server_running": self.is_web_server_running,
            "web_server_port": self.web_server_port if self.is_web_server_running else None,
            "config_directory": str(self.config_root),
            "ui_directory": str(self.ui_generator.output_dir)
        }
        
    def refresh_all_uis(self) -> List[str]:
        """Rigenera tutte le interfacce UI."""
        try:
            generated_files = self.ui_generator.generate_all_plugin_uis()
            menu_file = self.ui_generator.generate_plugin_menu()
            if menu_file:
                generated_files.append(menu_file)
                
            logger.info(f"Rigenerate {len(generated_files)} interfacce UI")
            return generated_files
            
        except Exception as e:
            logger.error(f"Errore nella rigenerazione UI: {e}")
            return []

# Istanza globale per integrazione facile
_global_config_integration = None

def get_config_integration(core_instance=None) -> LaboonConfigIntegration:
    """Ottieni l'istanza globale del sistema configurazioni."""
    global _global_config_integration
    
    if _global_config_integration is None:
        _global_config_integration = LaboonConfigIntegration(core_instance)
        
    return _global_config_integration

def initialize_config_system(core_instance=None) -> LaboonConfigIntegration:
    """Inizializza il sistema configurazioni."""
    integration = get_config_integration(core_instance)
    
    # Genera UI iniziali
    integration.refresh_all_uis()
    
    return integration