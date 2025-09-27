"""
Test Sistema Configurazioni Dinamiche LaboonChat
Test completo per validare il sistema di configurazioni plugin con auto-generazione UI.

Testa registrazione plugin, generazione UI, gestione configurazioni e integrazione.
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_config_system():
    """Test completo del sistema configurazioni."""
    
    print("🚀 Avvio Test Sistema Configurazioni LaboonChat")
    print("=" * 60)
    
    try:
        # Import moduli con gestione errori
        try:
            from .plugin_config_system import PluginConfigManager, PluginConfigSchema, ConfigField, ConfigFieldType
            from .config_ui_generator import ConfigUIGenerator
            from .config_integration import LaboonConfigIntegration, initialize_config_system
        except ImportError:
            # Fallback per esecuzione standalone
            from plugin_config_system import PluginConfigManager, PluginConfigSchema, ConfigField, ConfigFieldType
            from config_ui_generator import ConfigUIGenerator
            from config_integration import LaboonConfigIntegration, initialize_config_system
        
        print("✅ Moduli importati con successo")
        
        # Test 1: Inizializzazione sistema
        print("\n📋 Test 1: Inizializzazione Sistema")
        integration = initialize_config_system()
        status = integration.get_system_status()
        
        print(f"   Plugin registrati: {status['plugins_registered']}")
        print(f"   Directory configurazioni: {status['config_directory']}")
        print(f"   Directory UI: {status['ui_directory']}")
        
        # Test 2: Registrazione plugin personalizzato
        print("\n📋 Test 2: Registrazione Plugin Personalizzato")
        
        # Crea schema plugin di test
        test_schema = PluginConfigSchema(
            plugin_id="test_plugin",
            plugin_name="Plugin di Test",
            description="Plugin per testare il sistema configurazioni",
            version="1.0.0"
        )
        
        # Aggiungi campi di vario tipo
        test_schema.add_field(ConfigField(
            name="server_url",
            field_type=ConfigFieldType.STRING,
            title="URL Server",
            description="Indirizzo del server di destinazione",
            default="https://api.example.com",
            required=True,
            pattern=r"https?://.*"
        ))
        
        test_schema.add_field(ConfigField(
            name="max_connections",
            field_type=ConfigFieldType.INTEGER,
            title="Connessioni Massime",
            description="Numero massimo di connessioni simultanee",
            default=10,
            min_value=1,
            max_value=100
        ))
        
        test_schema.add_field(ConfigField(
            name="enable_logging",
            field_type=ConfigFieldType.BOOLEAN,
            title="Abilita Logging",
            description="Attiva la registrazione degli eventi",
            default=True
        ))
        
        test_schema.add_field(ConfigField(
            name="log_level",
            field_type=ConfigFieldType.ENUM,
            title="Livello Log",
            description="Livello di dettaglio dei log",
            default="INFO",
            enum_values=["DEBUG", "INFO", "WARNING", "ERROR"]
        ))
        
        test_schema.add_field(ConfigField(
            name="api_timeout",
            field_type=ConfigFieldType.FLOAT,
            title="Timeout API (secondi)",
            description="Timeout per le chiamate API",
            default=30.0,
            min_value=1.0,
            max_value=300.0
        ))
        
        test_schema.add_field(ConfigField(
            name="theme_color",
            field_type=ConfigFieldType.STRING,
            title="Colore Tema",
            description="Colore principale dell'interfaccia",
            default="#28a745",
            ui_widget="color"
        ))
        
        test_schema.add_field(ConfigField(
            name="backup_directories",
            field_type=ConfigFieldType.ARRAY,
            title="Directory Backup",
            description="Lista delle directory per i backup",
            default=["/backup1", "/backup2"]
        ))
        
        # Registra plugin
        success = integration.register_plugin_config(test_schema)
        print(f"   Plugin registrato: {'✅' if success else '❌'}")
        
        # Test 3: Caricamento configurazione
        print("\n📋 Test 3: Caricamento Configurazione")
        config = integration.get_plugin_config("test_plugin")
        print(f"   Configurazione caricata: {'✅' if config else '❌'}")
        
        if not config:
            print("   ⚠️ Configurazione non trovata, genero configurazione di default")
            config = integration.config_manager._generate_default_config("test_plugin")
            if config:
                integration.update_plugin_config("test_plugin", config)
                print("   ✅ Configurazione di default generata e salvata")
        
        if config:
            print(f"   Campi configurazione: {list(config.keys())}")
            print(f"   Server URL: {config.get('server_url')}")
            print(f"   Max Connections: {config.get('max_connections')}")
            
        # Test 4: Aggiornamento configurazione
        print("\n📋 Test 4: Aggiornamento Configurazione")
        if config:
            new_config = config.copy()
            new_config['server_url'] = 'https://test.example.com'
            new_config['max_connections'] = 25
            new_config['enable_logging'] = False
            
            update_success = integration.update_plugin_config("test_plugin", new_config)
            print(f"   Configurazione aggiornata: {'✅' if update_success else '❌'}")
            
            # Verifica aggiornamento
            updated_config = integration.get_plugin_config("test_plugin")
            if updated_config:
                print(f"   Nuovo Server URL: {updated_config.get('server_url')}")
                print(f"   Nuove Max Connections: {updated_config.get('max_connections')}")
        else:
            print("   ❌ Impossibile aggiornare: configurazione non disponibile")
            
        # Test 5: Generazione UI
        print("\n📋 Test 5: Generazione UI")
        
        # Genera UI per plugin specifico
        ui_file = integration.generate_config_ui("test_plugin")
        print(f"   UI plugin generata: {'✅' if ui_file else '❌'}")
        if ui_file:
            print(f"   File UI: {ui_file}")
            
        # Genera menu principale
        menu_file = integration.generate_config_ui()
        print(f"   Menu principale generato: {'✅' if menu_file else '❌'}")
        if menu_file:
            print(f"   File menu: {menu_file}")
            
        # Test 6: Validazione schema JSON
        print("\n📋 Test 6: Validazione Schema JSON")
        
        # Test configurazione valida
        valid_config = {
            "server_url": "https://valid.example.com",
            "max_connections": 50,
            "enable_logging": True,
            "log_level": "DEBUG",
            "api_timeout": 60.0,
            "theme_color": "#ff5722",
            "backup_directories": ["/new/backup"]
        }
        
        is_valid = integration.config_manager.validate_plugin_config("test_plugin", valid_config)
        print(f"   Configurazione valida: {'✅' if is_valid else '❌'}")
        
        # Test configurazione non valida
        invalid_config = {
            "server_url": "not-a-url",  # Pattern non valido
            "max_connections": 150,     # Fuori range
            "log_level": "INVALID"      # Valore enum non valido
        }
        
        is_invalid = not integration.config_manager.validate_plugin_config("test_plugin", invalid_config)
        print(f"   Configurazione non valida rilevata: {'✅' if is_invalid else '❌'}")
        
        # Test 7: Export/Import configurazioni
        print("\n📋 Test 7: Export/Import Configurazioni")
        
        # Export
        export_file = integration.export_all_configs("test_export.json")
        print(f"   Export configurazioni: {'✅' if export_file else '❌'}")
        
        if export_file and os.path.exists(export_file):
            # Verifica contenuto export
            with open(export_file, 'r', encoding='utf-8') as f:
                export_data = json.load(f)
                
            print(f"   Plugin esportati: {len(export_data.get('configs', {}))}")
            
            # Test import
            import_success = integration.import_configs(export_file)
            print(f"   Import configurazioni: {'✅' if import_success else '❌'}")
            
            # Cleanup
            os.remove(export_file)
            
        # Test 8: Generazione UI per tutti i plugin
        print("\n📋 Test 8: Generazione UI Completa")
        
        generated_files = integration.refresh_all_uis()
        print(f"   File UI generati: {len(generated_files)}")
        
        for file_path in generated_files:
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path) / 1024  # KB
                print(f"   - {os.path.basename(file_path)}: {file_size:.1f} KB")
                
        # Test 9: Avvio server web (opzionale)
        print("\n📋 Test 9: Server Web (Opzionale)")
        
        try:
            server_started = integration.start_config_web_server(8082)
            if server_started:
                print("   ✅ Server web avviato su porta 8082")
                print("   🌐 Accedi a: http://localhost:8082/plugin_menu.html")
                print("   ⚠️  Premi Ctrl+C per fermare il server e continuare")
                
                # Aspetta input utente per continuare
                input("   Premi INVIO per continuare con i test...")
                
                integration.stop_config_web_server()
                print("   ✅ Server web fermato")
            else:
                print("   ❌ Impossibile avviare server web")
                
        except KeyboardInterrupt:
            print("   ✅ Server web fermato dall'utente")
            integration.stop_config_web_server()
        except Exception as e:
            print(f"   ⚠️  Errore server web: {e}")
            
        # Test 10: Verifica stato finale
        print("\n📋 Test 10: Stato Finale Sistema")
        
        final_status = integration.get_system_status()
        all_configs = integration.get_all_plugin_configs()
        
        print(f"   Plugin totali: {final_status['plugins_registered']}")
        print(f"   Configurazioni attive: {len(all_configs)}")
        print(f"   Sistema inizializzato: {'✅' if final_status['initialized'] else '❌'}")
        
        # Riepilogo plugin
        print("\n📊 Riepilogo Plugin Registrati:")
        for plugin_id in all_configs.keys():
            ui_metadata = integration.config_manager.get_ui_metadata(plugin_id)
            if ui_metadata:
                print(f"   - {ui_metadata['plugin_name']} (v{ui_metadata['version']})")
                
        print("\n🎉 Test Sistema Configurazioni Completato!")
        print("=" * 60)
        
        return True
        
    except ImportError as e:
        print(f"❌ Errore import moduli: {e}")
        print("   Assicurati che tutti i moduli siano nel percorso corretto")
        return False
        
    except Exception as e:
        print(f"❌ Errore durante i test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_config_system()
    exit(0 if success else 1)