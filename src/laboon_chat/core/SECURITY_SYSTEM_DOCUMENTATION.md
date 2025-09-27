# Sistema di Sicurezza LaboonChat - Documentazione Completa

## 🛡️ Panoramica del Sistema

Il sistema di sicurezza di LaboonChat implementa un approccio multi-livello per proteggere l'applicazione da plugin potenzialmente dannosi, con particolare attenzione ai **downgrade di certificazione**.

### Componenti Principali

1. **Security Dashboard** - Monitoraggio e gestione eventi di sicurezza
2. **Secure Boot Manager** - Gestione del boot sicuro dei plugin
3. **Sistema di Avvertimenti** - Notifiche per downgrade di certificazione
4. **Modalità Sviluppatore** - Bypass controllato per sviluppo

## 🚨 Sistema di Avvertimenti per Downgrade Certificazione

### Problema Risolto

**Richiesta Originale**: *"dai un avvertimento se un plugin passa da certificato a non certificato e chiedi se sei un dev ed ignorare il problema se si sta programmando l'app"*

### Implementazione

#### 1. Rilevamento Downgrade

Il sistema monitora automaticamente i cambiamenti di certificazione:

```python
def _check_certification_downgrade(self, plugin_name: str, current_cert: str) -> bool:
    """Verifica se c'è stato un downgrade di certificazione"""
    if plugin_name not in self.certification_history:
        return False
    
    previous_cert = self.certification_history[plugin_name].get('level', 'NONE')
    
    # Ordine di priorità certificazioni (dal più alto al più basso)
    cert_priority = {'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1, 'NONE': 0}
    
    prev_priority = cert_priority.get(previous_cert, 0)
    curr_priority = cert_priority.get(current_cert, 0)
    
    return prev_priority > curr_priority
```

#### 2. Gestione Interattiva

Quando viene rilevato un downgrade, il sistema presenta opzioni all'utente:

```
🚨 AVVERTIMENTO SICUREZZA - DOWNGRADE CERTIFICAZIONE
============================================================
Plugin: example_plugin
Certificazione precedente: HIGH
Certificazione attuale: NONE

⚠️  QUESTO POTREBBE INDICARE:
   • Plugin compromesso o modificato
   • Certificazione scaduta o revocata
   • Possibile minaccia alla sicurezza

Scegli un'azione:
1. Blocca plugin (raccomandato)
2. Metti in quarantena
3. Ignora (solo per sviluppatori)
```

#### 3. Modalità Sviluppatore

```python
def set_developer_mode(self, enabled: bool):
    """Attiva/disattiva modalità sviluppatore"""
    self.developer_mode = enabled
    if enabled:
        self.log_event(
            ThreatType.SYSTEM_EVENT,
            "Modalità sviluppatore ATTIVATA - Avvertimenti downgrade disabilitati",
            SecurityLevel.LOW
        )
```

## 📊 Architettura del Sistema

### Security Dashboard

**File**: `security_dashboard.py`

**Responsabilità**:
- Monitoraggio eventi di sicurezza in tempo reale
- Gestione storico certificazioni plugin
- Generazione report di sicurezza
- Gestione modalità sviluppatore

**Metriche Tracciate**:
- Plugin consentiti/bloccati/in quarantena
- Eventi di sicurezza per tipo
- Downgrade di certificazione
- Attività sviluppatore

### Secure Boot Manager

**File**: `secure_boot.py`

**Responsabilità**:
- Verifica integrità plugin al boot
- Controllo certificazioni
- Applicazione politiche di sicurezza
- Integrazione con Security Dashboard

### Integrazione Core

**File**: `core/__init__.py`

Il sistema è integrato nel core di LaboonChat:

```python
async def boot(self):
    """Avvio sicuro del sistema"""
    # ... inizializzazione componenti ...
    
    # Inizializza dashboard sicurezza
    self.security_dashboard = create_security_dashboard(
        str(self.data_dir / "security")
    )
    
    # Boot sicuro plugin
    if self.security_dashboard:
        boot_stats = await initialize_secure_boot(
            self.plugin_manager,
            str(self.plugins_dir),
            str(self.data_dir / "certified_repo"),
            str(self.data_dir / "security")
        )
        
        # Aggiorna dashboard con statistiche
        self.security_dashboard.update_system_metrics({
            'plugins_allowed': boot_stats.get('allowed', 0),
            'plugins_quarantined': boot_stats.get('quarantined', 0),
            'plugins_blocked': boot_stats.get('blocked', 0)
        })
```

## 🧪 Test e Validazione

### Test Automatizzati

