# 🛡️ Sistema di Protezione Minori - LaboonChat

## Panoramica

Il sistema di protezione minori di LaboonChat è stato progettato per essere **semplice, elegante e pratico**. Invece di utilizzare date di nascita complesse, utilizza un approccio basato su checkbox durante la creazione dell'identità, con un sistema di plugin completamente configurabile e disattivabile.

## 🎯 Caratteristiche Principali

### ✅ Setup Semplificato
- **Checkbox durante la creazione identità**: "Sono un minorenne"
- **Nessuna data di nascita richiesta**: Approccio più privacy-friendly
- **Configurazione immediata**: Email genitore e impostazioni in un unico passaggio

### 🔧 Plugin Configurabile
- **Completamente disattivabile**: Il sistema può essere spento quando non necessario
- **Configurazione flessibile**: Intervalli di notifica, email SMTP personalizzabili
- **Gestione automatica**: Attivazione/disattivazione basata sullo status di minorenne

### 📧 Notifiche Email Intelligenti
- **Email di attivazione**: Notifica al genitore quando la protezione viene attivata
- **Email di disattivazione**: Notifica automatica quando l'utente diventa maggiorenne
- **Rapporti periodici**: Riassunti dell'utilizzo inviati ai genitori

## 🏗️ Architettura del Sistema

### Componenti Principali

1. **`SimpleMinorProtection`** - Core del sistema di protezione
2. **`IdentitySetupDialog`** - Interfaccia per setup iniziale identità
3. **`MinorProtectionSettingsDialog`** - Interfaccia per gestione impostazioni
4. **`LaboonConfigIntegration`** - Integrazione con sistema di configurazione

### Flusso di Utilizzo

```
Creazione Identità → Checkbox Minorenne → Configurazione Protezione → Monitoraggio Attivo
                                      ↓
                              Email Notifica Genitore
                                      ↓
                              Rapporti Periodici
                                      ↓
                              Disattivazione Automatica (Maggiorenne)
```

## 🚀 Guida all'Uso

### Per gli Sviluppatori

#### Inizializzazione del Sistema

```python
from simple_minor_protection import SimpleMinorProtection

# Crea istanza del sistema
protection = SimpleMinorProtection("/path/to/config")

# Verifica stato
if protection.is_minor():
    print("Utente configurato come minorenne")
    
if protection.is_enabled():
    print("Protezione attiva")
```

#### Configurazione come Minorenne

```python
# Imposta utente come minorenne
protection.set_minor_status(
    is_minor=True,
    parent_email="genitore@example.com",
    user_name="NomeUtente"
)
# La protezione si attiva automaticamente
```

#### Disattivazione per Maggiorenni

```python
# Quando l'utente diventa maggiorenne
protection.set_minor_status(is_minor=False)
# La protezione si disattiva automaticamente e invia email al genitore
```

#### Configurazione Avanzata

```python
# Aggiorna configurazioni
protection.update_config(
    interval_minutes=30,  # Notifiche ogni 30 minuti
    parent_email="nuovo@example.com",
    smtp_server="smtp.gmail.com",
    smtp_port=587
)
```

### Per gli Utenti

#### Setup Iniziale

1. **Avvia LaboonChat** per la prima volta
2. **Compila il form di identità**:
   - Nome utente
   - Email (opzionale)
   - ☑️ **"Sono un minorenne"** (se applicabile)
3. **Se minorenne**, inserisci:
   - Email del genitore
   - Intervallo notifiche (default: 60 minuti)
4. **Conferma** - Il sistema si attiva automaticamente

#### Gestione Impostazioni

1. **Accedi alle impostazioni** di protezione minori
2. **Visualizza stato attuale**:
   - Status: Attivo/Disattivo
   - Email genitore
   - Intervallo notifiche
3. **Modifica impostazioni** se necessario
4. **Disattiva protezione** quando diventi maggiorenne

## 📋 Configurazione

### Schema Configurazione

```json
{
  "is_minor": false,
  "enabled": false,
  "interval_minutes": 60,
  "parent_email": "",
  "user_name": "",
  "smtp_server": "localhost",
  "smtp_port": 587,
  "smtp_username": "",
  "smtp_password": "",
  "from_email": "protection@laboonchat.local"
}
```

### Campi Configurazione

| Campo | Tipo | Descrizione | Default |
|-------|------|-------------|---------|
| `is_minor` | boolean | Indica se l'utente è minorenne | `false` |
| `enabled` | boolean | Indica se la protezione è attiva | `false` |
| `interval_minutes` | integer | Intervallo notifiche (15-1440 min) | `60` |
| `parent_email` | string | Email del genitore per notifiche | `""` |
| `user_name` | string | Nome dell'utente | `""` |
| `smtp_server` | string | Server SMTP per invio email | `"localhost"` |
| `smtp_port` | integer | Porta SMTP | `587` |
| `smtp_username` | string | Username SMTP | `""` |
| `smtp_password` | string | Password SMTP | `""` |
| `from_email` | string | Email mittente | `"protection@laboonchat.local"` |

## 🔧 API Reference

### Classe `SimpleMinorProtection`

#### Metodi Principali

