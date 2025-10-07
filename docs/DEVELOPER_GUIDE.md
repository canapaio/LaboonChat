# LaboonChat2 - Guida per Sviluppatori

## Indice

1. [Panoramica Architettura](#panoramica-architettura)
2. [Struttura del Progetto](#struttura-del-progetto)
3. [Moduli Core](#moduli-core)
4. [Sistema Plugin](#sistema-plugin)
5. [Sviluppo Plugin](#sviluppo-plugin)
6. [Testing](#testing)
7. [Configurazione](#configurazione)
8. [Best Practices](#best-practices)
9. [API Reference](#api-reference)
10. [Troubleshooting](#troubleshooting)

## Panoramica Architettura

LaboonChat2 è costruito su un'architettura modulare che separa chiaramente le responsabilità:

### Architettura a Livelli

```
┌─────────────────────────────────────────────────────────┐
│                    Applicazione                         │
├─────────────────────────────────────────────────────────┤
│                  Plugin Secondari                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │
│  │   ChatBot   │ │ FileSharing │ │    Encryption       │ │
│  └─────────────┘ └─────────────┘ └─────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│                    Moduli Core                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │
│  │  Security   │ │ Messaging   │ │     Network         │ │
│  └─────────────┘ └─────────────┘ └─────────────────────┘ │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │
│  │ Interface   │ │   Config    │ │   Plugin Manager    │ │
│  └─────────────┘ └─────────────┘ └─────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│                 Interfacce Base                         │
└─────────────────────────────────────────────────────────┘
```

### Principi Architetturali

1. **Separazione delle Responsabilità**: Ogni modulo ha una responsabilità specifica
2. **Inversione delle Dipendenze**: I moduli dipendono da interfacce, non da implementazioni
3. **Plugin Architecture**: Estensibilità tramite plugin
4. **Configurazione Centralizzata**: Gestione unificata della configurazione
5. **Testing Completo**: Test unitari, integrazione e end-to-end

## Struttura del Progetto

```
LaboonChat2/
├── src/                          # Codice sorgente principale
│   └── laboon_chat2/
│       ├── core/                 # Moduli core
│       │   ├── interfaces.py     # Interfacce base
│       │   ├── config_manager.py # Gestione configurazione
│       │   └── plugin_manager.py # Gestione plugin
│       └── launcher/             # Launcher applicazione
├── plugins/                      # Plugin del sistema
│   ├── core/                     # Plugin core (obbligatori)
│   │   ├── security/            # Moduli sicurezza
│   │   ├── messaging/           # Moduli messaggistica
│   │   ├── network/             # Moduli rete
│   │   └── interface/           # Moduli interfaccia
│   └── secondary/               # Plugin secondari (opzionali)
│       └── advanced_features/   # Funzionalità avanzate
├── tests/                       # Test suite
│   ├── unit/                    # Test unitari
│   ├── integration/             # Test integrazione
│   └── e2e/                     # Test end-to-end
├── docs/                        # Documentazione
├── config/                      # File configurazione
└── data/                        # Dati applicazione
```

## Moduli Core

### 1. Security Module (ISecurityModule)

Gestisce autenticazione, autorizzazione e sicurezza generale.

```python
from laboon_chat2.core.interfaces import ISecurityModule

class MySecurityModule(ISecurityModule):
    async def initialize(self, config: Dict[str, Any]) -> None:
        # Inizializzazione modulo
        pass
    
    async def authenticate_user(self, credentials: Dict[str, Any]) -> bool:
        # Logica autenticazione
        pass
    
    async def check_permission(self, user_id: str, permission: str) -> bool:
        # Controllo permessi
        pass
```

**Responsabilità:**
- Autenticazione utenti
- Gestione permessi
- Audit logging
- Crittografia base

### 2. Messaging Module (IMessagingModule)

Gestisce l'invio, ricezione e storage dei messaggi.

```python
from laboon_chat2.core.interfaces import IMessagingModule

class MyMessagingModule(IMessagingModule):
    async def send_message(self, recipient: str, content: str) -> bool:
        # Invio messaggio
        pass
    
    async def get_message_history(self, peer_id: str) -> List[Dict[str, Any]]:
        # Recupero cronologia
        pass
```

**Responsabilità:**
- Invio/ricezione messaggi
- Storage messaggi
- Cronologia conversazioni
- Notifiche

### 3. Network Module (INetworkModule)

Gestisce connessioni di rete e comunicazione P2P.

```python
from laboon_chat2.core.interfaces import INetworkModule

class MyNetworkModule(INetworkModule):
    async def connect_to_peer(self, peer_id: str, host: str, port: int) -> bool:
        # Connessione a peer
        pass
    
    async def discover_peers(self) -> List[Dict[str, Any]]:
        # Scoperta peer
        pass
```

**Responsabilità:**
- Gestione connessioni P2P
- Discovery peer
- Routing messaggi
- Monitoraggio rete

### 4. Interface Module (IInterfaceModule)

Gestisce l'interfaccia utente e l'interazione.

```python
from laboon_chat2.core.interfaces import IInterfaceModule

class MyInterfaceModule(IInterfaceModule):
    async def render_interface(self) -> Any:
        # Rendering interfaccia
        pass
    
    async def update_display(self, component: str, data: Any) -> None:
        # Aggiornamento display
        pass
```

**Responsabilità:**
- Rendering interfaccia
- Gestione eventi utente
- Aggiornamenti real-time
- Notifiche visive

## Sistema Plugin

### Tipi di Plugin

1. **Plugin Core**: Implementazioni dei moduli base (obbligatori)
2. **Plugin Secondari**: Funzionalità aggiuntive (opzionali)

### Interfaccia Plugin Secondari

```python
from laboon_chat2.core.interfaces import ISecondaryPlugin

class MyPlugin(ISecondaryPlugin):
    async def initialize(self, config: Dict[str, Any]) -> None:
        self.config = config
        # Inizializzazione plugin
    
    async def activate(self) -> None:
        # Attivazione plugin
        self.active = True
    
    async def deactivate(self) -> None:
        # Disattivazione plugin
        self.active = False
    
    async def set_core_module(self, module_type: str, module: Any) -> None:
        # Riferimento a moduli core
        if module_type == "messaging":
            self.messaging_module = module
    
    def get_plugin_info(self) -> Dict[str, Any]:
        return {
            "name": "MyPlugin",
            "version": "1.0.0",
            "description": "Plugin di esempio",
            "author": "Developer"
        }
```

## Sviluppo Plugin

### 1. Creazione Plugin Core

Per creare un nuovo modulo core:

1. **Implementa l'interfaccia appropriata**:
```python
from laboon_chat2.core.interfaces import ISecurityModule

class CustomSecurityModule(ISecurityModule):
    # Implementa tutti i metodi richiesti
    pass
```

2. **Crea factory function**:
```python
def create_custom_security_module() -> ISecurityModule:
    return CustomSecurityModule()
```

3. **Aggiungi configurazione**:
```python
DEFAULT_CONFIG = {
    "data_dir": "./data/security",
    "encryption_algorithm": "aes_256_gcm",
    # altre configurazioni...
}
```

### 2. Creazione Plugin Secondari

Per creare un plugin secondario:

1. **Implementa ISecondaryPlugin**:
```python
from laboon_chat2.core.interfaces import ISecondaryPlugin

class MyFeaturePlugin(ISecondaryPlugin):
    def __init__(self):
        self.active = False
        self.core_modules = {}
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        self.config = config
        # Setup iniziale
    
    # Implementa altri metodi richiesti...
```

2. **Registra il plugin**:
```python
# In __init__.py del package plugin
AVAILABLE_PLUGINS = {
    "my_feature": {
        "class": MyFeaturePlugin,
        "factory": create_my_feature_plugin,
        "config": DEFAULT_CONFIG,
        "description": "Descrizione funzionalità",
        "category": "utility"
    }
}
```

### 3. Best Practices Plugin

1. **Gestione Errori**:
```python
async def risky_operation(self):
    try:
        # Operazione che può fallire
        result = await some_operation()
        return result
    except Exception as e:
        self.logger.error(f"Errore in operazione: {e}")
        # Gestione graceful dell'errore
        return None
```

2. **Configurazione Flessibile**:
```python
def get_config_value(self, key: str, default: Any = None) -> Any:
    return self.config.get(key, default)
```

3. **Logging Strutturato**:
```python
import logging

class MyPlugin:
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def some_method(self):
        self.logger.info("Operazione avviata", extra={"plugin": "MyPlugin"})
```

## Testing

### Struttura Test

```
tests/
├── unit/                    # Test unitari per singoli moduli
│   ├── test_security.py
│   ├── test_messaging.py
│   └── test_network.py
├── integration/             # Test integrazione tra moduli
│   ├── test_module_integration.py
│   └── test_plugin_integration.py
└── e2e/                     # Test end-to-end completi
    ├── test_integration_e2e.py
    └── test_real_world_scenarios.py
```

### Esecuzione Test

```bash
# Test unitari
python -m pytest tests/unit/ -v

# Test integrazione
python -m pytest tests/integration/ -v

# Test end-to-end
python -m pytest tests/e2e/ -v

# Suite completa con copertura
python tests/run_integration_tests.py --save-results

# Test specifici
python -m pytest tests/ -k "test_security" -v
```

### Fixture Comuni

```python
import pytest
from unittest.mock import Mock, AsyncMock

@pytest.fixture
async def mock_security_module():
    module = Mock()
    module.authenticate_user = AsyncMock(return_value=True)
    module.check_permission = AsyncMock(return_value=True)
    return module

@pytest.fixture
async def temp_config():
    return {
        "data_dir": "/tmp/test",
        "log_level": "DEBUG"
    }
```

## Configurazione

### Struttura Configurazione

```json
{
  "app": {
    "name": "LaboonChat2",
    "version": "1.0.0",
    "data_dir": "./data",
    "log_level": "INFO"
  },
  "core_modules": {
    "security": {
      "module": "basic_security",
      "config": {
        "data_dir": "./data/security",
        "encryption_algorithm": "aes_256_gcm"
      }
    },
    "messaging": {
      "module": "simple_p2p_messaging",
      "config": {
        "data_dir": "./data/messaging",
        "max_message_size": 1048576
      }
    }
  },
  "secondary_plugins": {
    "chatbot": {
      "enabled": true,
      "config": {
        "personality": "helpful",
        "auto_respond": true
      }
    }
  }
}
```

### Gestione Configurazione

```python
from laboon_chat2.core.config_manager import ConfigManager

# Caricamento configurazione
config_manager = ConfigManager("config.json")
await config_manager.initialize()

# Accesso configurazione
app_config = config_manager.get_config("app")
security_config = config_manager.get_config("core_modules.security.config")

# Aggiornamento configurazione
await config_manager.update_config("app.log_level", "DEBUG")
```

## Best Practices

### 1. Codice

- **Usa type hints**: Sempre specificare tipi per parametri e return values
- **Async/await**: Usa programmazione asincrona per operazioni I/O
- **Error handling**: Gestisci sempre le eccezioni in modo appropriato
- **Logging**: Usa logging strutturato per debugging

```python
from typing import Dict, List, Optional, Any
import logging

async def process_message(
    self, 
    sender: str, 
    content: str, 
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Processa un messaggio ricevuto.
    
    Args:
        sender: ID del mittente
        content: Contenuto del messaggio
        metadata: Metadati opzionali
    
    Returns:
        True se il messaggio è stato processato con successo
    
    Raises:
        ValueError: Se il contenuto è vuoto
        ProcessingError: Se il processing fallisce
    """
    if not content.strip():
        raise ValueError("Contenuto messaggio vuoto")
    
    try:
        # Logica processing
        result = await self._internal_process(sender, content, metadata)
        self.logger.info(
            "Messaggio processato",
            extra={"sender": sender, "length": len(content)}
        )
        return result
    except Exception as e:
        self.logger.error(
            "Errore processing messaggio",
            extra={"sender": sender, "error": str(e)}
        )
        raise ProcessingError(f"Processing fallito: {e}") from e
```

### 2. Architettura

- **Single Responsibility**: Ogni classe/modulo ha una responsabilità
- **Dependency Injection**: Usa DI per testabilità
- **Interface Segregation**: Interfacce piccole e specifiche
- **Open/Closed**: Aperto per estensione, chiuso per modifica

### 3. Testing

- **Test Pyramid**: Molti test unitari, alcuni integrazione, pochi E2E
- **Arrange-Act-Assert**: Struttura chiara dei test
- **Mock External Dependencies**: Isola unità sotto test
- **Test Edge Cases**: Testa casi limite e errori

```python
@pytest.mark.asyncio
async def test_message_processing_success():
    # Arrange
    processor = MessageProcessor()
    await processor.initialize({"max_length": 1000})
    
    # Act
    result = await processor.process_message("user1", "Hello world")
    
    # Assert
    assert result is True
    assert processor.message_count == 1

@pytest.mark.asyncio
async def test_message_processing_empty_content():
    # Arrange
    processor = MessageProcessor()
    await processor.initialize({})
    
    # Act & Assert
    with pytest.raises(ValueError, match="Contenuto messaggio vuoto"):
        await processor.process_message("user1", "")
```

### 4. Performance

- **Lazy Loading**: Carica risorse solo quando necessario
- **Connection Pooling**: Riusa connessioni di rete
- **Caching**: Cache risultati costosi
- **Batch Operations**: Raggruppa operazioni simili

```python
from functools import lru_cache
import asyncio

class OptimizedModule:
    def __init__(self):
        self._connection_pool = None
        self._cache = {}
    
    @lru_cache(maxsize=128)
    def expensive_computation(self, input_data: str) -> str:
        # Computazione costosa con cache
        return complex_algorithm(input_data)
    
    async def batch_process(self, items: List[str]) -> List[str]:
        # Processa items in batch per efficienza
        tasks = [self.process_item(item) for item in items]
        return await asyncio.gather(*tasks)
```

## API Reference

### Core Interfaces

#### ISecurityModule

```python
class ISecurityModule(ABC):
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None: ...
    
    @abstractmethod
    async def cleanup(self) -> None: ...
    
    @abstractmethod
    def get_module_info(self) -> Dict[str, Any]: ...
    
    @abstractmethod
    async def authenticate_user(self, credentials: Dict[str, Any]) -> bool: ...
    
    @abstractmethod
    async def check_permission(self, user_id: str, permission: str) -> bool: ...
    
    @abstractmethod
    async def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]: ...
```

#### IMessagingModule

```python
class IMessagingModule(ABC):
    @abstractmethod
    async def send_message(self, recipient: str, content: str) -> bool: ...
    
    @abstractmethod
    async def get_message_history(self, peer_id: str) -> List[Dict[str, Any]]: ...
    
    @abstractmethod
    async def set_message_handler(self, handler: Callable) -> None: ...
```

#### INetworkModule

```python
class INetworkModule(ABC):
    @abstractmethod
    async def connect_to_peer(self, peer_id: str, host: str, port: int) -> bool: ...
    
    @abstractmethod
    async def disconnect_from_peer(self, peer_id: str) -> bool: ...
    
    @abstractmethod
    async def discover_peers(self) -> List[Dict[str, Any]]: ...
    
    @abstractmethod
    async def get_connected_peers(self) -> List[Dict[str, Any]]: ...
```

#### IInterfaceModule

```python
class IInterfaceModule(ABC):
    @abstractmethod
    async def render_interface(self) -> Any: ...
    
    @abstractmethod
    async def update_display(self, component: str, data: Any) -> None: ...
    
    @abstractmethod
    async def get_components(self) -> List[Dict[str, Any]]: ...
```

#### ISecondaryPlugin

```python
class ISecondaryPlugin(ABC):
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None: ...
    
    @abstractmethod
    async def cleanup(self) -> None: ...
    
    @abstractmethod
    def get_plugin_info(self) -> Dict[str, Any]: ...
    
    @abstractmethod
    async def activate(self) -> None: ...
    
    @abstractmethod
    async def deactivate(self) -> None: ...
    
    @abstractmethod
    async def set_core_module(self, module_type: str, module: Any) -> None: ...
    
    @abstractmethod
    async def get_status(self) -> Dict[str, Any]: ...
```

## Troubleshooting

### Problemi Comuni

#### 1. Plugin non si carica

**Sintomi**: Plugin non appare nella lista o fallisce inizializzazione

**Soluzioni**:
- Verifica che il plugin implementi correttamente l'interfaccia
- Controlla che sia registrato in `AVAILABLE_PLUGINS`
- Verifica configurazione nel file config
- Controlla log per errori specifici

```python
# Debug plugin loading
import logging
logging.basicConfig(level=logging.DEBUG)

# Verifica registrazione plugin
from plugins.secondary.my_plugin import AVAILABLE_PLUGINS
print(AVAILABLE_PLUGINS)
```

#### 2. Errori di connessione rete

**Sintomi**: Impossibile connettersi ai peer

**Soluzioni**:
- Verifica configurazione porte
- Controlla firewall
- Verifica che il peer sia raggiungibile
- Controlla log di rete

```python
# Test connessione manuale
import asyncio
import socket

async def test_connection(host: str, port: int):
    try:
        reader, writer = await asyncio.open_connection(host, port)
        print(f"Connessione a {host}:{port} riuscita")
        writer.close()
        await writer.wait_closed()
    except Exception as e:
        print(f"Connessione fallita: {e}")

# Test
asyncio.run(test_connection("127.0.0.1", 8080))
```

#### 3. Problemi di performance

**Sintomi**: Applicazione lenta o non responsiva

**Soluzioni**:
- Profila il codice per identificare bottleneck
- Verifica utilizzo memoria
- Controlla operazioni bloccanti
- Ottimizza query database

```python
# Profiling semplice
import time
import functools

def profile_time(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {end - start:.2f} seconds")
        return result
    return wrapper

@profile_time
async def slow_function():
    # Funzione da profilare
    pass
```

### Debug Tools

#### 1. Logging Avanzato

```python
import logging
import json

class StructuredFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "module": record.module,
            "message": record.getMessage(),
        }
        if hasattr(record, 'extra_data'):
            log_entry.update(record.extra_data)
        return json.dumps(log_entry)

# Setup
handler = logging.StreamHandler()
handler.setFormatter(StructuredFormatter())
logger = logging.getLogger("laboon_chat2")
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
```

#### 2. Health Check

```python
async def health_check() -> Dict[str, Any]:
    """Verifica stato salute applicazione"""
    health = {
        "status": "healthy",
        "modules": {},
        "plugins": {},
        "timestamp": time.time()
    }
    
    # Verifica moduli core
    for module_name, module in core_modules.items():
        try:
            info = module.get_module_info()
            health["modules"][module_name] = {
                "status": "healthy",
                "info": info
            }
        except Exception as e:
            health["modules"][module_name] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health["status"] = "degraded"
    
    return health
```

### Supporto

Per supporto aggiuntivo:

1. **Controlla la documentazione**: Questa guida e README
2. **Esamina i test**: I test mostrano esempi di utilizzo
3. **Controlla i log**: Abilita logging DEBUG per dettagli
4. **Esamina il codice**: Il codice è ben documentato
5. **Crea issue**: Segnala bug o richiedi funzionalità

---

*Questa guida è in continua evoluzione. Contribuisci con miglioramenti e correzioni!*