**File**: `test_secure_boot_system.py`

Il sistema include test completi che verificano:

1. **Verifica Plugin Individuali**
   - Plugin certificati → ALLOW
   - Plugin sospetti → QUARANTINE  
   - Plugin malizi → BLOCK

2. **Simulazione Boot Completo**
   - Caricamento repository certificato
   - Verifica batch di plugin
   - Statistiche finali

3. **Test Downgrade Certificazione**
   - Simulazione cambio certificazione
   - Verifica avvertimenti
   - Test modalità sviluppatore

### Risultati Test

```
📊 STATISTICHE BOOT SICURO:
   ✅ Plugin consentiti: 0
   🔒 Plugin in quarantena: 1
   🚫 Plugin bloccati: 2

📈 RIEPILOGO FINALE:
   • Sistema di verifica plugin: ✅ FUNZIONANTE
   • Sistema di quarantena: ✅ FUNZIONANTE
   • Sistema di blocco: ✅ FUNZIONANTE
   • Sistema avvertimenti: ✅ FUNZIONANTE
   • Repository certificato: ✅ FUNZIONANTE
```

## 🔧 Configurazione e Utilizzo

### Attivazione Modalità Sviluppatore

```python
# Tramite Security Dashboard
dashboard.set_developer_mode(True)

# Oppure durante test interattivo
# Il sistema chiederà automaticamente se si è sviluppatori
```

### Struttura Directory

```
LaboonChat/
├── src/laboon_chat/core/
│   ├── security_dashboard.py      # Dashboard sicurezza
│   ├── secure_boot.py            # Boot sicuro
│   ├── __init__.py               # Integrazione core
│   └── test_secure_boot_system.py # Test sistema
├── data/
│   ├── security/                 # Dati sicurezza
│   │   ├── security_events.json  # Eventi sicurezza
│   │   ├── system_metrics.json   # Metriche sistema
│   │   └── cert_history.json     # Storico certificazioni
│   └── certified_repo/           # Repository certificato
│       └── certified_plugins.json
└── test_plugins/                 # Plugin di test
    ├── certified_plugin.py
    ├── suspicious_plugin.py
    └── malicious_plugin.py
```

## 🛠️ Personalizzazione

### Aggiunta Nuovi Tipi di Minaccia

```python
class ThreatType(Enum):
    MALICIOUS_CODE = "MALICIOUS_CODE"
    SUSPICIOUS_BEHAVIOR = "SUSPICIOUS_BEHAVIOR"
    CERTIFICATION_DOWNGRADE = "CERTIFICATION_DOWNGRADE"
    # Aggiungi nuovi tipi qui
    CUSTOM_THREAT = "CUSTOM_THREAT"
```

### Configurazione Soglie Sicurezza

```python
# In security_dashboard.py
TRUST_THRESHOLDS = {
    'ALLOW': 80.0,      # Plugin consentiti
    'QUARANTINE': 40.0, # Plugin in quarantena
    'BLOCK': 0.0        # Plugin bloccati
}
```

## 📈 Monitoraggio e Report

### Eventi di Sicurezza

Il sistema traccia automaticamente:
- Tentativi di caricamento plugin
- Downgrade di certificazione
- Attivazione modalità sviluppatore
- Blocchi e quarantene

### Report Automatici

```python
# Genera report sicurezza
report = dashboard.generate_security_report()
print(report)

# Eventi recenti
events = dashboard.get_recent_events(limit=10)
for event in events:
    print(f"{event.timestamp}: {event.message}")
```

## 🔒 Sicurezza e Best Practices

### Raccomandazioni

1. **Modalità Produzione**: Disabilitare modalità sviluppatore
2. **Aggiornamenti**: Mantenere repository certificato aggiornato
3. **Monitoraggio**: Controllare regolarmente eventi di sicurezza
4. **Backup**: Salvare storico certificazioni

### Limitazioni Conosciute

- Il sistema si basa su pattern statici per rilevare codice sospetto
- La modalità sviluppatore bypassa tutti i controlli di downgrade
- Repository certificato deve essere mantenuto manualmente

## 🚀 Sviluppi Futuri

### Miglioramenti Pianificati

1. **Analisi Dinamica**: Esecuzione plugin in sandbox
2. **Machine Learning**: Rilevamento automatico minacce
3. **Aggiornamenti Automatici**: Sincronizzazione repository certificato
4. **API Esterna**: Integrazione con servizi di sicurezza

---

**Versione**: 1.0  
**Data**: 2025-01-27  
**Autore**: Sistema LaboonChat  
**Status**: ✅ IMPLEMENTATO E TESTATO