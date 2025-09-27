# 🚀 Guida Setup - Sistema AI Verifier LaboonChat

## 📋 Panoramica

Questa guida ti aiuterà a configurare e utilizzare il sistema AI Verifier di LaboonChat, sia in modalità tradizionale che con supporto AI opzionale.

## ⚡ Quick Start

### 1. **Setup Base (Modalità Tradizionale)**
```bash
# Clona il progetto
git clone <repository-url>
cd LaboonChat/shared/plugins

# Test immediato (senza AI)
python test-ai-integration.py
```

**Risultato atteso:**
```
🔒 Modalità sicurezza tradizionale (AI non disponibile)
✅ Test completato con successo!
```

### 2. **Setup Completo (Con AI Opzionale)**
```bash
# 1. Installa Ollama (se non già presente)
# Windows: Scarica da https://ollama.ai
# Linux/Mac: curl -fsSL https://ollama.ai/install.sh | sh

# 2. Verifica installazione
ollama --version

# 3. Scarica un modello (opzionale)
ollama pull llama2:7b

# 4. Test con AI
python test-ai-integration.py
```

**Risultato atteso:**
```
🤖 AI Code Verifier disponibile (opzionale)
✅ AI Code Verifier inizializzato (Ollama preinstallato)
🎉 Test completato con successo!
```

## 🔧 Configurazione Dettagliata

### Struttura File
```
LaboonChat/shared/plugins/
├── simple_security.py          # Sistema sicurezza principale
├── ai_code_verifier.py         # Modulo AI (opzionale)
├── ollama_setup.py             # Setup Ollama (opzionale)
├── test-ai-integration.py      # Test completo
├── test-fallback-mode.py       # Test modalità fallback
├── README-AI-VERIFIER.md       # Documentazione completa
└── SETUP-GUIDE.md             # Questa guida
```

### Dipendenze Python

**Base (sempre richieste):**
```python
# Built-in modules
import hashlib
import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from enum import Enum
from dataclasses import dataclass
```

**AI Opzionali:**
```bash
pip install aiohttp  # Per comunicazione con Ollama
```

## 🧪 Testing e Verifica

### Test Completo
```bash
# Test principale con tutti i plugin
python test-ai-integration.py

# Output atteso:
# 🔍 Test plugin: safe_emoji.py - Status: warning
# 🔍 Test plugin: suspicious_weather.py - Status: warning  
# 🔍 Test plugin: dangerous_system.py - Status: blocked
```

### Test Modalità Fallback
```bash
# Test senza AI
python test-fallback-mode.py

# Verifica che il sistema funzioni anche senza AI
```

### Test Personalizzati
```python
from simple_security import SimplePluginSecurity
from pathlib import Path

# Inizializza sistema
security = SimplePluginSecurity()

# Test plugin personalizzato
result = security.check_plugin(Path("mio_plugin.py"))
print(f"Status: {result.status.value}")
print(f"Trust Score: {result.trust_score:.2f}")
print(f"AI Analysis: {'Sì' if result.ai_analysis else 'No'}")
```

## 🔍 Troubleshooting

### Problema: "AI non disponibile"
```
🔒 Modalità sicurezza tradizionale (AI non disponibile)
```

**Diagnosi:**
```bash
# 1. Verifica Ollama
ollama --version
# Se errore: Ollama non installato

# 2. Verifica moduli Python
python -c "from ai_code_verifier import AICodeVerifier"
# Se errore: Modulo AI mancante

# 3. Verifica file
ls -la ai_code_verifier.py ollama_setup.py
```

**Soluzioni:**
- **Ollama mancante**: Installa da https://ollama.ai
- **Moduli mancanti**: Verifica che i file `.py` esistano
- **Permessi**: Verifica permessi di lettura sui file

### Problema: "Ollama non risponde"
```
⚠️ Ollama non trovato, modalità tradizionale attiva
```

**Diagnosi:**
```bash
# Verifica servizio Ollama
ollama list
ollama serve  # Avvia servizio se necessario
```

**Soluzioni:**
- Avvia servizio Ollama: `ollama serve`
- Verifica porta: `curl http://localhost:11434/api/version`
- Riavvia Ollama se necessario

### Problema: "Performance lenta"
```
🤖 AI analysis completata per plugin (5.2s)
```

