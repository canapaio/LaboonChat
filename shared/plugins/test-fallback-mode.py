#!/usr/bin/env python3
"""
Test per verificare il fallback elegante quando AI non è disponibile
"""

import logging
import sys
import tempfile
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_fallback_mode():
    """Test modalità fallback senza AI"""
    
    # Simula assenza AI rinominando temporaneamente il modulo
    ai_verifier_path = Path("ai_code_verifier.py")
    ai_verifier_backup = None
    
    try:
        # Backup temporaneo del modulo AI
        if ai_verifier_path.exists():
            ai_verifier_backup = ai_verifier_path.with_suffix('.py.backup')
            ai_verifier_path.rename(ai_verifier_backup)
            logging.info("🔒 Modulo AI temporaneamente disabilitato")
        
        # Importa il sistema di sicurezza (dovrebbe fallback)
        from simple_security import SimplePluginSecurity
        
        # Inizializza sistema
        security = SimplePluginSecurity()
        logging.info("✅ Sistema sicurezza inizializzato in modalità tradizionale")
        
        # Test plugin di esempio
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
# Plugin di test
def hello():
    print("Hello World!")
""")
            plugin_path = Path(f.name)
        
        # Verifica plugin
        result = security.check_plugin(plugin_path)
        
        logging.info(f"🔍 Test plugin: {result.name}")
        logging.info(f"  Status: {result.status.value}")
        logging.info(f"  Trust Score: {result.trust_score:.2f}")
        logging.info(f"  AI Analysis: {'Disponibile' if result.ai_analysis else 'Non disponibile'}")
        
        # Verifica che funzioni senza AI
        assert result.ai_analysis is None, "AI dovrebbe essere None in modalità fallback"
        assert result.trust_score > 0, "Trust score dovrebbe essere calcolato"
        
        logging.info("✅ Test fallback completato con successo!")
        
        # Cleanup
        plugin_path.unlink()
        
    except Exception as e:
        logging.error(f"❌ Errore durante test fallback: {e}")
        return False
        
    finally:
        # Ripristina modulo AI se esisteva
        if ai_verifier_backup and ai_verifier_backup.exists():
            ai_verifier_backup.rename(ai_verifier_path)
            logging.info("🔄 Modulo AI ripristinato")
    
    return True

def test_ai_optional_import():
    """Test che l'import AI sia veramente opzionale"""
    
    logging.info("🧪 Test import opzionale AI...")
    
    try:
        # Test import diretto
        from simple_security import SimplePluginSecurity, AI_VERIFIER_AVAILABLE
        
        logging.info(f"📊 AI_VERIFIER_AVAILABLE: {AI_VERIFIER_AVAILABLE}")
        
        # Inizializza sistema
        security = SimplePluginSecurity()
        
        if AI_VERIFIER_AVAILABLE:
            logging.info("✅ AI disponibile - sistema ibrido attivo")
            assert security.ai_verifier is not None, "AI verifier dovrebbe essere inizializzato"
        else:
            logging.info("✅ AI non disponibile - modalità tradizionale attiva")
            assert security.ai_verifier is None, "AI verifier dovrebbe essere None"
        
        return True
        
    except Exception as e:
        logging.error(f"❌ Errore test import: {e}")
        return False

if __name__ == "__main__":
    logging.info("🧪 Avvio test modalità fallback...")
    
    # Test 1: Import opzionale
    success1 = test_ai_optional_import()
    
    # Test 2: Fallback completo
    success2 = test_fallback_mode()
    
    if success1 and success2:
        logging.info("🎉 Tutti i test fallback completati con successo!")
        sys.exit(0)
    else:
        logging.error("❌ Alcuni test fallback sono falliti")
        sys.exit(1)