```python
def is_minor() -> bool
    """Verifica se l'utente è configurato come minorenne"""

def is_enabled() -> bool
    """Verifica se il sistema di protezione è attivo"""

def set_minor_status(is_minor: bool, parent_email: str = "", user_name: str = "")
    """Imposta lo stato di minorenne dell'utente"""

def enable_protection(parent_email: str, user_name: str = "", interval_minutes: int = 60, smtp_config: Dict = None)
    """Attiva il sistema di protezione minori"""

def disable_protection(reason: str = "Utente diventato maggiorenne")
    """Disattiva il sistema di protezione minori"""

def update_config(**kwargs)
    """Aggiorna la configurazione del sistema"""

def start_monitoring()
    """Avvia il monitoraggio e le notifiche periodiche"""

def stop_monitoring()
    """Ferma il monitoraggio"""
```

#### Metodi di Notifica

```python
def _send_activation_notification()
    """Invia email di attivazione al genitore"""

def _send_deactivation_notification(reason: str)
    """Invia email di disattivazione al genitore"""

def _send_usage_notification()
    """Invia rapporto periodico di utilizzo"""
```

### Interfacce UI

#### `IdentitySetupDialog`

```python
def show_identity_setup() -> Optional[Dict[str, Any]]
    """
    Mostra dialog di setup identità
    
    Returns:
        Dict con dati utente o None se cancellato
        {
            'username': str,
            'email': str,
            'is_minor': bool,
            'parent_email': str,  # se is_minor=True
            'notification_interval': int  # se is_minor=True
        }
    """
```

#### `MinorProtectionSettingsDialog`

```python
def show_minor_protection_settings(protection: SimpleMinorProtection) -> bool
    """
    Mostra dialog impostazioni protezione
    
    Args:
        protection: Istanza SimpleMinorProtection
        
    Returns:
        True se modifiche salvate, False se cancellato
    """
```

## 🧪 Testing

### Test Automatici

Il sistema include test completi in `test_minor_protection_integration.py`:

```bash
# Esegui i test
cd src/laboon_chat/core
python test_minor_protection_integration.py
```

### Test Coperti

1. **Creazione sistema protezione**
2. **Configurazione come minorenne**
3. **Disattivazione per maggiorenne**
4. **Configurazione manuale**
5. **Persistenza configurazione**
6. **Integrazione con sistema configurazione**
7. **Integrazione UI**

### Risultati Attesi

```
🚀 Avvio test sistema protezione minori
🧪 Test 1: Creazione sistema di protezione
✅ Stato iniziale corretto
🧪 Test 2: Configurazione come minorenne
✅ Configurazione minorenne corretta
🧪 Test 3: Disattivazione per maggiorenne
✅ Disattivazione per maggiorenne corretta
🧪 Test 4: Configurazione manuale
✅ Configurazione manuale corretta
🧪 Test 5: Persistenza configurazione
✅ Persistenza configurazione corretta
✅ Integrazione configurazione corretta
✅ Moduli UI importati correttamente
✅ Dialog UI creabili
🎉 Tutti i test completati con successo!
✅ Il sistema di protezione minori è pronto per l'uso
```

## 🔒 Sicurezza e Privacy

### Principi di Design

1. **Privacy by Design**: Nessuna data di nascita memorizzata
2. **Minimal Data Collection**: Solo informazioni essenziali
3. **Parental Control**: Controllo completo da parte dei genitori
4. **Transparent Operation**: Tutte le azioni sono loggate e notificate

### Considerazioni di Sicurezza

- **Email Encryption**: Le email possono essere configurate con TLS/SSL
- **Config Protection**: File di configurazione protetti da accesso non autorizzato
- **Audit Trail**: Tutte le operazioni sono loggate per audit
- **Graceful Degradation**: Il sistema funziona anche se l'email non è disponibile

## 🚀 Roadmap Future

### Miglioramenti Pianificati

1. **Integrazione con Identity Manager**: Setup automatico durante creazione identità
2. **Dashboard Genitore**: Interfaccia web per monitoraggio remoto
3. **Notifiche Push**: Alternative all'email per notifiche immediate
4. **Controlli Granulari**: Limitazioni specifiche per contenuti e orari
5. **Multi-Genitore**: Supporto per più email genitori
6. **Backup Automatico**: Backup automatico delle configurazioni

### Estensioni Plugin

- **Time Limits**: Limitazioni orarie di utilizzo
- **Content Filtering**: Filtri per contenuti inappropriati
- **Geo-Fencing**: Limitazioni geografiche
- **Device Management**: Gestione multi-dispositivo

## 📞 Supporto

Per supporto tecnico o domande sul sistema di protezione minori:

1. **Documentazione**: Consulta questa guida
2. **Test**: Esegui i test automatici per verificare il funzionamento
3. **Log**: Controlla i log per messaggi di errore o debug
4. **Community**: Partecipa alle discussioni della community LaboonChat

---

*"La sicurezza dei minori online è una responsabilità condivisa. LaboonChat fornisce gli strumenti, ma l'educazione e la supervisione rimangono fondamentali."*

**Versione**: 1.0  
**Ultima modifica**: 2025-01-27  
**Compatibilità**: LaboonChat v0.4+