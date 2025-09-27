# 🤖 Sistema AI Verifier per LaboonChat

## Panoramica

Il sistema AI Verifier di LaboonChat è un sistema di sicurezza **completamente opzionale** che utilizza l'intelligenza artificiale per analizzare e verificare la sicurezza dei plugin prima dell'installazione.

## 🎯 Caratteristiche Principali

### ✅ **Completamente Opzionale**
- Il sistema funziona perfettamente **senza AI**
- Fallback elegante alla modalità sicurezza tradizionale
- Nessuna dipendenza obbligatoria da Ollama o modelli AI

### 🔧 **Ollama Preinstallato**
- Rileva automaticamente Ollama se già installato nel sistema
- Non tenta di installare o configurare Ollama automaticamente
- Utilizza modelli già disponibili localmente

### 🛡️ **Sicurezza Ibrida**
- **Con AI**: Analisi avanzata del codice + sicurezza tradizionale
- **Senza AI**: Sicurezza tradizionale robusta (checksum, blacklist, analisi statica)

## 🏗️ Architettura

```
SimplePluginSecurity
├── 🔍 Analisi Tradizionale (sempre attiva)
│   ├── Calcolo checksum SHA256
│   ├── Controllo blacklist
│   ├── Verifica registry ufficiale
│   ├── Score community
│   └── Analisi statica basic
│
└── 🤖 Analisi AI (opzionale)
    ├── AICodeVerifier
    ├── Ollama integration
    └── Analisi semantica codice
```

## 📋 Stati Plugin

| Stato | Icona | Descrizione | Azione |
|-------|-------|-------------|---------|
| `SAFE` | ✅ | Plugin sicuro e verificato | Installazione automatica |
| `WARNING` | ⚠️ | Plugin potenzialmente sicuro | Richiede conferma utente |
| `BLOCKED` | 🚫 | Plugin pericoloso o sospetto | Installazione negata |

## 🚀 Utilizzo

### Inizializzazione Base
```python
from simple_security import SimplePluginSecurity

# Inizializzazione automatica (rileva AI se disponibile)
security = SimplePluginSecurity()

# Verifica plugin
result = security.check_plugin(Path("plugin.py"))
print(f"Status: {result.status.value}")
print(f"Trust Score: {result.trust_score:.2f}")
```

### Verifica Stato AI
```python
from simple_security import AI_VERIFIER_AVAILABLE

if AI_VERIFIER_AVAILABLE:
    print("🤖 AI disponibile - modalità ibrida")
else:
    print("🔒 Modalità tradizionale - senza AI")
```

## 🔧 Configurazione

### Requisiti Minimi
- Python 3.8+
- Dipendenze base: `hashlib`, `sqlite3`, `pathlib`

### Requisiti Opzionali (per AI)
- Ollama preinstallato nel sistema
- Modelli Ollama disponibili localmente
- Dipendenze AI: `aiohttp`, `asyncio`

### Verifica Ollama
Il sistema verifica automaticamente Ollama con:
```bash
ollama --version
```

## 📊 Algoritmo di Scoring

### Trust Score (0.0 - 1.0)

**Con AI disponibile:**
- Registry ufficiale: 40%
- Community score: 20%
- Analisi statica: 20%
- Analisi AI: 20%

**Senza AI:**
- Registry ufficiale: 50%
- Community score: 25%
- Analisi statica: 25%

### Soglie Decisione
- `≥ 0.8`: SAFE
- `≥ 0.5`: WARNING  
- `< 0.5`: BLOCKED

## 🧪 Testing

### Test Completo
```bash
python test-ai-integration.py
```

### Test Fallback
```bash
python test-fallback-mode.py
```

### Plugin di Test Inclusi
- `safe_emoji.py`: Plugin sicuro (dovrebbe essere WARNING/SAFE)
- `suspicious_weather.py`: Plugin sospetto (dovrebbe essere WARNING)
- `dangerous_system.py`: Plugin pericoloso (dovrebbe essere BLOCKED)

## 🔄 Modalità Operative

### 1. **Modalità Ibrida** (AI + Tradizionale)
```
🤖 AI Code Verifier disponibile (opzionale)
✅ AI Code Verifier inizializzato (Ollama preinstallato)
```
- Analisi AI completa del codice
- Decisioni basate su AI + trust score
- Maggiore precisione nella rilevazione minacce

### 2. **Modalità Tradizionale** (Solo Sicurezza Base)
```
🔒 Modalità sicurezza tradizionale (AI non disponibile)
```
- Analisi basata su pattern statici
- Checksum e blacklist
- Scoring community e registry

## 🛠️ Personalizzazione

### Configurazione Avanzata
```python
security = SimplePluginSecurity()

# Modifica soglie
security.config["trust_threshold"] = 0.7

# Aggiungi pattern sospetti personalizzati
security.suspicious_patterns.extend([
    "custom_dangerous_function",
    "suspicious_import"
])
```

### Cache e Performance
- Cache SQLite per risultati precedenti
- Validità cache: 24 ore
- Checksum per invalidazione automatica

## 🔍 Troubleshooting

### AI Non Disponibile
```
🔒 Modalità sicurezza tradizionale (AI non disponibile)
```
**Cause possibili:**
- Ollama non installato
- Moduli AI mancanti (`ai_code_verifier.py`)
- Errore inizializzazione

**Soluzione:** Il sistema continua a funzionare in modalità tradizionale.

### Ollama Non Rilevato
```
⚠️ Ollama non trovato, modalità tradizionale attiva
```
**Verifica:**
```bash
ollama --version
ollama list  # Verifica modelli disponibili
```

### Performance Lenta
- L'analisi AI può richiedere 2-5 secondi per plugin
- Cache riduce tempi per plugin già analizzati
- Modalità tradizionale è istantanea

## 📈 Roadmap

### Versione Attuale (v1.0)
- ✅ Sistema AI completamente opzionale
- ✅ Ollama preinstallato
- ✅ Fallback elegante
- ✅ Cache intelligente

### Prossime Versioni
- 🔄 Supporto OpenAI API (alternativa a Ollama)
- 🔄 Registry plugin distribuito
- 🔄 Whitelist community-driven
- 🔄 Analisi comportamentale runtime

## 🤝 Contribuire

Il sistema è progettato per essere estensibile:

1. **Nuovi Provider AI**: Implementa `AICodeVerifier` interface
2. **Pattern Sicurezza**: Aggiungi pattern in `_basic_static_analysis`
3. **Registry**: Estendi `_is_in_official_registry`
4. **Scoring**: Modifica algoritmi in `_calculate_trust_score`

---

*Sistema AI Verifier - Sicurezza intelligente e opzionale per LaboonChat* 🚀