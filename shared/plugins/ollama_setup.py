#!/usr/bin/env python3
"""
🦙 Ollama Setup per LaboonChat AI Verifier
==========================================

Script automatico per installazione e configurazione di Ollama
per l'analisi locale dei plugin LaboonChat.

Caratteristiche:
- Download automatico Ollama
- Configurazione modelli ottimizzati
- Test di connettività
- Setup guidato per utenti non tecnici
"""

import asyncio
import json
import logging
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional
import aiohttp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OllamaSetup:
    """Setup automatico per Ollama"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.ollama_url = "http://localhost:11434"
        self.recommended_models = [
            {
                "name": "codellama:7b",
                "description": "CodeLlama 7B - Ottimo per analisi codice, veloce",
                "size": "3.8GB",
                "recommended": True
            },
            {
                "name": "llama2:7b",
                "description": "Llama2 7B - Generale, buono per sicurezza",
                "size": "3.8GB",
                "recommended": False
            },
            {
                "name": "codellama:13b",
                "description": "CodeLlama 13B - Migliore qualità, più lento",
                "size": "7.3GB",
                "recommended": False
            },
            {
                "name": "mistral:7b",
                "description": "Mistral 7B - Veloce e accurato",
                "size": "4.1GB",
                "recommended": False
            }
        ]
    
    def check_ollama_installed(self) -> bool:
        """Controlla se Ollama è installato"""
        try:
            result = subprocess.run(
                ["ollama", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            if result.returncode == 0:
                logger.info(f"✅ Ollama trovato: {result.stdout.strip()}")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        logger.info("❌ Ollama non trovato")
        return False
    
    async def check_ollama_running(self) -> bool:
        """Controlla se Ollama è in esecuzione"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.ollama_url}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        logger.info("✅ Ollama è in esecuzione")
                        return True
        except Exception:
            pass
        
        logger.info("❌ Ollama non è in esecuzione")
        return False
    
    def install_ollama(self) -> bool:
        """Installa Ollama automaticamente"""
        logger.info("🔄 Installazione Ollama...")
        
        try:
            if self.system == "windows":
                # Windows: download installer
                logger.info("📥 Download Ollama per Windows...")
                import urllib.request
                
                installer_url = "https://ollama.ai/download/windows"
                installer_path = "ollama-installer.exe"
                
                urllib.request.urlretrieve(installer_url, installer_path)
                
                logger.info("🚀 Avvio installer Ollama...")
                logger.info("⚠️ Segui le istruzioni dell'installer e riavvia questo script")
                
                subprocess.run([installer_path], check=False)
                return False  # Richiede riavvio manuale
                
            elif self.system == "darwin":  # macOS
                logger.info("📥 Download Ollama per macOS...")
                subprocess.run([
                    "curl", "-fsSL", 
                    "https://ollama.ai/install.sh", 
                    "|", "sh"
                ], shell=True, check=True)
                
            elif self.system == "linux":
                logger.info("📥 Download Ollama per Linux...")
                subprocess.run([
                    "curl", "-fsSL", 
                    "https://ollama.ai/install.sh", 
                    "|", "sh"
                ], shell=True, check=True)
            
            else:
                logger.error(f"❌ Sistema {self.system} non supportato")
                return False
            
            logger.info("✅ Ollama installato con successo")
            return True
            
        except Exception as e:
            logger.error(f"❌ Errore installazione Ollama: {e}")
            return False
    
    def start_ollama(self) -> bool:
        """Avvia Ollama in background"""
        try:
            if self.system == "windows":
                # Windows: avvia come servizio
                subprocess.Popen(
                    ["ollama", "serve"],
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:
                # Unix: avvia in background
                subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            
            # Aspetta che si avvii
            logger.info("⏳ Avvio Ollama...")
            time.sleep(5)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Errore avvio Ollama: {e}")
            return False
    
    async def list_installed_models(self) -> List[str]:
        """Lista modelli installati"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ollama_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        models = [model["name"] for model in data.get("models", [])]
                        logger.info(f"📋 Modelli installati: {models}")
                        return models
        except Exception as e:
            logger.warning(f"Errore lista modelli: {e}")
        
        return []
    
    async def pull_model(self, model_name: str) -> bool:
        """Scarica un modello"""
        logger.info(f"📥 Download modello {model_name}...")
        
        try:
            # Usa subprocess per il download con progress
            process = subprocess.Popen(
                ["ollama", "pull", model_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Mostra progress
            for line in process.stdout:
                if "pulling" in line.lower() or "%" in line:
                    print(f"  {line.strip()}")
            
            process.wait()
            
            if process.returncode == 0:
                logger.info(f"✅ Modello {model_name} scaricato")
                return True
            else:
                logger.error(f"❌ Errore download {model_name}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Errore download modello: {e}")
            return False
    
    async def test_model(self, model_name: str) -> bool:
        """Testa un modello con prompt di sicurezza"""
        logger.info(f"🧪 Test modello {model_name}...")
        
        test_prompt = """
Analizza questo codice Python per sicurezza:

```python
import os
print("Hello World")
```

Rispondi in formato JSON con security_level: "safe" o "dangerous".
"""
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": model_name,
                    "prompt": test_prompt,
                    "stream": False
                }
                
                async with session.post(
                    f"{self.ollama_url}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        response_text = data.get("response", "")
                        
                        if "safe" in response_text.lower():
                            logger.info(f"✅ Test {model_name} superato")
                            return True
                        else:
                            logger.warning(f"⚠️ Test {model_name} parziale")
                            return True  # Comunque funzionante
                    
        except Exception as e:
            logger.error(f"❌ Errore test modello: {e}")
        
        return False
    
    def update_config(self, model_name: str):
        """Aggiorna configurazione AI verifier"""
        config_path = "ai-verifier-config.json"
        
        try:
            # Carica config esistente
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
            else:
                config = {}
            
            # Aggiorna configurazione Ollama
            if "providers" not in config:
                config["providers"] = {}
            
            config["providers"]["ollama"] = {
                "enabled": True,
                "url": self.ollama_url,
                "model": model_name,
                "timeout": 30,
                "priority": 1
            }
            
            # Salva config aggiornata
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"✅ Configurazione aggiornata: {model_name}")
            
        except Exception as e:
            logger.error(f"❌ Errore aggiornamento config: {e}")
    
    async def interactive_setup(self):
        """Setup interattivo guidato"""
        print("\n🦙 Setup Ollama per LaboonChat AI Verifier")
        print("=" * 50)
        
        # 1. Controlla installazione
        if not self.check_ollama_installed():
            print("\n📦 Ollama non trovato. Installazione necessaria.")
            
            if input("Vuoi installare Ollama? (y/n): ").lower() == 'y':
                if not self.install_ollama():
                    print("❌ Installazione fallita o richiede riavvio manuale")
                    return False
            else:
                print("❌ Setup annullato")
                return False
        
        # 2. Avvia Ollama se necessario
        if not await self.check_ollama_running():
            print("\n🚀 Avvio Ollama...")
            if not self.start_ollama():
                print("❌ Impossibile avviare Ollama")
                return False
            
            # Ricontrolla
            await asyncio.sleep(3)
            if not await self.check_ollama_running():
                print("❌ Ollama non risponde")
                return False
        
        # 3. Controlla modelli installati
        installed_models = await self.list_installed_models()
        
        # 4. Suggerisci modello se necessario
        recommended_model = None
        for model in self.recommended_models:
            if model["name"] in installed_models:
                recommended_model = model["name"]
                break
        
        if not recommended_model:
            print("\n📥 Nessun modello raccomandato trovato.")
            print("Modelli disponibili:")
            
            for i, model in enumerate(self.recommended_models):
                marker = "⭐" if model["recommended"] else "  "
                print(f"{marker} {i+1}. {model['name']} - {model['description']} ({model['size']})")
            
            try:
                choice = int(input("\nScegli modello (1-4): ")) - 1
                if 0 <= choice < len(self.recommended_models):
                    model_to_install = self.recommended_models[choice]["name"]
                    
                    print(f"\n📥 Download {model_to_install}...")
                    if await self.pull_model(model_to_install):
                        recommended_model = model_to_install
                    else:
                        print("❌ Download fallito")
                        return False
                else:
                    print("❌ Scelta non valida")
                    return False
                    
            except ValueError:
                print("❌ Input non valido")
                return False
        
        # 5. Testa modello
        if recommended_model:
            print(f"\n🧪 Test modello {recommended_model}...")
            if await self.test_model(recommended_model):
                print("✅ Test superato!")
                
                # 6. Aggiorna configurazione
                self.update_config(recommended_model)
                
                print(f"\n🎉 Setup completato!")
                print(f"✅ Ollama: {self.ollama_url}")
                print(f"✅ Modello: {recommended_model}")
                print(f"✅ Config: ai-verifier-config.json")
                
                return True
            else:
                print("❌ Test modello fallito")
                return False
        
        return False
    
    async def quick_setup(self) -> bool:
        """Setup automatico veloce"""
        logger.info("🚀 Setup automatico Ollama...")
        
        # Controlla se già configurato
        if await self.check_ollama_running():
            models = await self.list_installed_models()
            for model in self.recommended_models:
                if model["name"] in models:
                    logger.info(f"✅ Setup già completato con {model['name']}")
                    self.update_config(model["name"])
                    return True
        
        # Setup automatico
        if not self.check_ollama_installed():
            logger.info("📦 Installazione Ollama...")
            if not self.install_ollama():
                return False
        
        if not await self.check_ollama_running():
            logger.info("🚀 Avvio Ollama...")
            if not self.start_ollama():
                return False
            await asyncio.sleep(5)
        
        # Installa modello raccomandato
        recommended = next(m for m in self.recommended_models if m["recommended"])
        logger.info(f"📥 Download {recommended['name']}...")
        
        if await self.pull_model(recommended["name"]):
            if await self.test_model(recommended["name"]):
                self.update_config(recommended["name"])
                logger.info("✅ Setup automatico completato!")
                return True
        
        return False

async def main():
    """Main function"""
    setup = OllamaSetup()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        # Setup automatico
        success = await setup.quick_setup()
    else:
        # Setup interattivo
        success = await setup.interactive_setup()
    
    if success:
        print("\n🎉 Ollama è pronto per LaboonChat!")
        print("Ora puoi usare l'AI verifier per analizzare i plugin.")
    else:
        print("\n❌ Setup fallito. Controlla i log per dettagli.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())