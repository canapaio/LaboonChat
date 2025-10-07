# API Reference - LaboonChat2

> **Documentazione completa delle API per sviluppatori**

Questa documentazione fornisce una guida completa alle interfacce e API di LaboonChat2, permettendo agli sviluppatori di estendere l'applicazione e creare plugin personalizzati.

## 📋 Indice

- [Core Interfaces](#core-interfaces)
- [Security Module API](#security-module-api)
- [Messaging Module API](#messaging-module-api)
- [Network Module API](#network-module-api)
- [Interface Module API](#interface-module-api)
- [Plugin System API](#plugin-system-api)
- [Configuration API](#configuration-api)
- [Utility Functions](#utility-functions)
- [Event System](#event-system)
- [Error Handling](#error-handling)

---

## Core Interfaces

### ISecurityModule

Interfaccia base per tutti i moduli di sicurezza.

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple, List

class ISecurityModule(ABC):
    """Interfaccia per moduli di sicurezza."""
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Inizializza il modulo di sicurezza."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Pulisce le risorse del modulo."""
        pass
    
    @abstractmethod
    async def create_identity(self, display_name: str) -> str:
        """Crea una nuova identità crittografica."""
        pass
    
    @abstractmethod
    async def encrypt_message(self, message: str, recipient_id: str) -> bytes:
        """Cripta un messaggio per un destinatario specifico."""
        pass
    
    @abstractmethod
    async def decrypt_message(self, encrypted_data: bytes, sender_id: str) -> str:
        """Decripta un messaggio da un mittente specifico."""
        pass
    
    @abstractmethod
    async def sign_data(self, data: bytes) -> bytes:
        """Firma digitalmente dei dati."""
        pass
    
    @abstractmethod
    async def verify_signature(self, data: bytes, signature: bytes, signer_id: str) -> bool:
        """Verifica una firma digitale."""
        pass
    
    @abstractmethod
    def get_public_key(self) -> str:
        """Restituisce la chiave pubblica dell'identità corrente."""
        pass
    
    @abstractmethod
    async def add_trusted_peer(self, peer_id: str, public_key: str) -> bool:
        """Aggiunge un peer fidato."""
        pass
    
    @abstractmethod
    def get_security_info(self) -> Dict[str, Any]:
        """Restituisce informazioni sulla sicurezza."""
        pass
```

### IMessagingModule

Interfaccia per moduli di messaggistica.

```python
class IMessagingModule(ABC):
    """Interfaccia per moduli di messaggistica."""
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Inizializza il modulo di messaggistica."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Pulisce le risorse del modulo."""
        pass
    
    @abstractmethod
    async def send_message(self, recipient_id: str, message: str, 
                          message_type: str = "text") -> bool:
        """Invia un messaggio a un destinatario."""
        pass
    
    @abstractmethod
    async def broadcast_message(self, message: str, 
                               message_type: str = "text") -> List[str]:
        """Invia un messaggio a tutti i peer connessi."""
        pass
    
    @abstractmethod
    async def get_message_history(self, peer_id: Optional[str] = None, 
                                 limit: int = 100) -> List[Dict[str, Any]]:
        """Recupera la cronologia dei messaggi."""
        pass
    
    @abstractmethod
    async def mark_message_read(self, message_id: str) -> bool:
        """Marca un messaggio come letto."""
        pass
    
    @abstractmethod
    def get_messaging_stats(self) -> Dict[str, Any]:
        """Restituisce statistiche di messaggistica."""
        pass
    
    @abstractmethod
    async def register_message_handler(self, handler: callable) -> None:
        """Registra un handler per messaggi in arrivo."""
        pass
```

### INetworkModule

Interfaccia per moduli di rete.

```python
class INetworkModule(ABC):
    """Interfaccia per moduli di rete."""
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Inizializza il modulo di rete."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Pulisce le risorse del modulo."""
        pass
    
    @abstractmethod
    async def start_listening(self, port: int) -> bool:
        """Inizia ad ascoltare su una porta specifica."""
        pass
    
    @abstractmethod
    async def stop_listening(self) -> None:
        """Ferma l'ascolto sulla rete."""
        pass
    
    @abstractmethod
    async def connect_to_peer(self, peer_address: str, peer_port: int) -> str:
        """Connette a un peer specifico."""
        pass
    
    @abstractmethod
    async def disconnect_from_peer(self, peer_id: str) -> bool:
        """Disconnette da un peer specifico."""
        pass
    
    @abstractmethod
    async def send_data(self, peer_id: str, data: bytes) -> bool:
        """Invia dati a un peer specifico."""
        pass
    
    @abstractmethod
    async def broadcast_data(self, data: bytes) -> List[str]:
        """Invia dati a tutti i peer connessi."""
        pass
    
    @abstractmethod
    def get_connected_peers(self) -> List[Dict[str, Any]]:
        """Restituisce la lista dei peer connessi."""
        pass
    
    @abstractmethod
    def get_network_stats(self) -> Dict[str, Any]:
        """Restituisce statistiche di rete."""
        pass
    
    @abstractmethod
    async def discover_peers(self) -> List[Dict[str, Any]]:
        """Scopre peer nella rete locale."""
        pass
```

### IInterfaceModule

Interfaccia per moduli di interfaccia utente.

```python
class IInterfaceModule(ABC):
    """Interfaccia per moduli di interfaccia utente."""
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Inizializza il modulo di interfaccia."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Pulisce le risorse del modulo."""
        pass
    
    @abstractmethod
    async def start_interface(self) -> bool:
        """Avvia l'interfaccia utente."""
        pass
    
    @abstractmethod
    async def stop_interface(self) -> None:
        """Ferma l'interfaccia utente."""
        pass
    
    @abstractmethod
    async def display_message(self, message: Dict[str, Any]) -> None:
        """Visualizza un messaggio nell'interfaccia."""
        pass
    
    @abstractmethod
    async def display_notification(self, notification: Dict[str, Any]) -> None:
        """Visualizza una notifica."""
        pass
    
    @abstractmethod
    async def update_peer_list(self, peers: List[Dict[str, Any]]) -> None:
        """Aggiorna la lista dei peer nell'interfaccia."""
        pass
    
    @abstractmethod
    async def update_status(self, status: str) -> None:
        """Aggiorna lo status nell'interfaccia."""
        pass
    
    @abstractmethod
    def get_interface_info(self) -> Dict[str, Any]:
        """Restituisce informazioni sull'interfaccia."""
        pass
```

---

## Security Module API

### BasicSecurity

Implementazione base del modulo di sicurezza.

#### Metodi Pubblici

```python
class BasicSecurity(ISecurityModule):
    
    async def generate_key_pair(self, key_size: int = 2048) -> Tuple[str, str]:
        """
        Genera una coppia di chiavi RSA.
        
        Args:
            key_size: Dimensione della chiave in bit
            
        Returns:
            Tuple[str, str]: (chiave_privata, chiave_pubblica)
        """
    
    async def derive_shared_secret(self, peer_public_key: str) -> bytes:
        """
        Deriva un segreto condiviso usando ECDH.
        
        Args:
            peer_public_key: Chiave pubblica del peer
            
        Returns:
            bytes: Segreto condiviso
        """
    
    async def hash_data(self, data: bytes, algorithm: str = "SHA256") -> str:
        """
        Calcola l'hash dei dati.
        
        Args:
            data: Dati da hashare
            algorithm: Algoritmo di hash (SHA256, SHA512, etc.)
            
        Returns:
            str: Hash esadecimale
        """
    
    def get_supported_algorithms(self) -> List[str]:
        """
        Restituisce gli algoritmi supportati.
        
        Returns:
            List[str]: Lista degli algoritmi
        """
```

#### Eventi

```python
# Eventi emessi dal modulo di sicurezza
SECURITY_EVENTS = {
    "identity_created": "Nuova identità creata",
    "peer_added": "Peer fidato aggiunto",
    "encryption_failed": "Fallimento crittografia",
    "signature_verified": "Firma verificata",
    "key_rotated": "Chiave ruotata"
}
```

---

## Messaging Module API

### SimpleMessaging

Implementazione base del modulo di messaggistica.

#### Strutture Dati

```python
@dataclass
class Message:
    """Struttura di un messaggio."""
    id: str
    sender_id: str
    recipient_id: Optional[str]
    content: str
    message_type: str
    timestamp: datetime
    encrypted: bool = False
    signature: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MessageStats:
    """Statistiche di messaggistica."""
    total_sent: int
    total_received: int
    total_encrypted: int
    total_signed: int
    average_size: float
    last_activity: datetime
```

#### Metodi Pubblici

```python
class SimpleMessaging(IMessagingModule):
    
    async def send_file_message(self, recipient_id: str, file_path: str, 
                               description: str = "") -> bool:
        """
        Invia un messaggio con allegato file.
        
        Args:
            recipient_id: ID del destinatario
            file_path: Percorso del file
            description: Descrizione opzionale
            
        Returns:
            bool: True se inviato con successo
        """
    
    async def search_messages(self, query: str, peer_id: Optional[str] = None) -> List[Message]:
        """
        Cerca messaggi per contenuto.
        
        Args:
            query: Testo da cercare
            peer_id: ID del peer (opzionale)
            
        Returns:
            List[Message]: Messaggi trovati
        """
    
    async def export_messages(self, format: str = "json", 
                             peer_id: Optional[str] = None) -> str:
        """
        Esporta messaggi in vari formati.
        
        Args:
            format: Formato di esportazione (json, csv, txt)
            peer_id: ID del peer (opzionale)
            
        Returns:
            str: Dati esportati
        """
```

---

## Network Module API

### SimpleNetwork

Implementazione base del modulo di rete.

#### Strutture Dati

```python
@dataclass
class PeerInfo:
    """Informazioni su un peer."""
    id: str
    address: str
    port: int
    public_key: str
    display_name: str
    last_seen: datetime
    connection_quality: float
    is_trusted: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class NetworkStats:
    """Statistiche di rete."""
    connected_peers: int
    total_connections: int
    bytes_sent: int
    bytes_received: int
    connection_uptime: timedelta
    average_latency: float
```

#### Metodi Pubblici

```python
class SimpleNetwork(INetworkModule):
    
    async def ping_peer(self, peer_id: str) -> float:
        """
        Ping a un peer specifico.
        
        Args:
            peer_id: ID del peer
            
        Returns:
            float: Latenza in millisecondi
        """
    
    async def get_peer_info(self, peer_id: str) -> Optional[PeerInfo]:
        """
        Ottiene informazioni su un peer.
        
        Args:
            peer_id: ID del peer
            
        Returns:
            Optional[PeerInfo]: Informazioni del peer
        """
    
    async def set_bandwidth_limit(self, upload_kbps: int, download_kbps: int) -> None:
        """
        Imposta limiti di banda.
        
        Args:
            upload_kbps: Limite upload in KB/s
            download_kbps: Limite download in KB/s
        """
```

---

## Plugin System API

### ISecondaryPlugin

Interfaccia base per plugin secondari.

```python
class ISecondaryPlugin(ABC):
    """Interfaccia per plugin secondari."""
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Inizializza il plugin."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Pulisce le risorse del plugin."""
        pass
    
    @abstractmethod
    def get_plugin_info(self) -> Dict[str, Any]:
        """Restituisce informazioni sul plugin."""
        pass
    
    @abstractmethod
    async def activate(self) -> bool:
        """Attiva il plugin."""
        pass
    
    @abstractmethod
    async def deactivate(self) -> bool:
        """Disattiva il plugin."""
        pass
    
    @abstractmethod
    async def set_core_modules(self, modules: Dict[str, Any]) -> None:
        """Imposta riferimenti ai moduli core."""
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Restituisce lo status del plugin."""
        pass
    
    @abstractmethod
    async def update_config(self, config: Dict[str, Any]) -> bool:
        """Aggiorna la configurazione del plugin."""
        pass
```

### PluginManager

Gestore dei plugin del sistema.

```python
class PluginManager:
    """Gestore dei plugin."""
    
    async def load_plugin(self, plugin_name: str, plugin_config: Dict[str, Any]) -> bool:
        """
        Carica un plugin.
        
        Args:
            plugin_name: Nome del plugin
            plugin_config: Configurazione del plugin
            
        Returns:
            bool: True se caricato con successo
        """
    
    async def unload_plugin(self, plugin_name: str) -> bool:
        """
        Scarica un plugin.
        
        Args:
            plugin_name: Nome del plugin
            
        Returns:
            bool: True se scaricato con successo
        """
    
    def get_loaded_plugins(self) -> List[str]:
        """
        Restituisce la lista dei plugin caricati.
        
        Returns:
            List[str]: Nomi dei plugin caricati
        """
    
    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """
        Ottiene informazioni su un plugin.
        
        Args:
            plugin_name: Nome del plugin
            
        Returns:
            Optional[Dict[str, Any]]: Informazioni del plugin
        """
    
    async def reload_plugin(self, plugin_name: str) -> bool:
        """
        Ricarica un plugin.
        
        Args:
            plugin_name: Nome del plugin
            
        Returns:
            bool: True se ricaricato con successo
        """
```

---

## Configuration API

### ConfigManager

Gestore della configurazione del sistema.

```python
class ConfigManager:
    """Gestore della configurazione."""
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Ottiene un valore di configurazione.
        
        Args:
            key: Chiave di configurazione (supporta notazione punto)
            default: Valore di default
            
        Returns:
            Any: Valore di configurazione
        """
    
    def set_config(self, key: str, value: Any) -> None:
        """
        Imposta un valore di configurazione.
        
        Args:
            key: Chiave di configurazione
            value: Valore da impostare
        """
    
    def save_config(self) -> bool:
        """
        Salva la configurazione su disco.
        
        Returns:
            bool: True se salvata con successo
        """
    
    def reload_config(self) -> bool:
        """
        Ricarica la configurazione da disco.
        
        Returns:
            bool: True se ricaricata con successo
        """
    
    def get_all_config(self) -> Dict[str, Any]:
        """
        Restituisce tutta la configurazione.
        
        Returns:
            Dict[str, Any]: Configurazione completa
        """
    
    def validate_config(self) -> List[str]:
        """
        Valida la configurazione corrente.
        
        Returns:
            List[str]: Lista di errori di validazione
        """
```

---

## Utility Functions

### Cryptography Utils

```python
from laboon_chat2.utils.crypto import (
    generate_random_bytes,
    derive_key_from_password,
    secure_compare,
    hash_password,
    verify_password
)

def generate_random_bytes(length: int) -> bytes:
    """Genera bytes casuali sicuri."""

def derive_key_from_password(password: str, salt: bytes, 
                           iterations: int = 100000) -> bytes:
    """Deriva una chiave da una password usando PBKDF2."""

def secure_compare(a: bytes, b: bytes) -> bool:
    """Confronto sicuro contro timing attacks."""

def hash_password(password: str) -> Tuple[str, str]:
    """Hash di una password con salt."""

def verify_password(password: str, hashed: str, salt: str) -> bool:
    """Verifica una password contro il suo hash."""
```

### Network Utils

```python
from laboon_chat2.utils.network import (
    is_valid_ip,
    is_port_available,
    get_local_ip,
    scan_local_network
)

def is_valid_ip(ip: str) -> bool:
    """Verifica se un IP è valido."""

def is_port_available(port: int, host: str = "localhost") -> bool:
    """Verifica se una porta è disponibile."""

def get_local_ip() -> str:
    """Ottiene l'IP locale."""

async def scan_local_network(port: int) -> List[str]:
    """Scansiona la rete locale per peer."""
```

### File Utils

```python
from laboon_chat2.utils.file import (
    calculate_file_hash,
    compress_file,
    decompress_file,
    split_file_chunks
)

def calculate_file_hash(file_path: str, algorithm: str = "SHA256") -> str:
    """Calcola l'hash di un file."""

def compress_file(input_path: str, output_path: str, 
                 compression_level: int = 6) -> bool:
    """Comprime un file."""

def decompress_file(input_path: str, output_path: str) -> bool:
    """Decomprime un file."""

def split_file_chunks(file_path: str, chunk_size: int = 1024*1024) -> List[bytes]:
    """Divide un file in chunk."""
```

---

## Event System

### EventEmitter

Sistema di eventi per comunicazione tra moduli.

```python
class EventEmitter:
    """Sistema di eventi."""
    
    def on(self, event: str, handler: callable) -> None:
        """
        Registra un handler per un evento.
        
        Args:
            event: Nome dell'evento
            handler: Funzione handler
        """
    
    def off(self, event: str, handler: callable) -> None:
        """
        Rimuove un handler per un evento.
        
        Args:
            event: Nome dell'evento
            handler: Funzione handler
        """
    
    def emit(self, event: str, *args, **kwargs) -> None:
        """
        Emette un evento.
        
        Args:
            event: Nome dell'evento
            *args: Argomenti posizionali
            **kwargs: Argomenti nominali
        """
    
    def once(self, event: str, handler: callable) -> None:
        """
        Registra un handler che si attiva una sola volta.
        
        Args:
            event: Nome dell'evento
            handler: Funzione handler
        """
```

### Eventi Standard

```python
# Eventi del sistema
SYSTEM_EVENTS = {
    "app_started": "Applicazione avviata",
    "app_stopping": "Applicazione in chiusura",
    "module_loaded": "Modulo caricato",
    "module_unloaded": "Modulo scaricato",
    "plugin_activated": "Plugin attivato",
    "plugin_deactivated": "Plugin disattivato",
    "config_changed": "Configurazione modificata",
    "peer_connected": "Peer connesso",
    "peer_disconnected": "Peer disconnesso",
    "message_received": "Messaggio ricevuto",
    "message_sent": "Messaggio inviato",
    "file_transfer_started": "Transfer file iniziato",
    "file_transfer_completed": "Transfer file completato",
    "error_occurred": "Errore verificato"
}
```

---

## Error Handling

### Eccezioni Personalizzate

```python
class LaboonChatError(Exception):
    """Eccezione base di LaboonChat."""
    pass

class SecurityError(LaboonChatError):
    """Errore di sicurezza."""
    pass

class NetworkError(LaboonChatError):
    """Errore di rete."""
    pass

class MessagingError(LaboonChatError):
    """Errore di messaggistica."""
    pass

class PluginError(LaboonChatError):
    """Errore di plugin."""
    pass

class ConfigurationError(LaboonChatError):
    """Errore di configurazione."""
    pass
```

### Error Handler

```python
class ErrorHandler:
    """Gestore degli errori."""
    
    def handle_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """
        Gestisce un errore.
        
        Args:
            error: Eccezione verificata
            context: Contesto dell'errore
        """
    
    def log_error(self, error: Exception, level: str = "ERROR") -> None:
        """
        Logga un errore.
        
        Args:
            error: Eccezione da loggare
            level: Livello di log
        """
    
    def get_error_stats(self) -> Dict[str, Any]:
        """
        Restituisce statistiche degli errori.
        
        Returns:
            Dict[str, Any]: Statistiche errori
        """
```

---

## Esempi di Utilizzo

### Creazione di un Plugin Semplice

```python
from laboon_chat2.core.interfaces import ISecondaryPlugin
from typing import Dict, Any

class HelloWorldPlugin(ISecondaryPlugin):
    """Plugin di esempio che saluta gli utenti."""
    
    def __init__(self):
        self.active = False
        self.core_modules = {}
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Inizializza il plugin."""
        self.config = config
        return True
    
    async def cleanup(self) -> None:
        """Pulisce le risorse."""
        self.active = False
    
    def get_plugin_info(self) -> Dict[str, Any]:
        """Informazioni del plugin."""
        return {
            "name": "HelloWorld",
            "version": "1.0.0",
            "description": "Plugin di saluto semplice",
            "author": "Developer",
            "category": "utility"
        }
    
    async def activate(self) -> bool:
        """Attiva il plugin."""
        self.active = True
        # Registra handler per messaggi
        if "messaging" in self.core_modules:
            await self.core_modules["messaging"].register_message_handler(
                self.handle_message
            )
        return True
    
    async def deactivate(self) -> bool:
        """Disattiva il plugin."""
        self.active = False
        return True
    
    async def set_core_modules(self, modules: Dict[str, Any]) -> None:
        """Imposta riferimenti ai moduli core."""
        self.core_modules = modules
    
    def get_status(self) -> Dict[str, Any]:
        """Status del plugin."""
        return {
            "active": self.active,
            "greetings_sent": getattr(self, 'greetings_count', 0)
        }
    
    async def update_config(self, config: Dict[str, Any]) -> bool:
        """Aggiorna configurazione."""
        self.config.update(config)
        return True
    
    async def handle_message(self, message: Dict[str, Any]) -> None:
        """Gestisce messaggi in arrivo."""
        if not self.active:
            return
        
        content = message.get("content", "").lower()
        if "hello" in content or "ciao" in content:
            # Invia risposta di saluto
            if "messaging" in self.core_modules:
                greeting = self.config.get("greeting_message", "Hello there!")
                await self.core_modules["messaging"].send_message(
                    message["sender_id"], 
                    greeting
                )
                self.greetings_count = getattr(self, 'greetings_count', 0) + 1
```

### Utilizzo delle API Core

```python
async def example_usage():
    """Esempio di utilizzo delle API core."""
    
    # Inizializzazione moduli
    security = BasicSecurity()
    messaging = SimpleMessaging()
    network = SimpleNetwork()
    
    # Configurazione
    config = {
        "security": {"key_size": 2048},
        "messaging": {"max_message_size": 1024*1024},
        "network": {"port": 9494}
    }
    
    # Inizializzazione
    await security.initialize(config["security"])
    await messaging.initialize(config["messaging"])
    await network.initialize(config["network"])
    
    # Creazione identità
    identity_id = await security.create_identity("MyUser")
    print(f"Created identity: {identity_id}")
    
    # Avvio rete
    await network.start_listening(9494)
    
    # Invio messaggio
    await messaging.send_message("peer_123", "Hello World!")
    
    # Cleanup
    await security.cleanup()
    await messaging.cleanup()
    await network.cleanup()
```

---

## Versioning e Compatibilità

### Versioning Schema

LaboonChat2 utilizza il [Semantic Versioning](https://semver.org/):

- **MAJOR**: Cambiamenti incompatibili nell'API
- **MINOR**: Nuove funzionalità backward-compatible
- **PATCH**: Bug fix backward-compatible

### Compatibilità API

| Versione API | Supportata | Note |
|--------------|------------|------|
| 2.0.x | ✅ Corrente | API stabile |
| 1.9.x | ⚠️ Deprecata | Supporto fino a v2.1 |
| 1.8.x | ❌ Non supportata | Aggiornamento richiesto |

---

## Supporto e Contributi

### Segnalazione Bug

Per segnalare bug nell'API:

1. Verifica che il bug non sia già stato segnalato
2. Crea un issue su GitHub con:
   - Versione di LaboonChat2
   - Codice per riprodurre il bug
   - Comportamento atteso vs attuale
   - Log di errore (se disponibili)

### Richieste di Funzionalità

Per richiedere nuove funzionalità API:

1. Apri una discussione su GitHub
2. Descrivi il caso d'uso
3. Proponi l'interfaccia API
4. Considera l'impatto sulla compatibilità

### Contributi

Per contribuire all'API:

1. Fork del repository
2. Crea branch per la feature
3. Implementa con test completi
4. Aggiorna la documentazione
5. Apri Pull Request

---

*Documentazione aggiornata per LaboonChat2 v2.0.0*
*Ultima modifica: 2025-01-27*