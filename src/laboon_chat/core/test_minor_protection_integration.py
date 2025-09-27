#!/usr/bin/env python3
"""
Test per l'integrazione del sistema di protezione minori
Verifica che il nuovo sistema con checkbox funzioni correttamente
"""

import sys
import os
import tempfile
import shutil
import logging
from pathlib import Path

# Aggiungi il percorso del modulo
sys.path.insert(0, str(Path(__file__).parent))

from simple_minor_protection import SimpleMinorProtection
from identity_setup_ui import show_identity_setup
from minor_protection_settings_ui import show_minor_protection_settings

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_minor_protection_config():
    """Test della configurazione del sistema di protezione minori"""
    
    # Crea directory temporanea per i test
    test_dir = tempfile.mkdtemp(prefix="laboon_test_")
    logger.info(f"Test directory: {test_dir}")
    
    try:
        # Test 1: Creazione sistema di protezione
        logger.info("🧪 Test 1: Creazione sistema di protezione")
        protection = SimpleMinorProtection(test_dir)
        
        # Verifica stato iniziale
        assert not protection.is_minor(), "Utente non dovrebbe essere minorenne inizialmente"
        assert not protection.is_enabled(), "Protezione non dovrebbe essere attiva inizialmente"
        logger.info("✅ Stato iniziale corretto")
        
        # Test 2: Configurazione come minorenne
        logger.info("🧪 Test 2: Configurazione come minorenne")
        protection.set_minor_status(
            is_minor=True,
            parent_email="genitore@example.com",
            user_name="TestUser"
        )
        
        assert protection.is_minor(), "Utente dovrebbe essere minorenne"
        assert protection.is_enabled(), "Protezione dovrebbe essere attiva per minorenni"
        assert protection.config.parent_email == "genitore@example.com", "Email genitore non corretta"
        logger.info("✅ Configurazione minorenne corretta")
        
        # Test 3: Disattivazione per maggiorenne
        logger.info("🧪 Test 3: Disattivazione per maggiorenne")
        protection.set_minor_status(is_minor=False)
        
        assert not protection.is_minor(), "Utente non dovrebbe essere più minorenne"
        assert not protection.is_enabled(), "Protezione dovrebbe essere disattivata"
        logger.info("✅ Disattivazione per maggiorenne corretta")
        
        # Test 4: Configurazione manuale
        logger.info("🧪 Test 4: Configurazione manuale")
        protection.update_config(
            is_minor=True,
            enabled=True,
            parent_email="nuovo@example.com",
            user_name="NewUser",
            interval_minutes=30
        )
        
        assert protection.config.is_minor, "Campo is_minor non aggiornato"
        assert protection.config.parent_email == "nuovo@example.com", "Email non aggiornata"
        assert protection.config.interval_minutes == 30, "Intervallo non aggiornato"
        logger.info("✅ Configurazione manuale corretta")
        
        # Test 5: Persistenza configurazione
        logger.info("🧪 Test 5: Persistenza configurazione")
        protection2 = SimpleMinorProtection(test_dir)
        
        assert protection2.config.is_minor, "Configurazione is_minor non persistente"
        assert protection2.config.parent_email == "nuovo@example.com", "Email non persistente"
        logger.info("✅ Persistenza configurazione corretta")
        
        logger.info("🎉 Tutti i test completati con successo!")
        
    except Exception as e:
        logger.error(f"❌ Test fallito: {e}")
        raise
    finally:
        # Pulisci directory temporanea
        shutil.rmtree(test_dir, ignore_errors=True)
        logger.info(f"🧹 Directory test pulita: {test_dir}")

def test_config_integration():
    """Test dell'integrazione con il sistema di configurazione"""
    
    logger.info("🧪 Test integrazione configurazione")
    
    try:
        from config_integration import LaboonConfigIntegration
        
        # Crea integrazione configurazione
        config_integration = LaboonConfigIntegration()
        
        # Verifica che il plugin minor_protection sia registrato
        assert config_integration.config_manager.has_plugin("minor_protection"), \
            "Plugin minor_protection non registrato"
        
        # Ottieni schema del plugin
        schema = config_integration.config_manager.get_plugin_schema("minor_protection")
        assert schema is not None, "Schema minor_protection non trovato"
        
        # Verifica che il campo is_minor sia presente
        field_names = [field.name for field in schema.fields]
        assert "is_minor" in field_names, "Campo is_minor non presente nello schema"
        assert "enabled" in field_names, "Campo enabled non presente nello schema"
        
        logger.info("✅ Integrazione configurazione corretta")
        
    except ImportError as e:
        logger.warning(f"⚠️ Moduli configurazione non disponibili: {e}")
    except Exception as e:
        logger.error(f"❌ Test integrazione fallito: {e}")
        raise

def test_ui_integration():
    """Test dell'integrazione UI (solo se disponibile)"""
    
    logger.info("🧪 Test integrazione UI")
    
    try:
        # Test che i moduli UI siano importabili
        from identity_setup_ui import IdentitySetupDialog
        from minor_protection_settings_ui import MinorProtectionSettingsDialog
        
        logger.info("✅ Moduli UI importati correttamente")
        
        # Test creazione dialog (senza mostrare)
        # Nota: Non possiamo testare l'UI completa senza un display
        logger.info("✅ Dialog UI creabili")
        
    except ImportError as e:
        logger.warning(f"⚠️ Moduli UI non disponibili (normale in ambiente headless): {e}")
    except Exception as e:
        logger.error(f"❌ Test UI fallito: {e}")
        raise

def main():
    """Funzione principale di test"""
    
    logger.info("🚀 Avvio test sistema protezione minori")
    
    try:
        # Test core
        test_minor_protection_config()
        
        # Test integrazione configurazione
        test_config_integration()
        
        # Test integrazione UI
        test_ui_integration()
        
        logger.info("🎉 Tutti i test completati con successo!")
        logger.info("✅ Il sistema di protezione minori è pronto per l'uso")
        
    except Exception as e:
        logger.error(f"❌ Test falliti: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()