**Ottimizzazioni:**
- Usa modelli più piccoli: `ollama pull llama2:7b` invece di modelli grandi
- Abilita cache: Il sistema cache automaticamente i risultati
- Modalità tradizionale: Disabilita AI per performance massime

## 🎯 Modalità di Utilizzo

### 1. **Sviluppo Locale**
```python
# Setup per sviluppo
security = SimplePluginSecurity(data_dir=Path("./dev_cache"))

# Test rapidi senza AI
security.config["ai_enabled"] = False
```

### 2. **Produzione con AI**
```python
# Setup produzione completo
security = SimplePluginSecurity()

# Verifica che AI sia disponibile
if security.ai_verifier:
    print("✅ AI attivo in produzione")
else:
    print("⚠️ Produzione in modalità tradizionale")
```

### 3. **CI/CD Pipeline**
```bash
# Test automatici in CI
python test-ai-integration.py
python test-fallback-mode.py

# Verifica che entrambi passino
echo $?  # Dovrebbe essere 0
```

## 🔧 Personalizzazione

### Configurazione Sicurezza
```python
security = SimplePluginSecurity()

# Modifica soglie
security.config.update({
    "trust_threshold": 0.7,      # Soglia SAFE/WARNING
    "cache_duration": 86400,     # Cache 24h
    "ai_timeout": 30             # Timeout AI 30s
})

# Pattern personalizzati
security.suspicious_patterns.extend([
    "eval(",
    "exec(",
    "subprocess.call"
])
```

### Blacklist Personalizzata
```python
# Aggiungi plugin alla blacklist
security.blacklist.update({
    "malicious_plugin.py",
    "sha256_hash_of_bad_plugin"
})
```

### Registry Personalizzato
```python
# Override registry check
def custom_registry_check(checksum):
    # Logica personalizzata
    return checksum in my_trusted_checksums

security._is_in_official_registry = custom_registry_check
```

## 📊 Monitoraggio

### Log Analysis
```python
import logging

# Abilita logging dettagliato
logging.basicConfig(level=logging.DEBUG)

# I log mostrano:
# 🤖 AI analysis completata per plugin_name
# 🔒 AI analysis fallita per plugin_name: ErrorType
# ✅ Plugin verificato e sicuro
# ⚠️ Plugin potenzialmente sicuro, usare con cautela
```

### Metriche Performance
```python
import time

start = time.time()
result = security.check_plugin(plugin_path)
duration = time.time() - start

print(f"Analisi completata in {duration:.2f}s")
print(f"AI utilizzata: {'Sì' if result.ai_analysis else 'No'}")
```

## 🚀 Deployment

### Ambiente Sviluppo
```bash
# Setup minimo per sviluppo
git clone <repo>
cd LaboonChat/shared/plugins
python test-ai-integration.py
```

### Ambiente Produzione
```bash
# Setup completo per produzione
# 1. Installa Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 2. Configura modelli
ollama pull llama2:7b

# 3. Avvia servizio
systemctl enable ollama
systemctl start ollama

# 4. Deploy applicazione
python -c "from simple_security import SimplePluginSecurity; print('✅ Setup OK')"
```

### Docker (Opzionale)
```dockerfile
FROM python:3.9-slim

# Installa Ollama (opzionale)
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Copia applicazione
COPY . /app
WORKDIR /app

# Test
RUN python test-ai-integration.py
```

## 🤝 Supporto

### FAQ Comuni

**Q: È obbligatorio installare Ollama?**
A: No, il sistema funziona perfettamente senza AI in modalità tradizionale.

**Q: Quali modelli Ollama sono supportati?**
A: Tutti i modelli compatibili con Ollama. Consigliati: llama2, codellama, mistral.

**Q: Come disabilito completamente l'AI?**
A: Rinomina o rimuovi `ai_code_verifier.py`. Il sistema rileverà automaticamente l'assenza.

**Q: Il sistema è sicuro senza AI?**
A: Sì, la modalità tradizionale include checksum, blacklist e analisi statica robusta.

### Contatti
- Issues: GitHub Issues del progetto
- Documentazione: `README-AI-VERIFIER.md`
- Test: `test-ai-integration.py` e `test-fallback-mode.py`

---

*Guida Setup Sistema AI Verifier - LaboonChat v1.0* 🚀