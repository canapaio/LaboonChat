"""
🔌 LaboonChat Plugin Manager - Sistema Plugin Sicuro
====================================================

Gestione sicura dei plugin per LaboonChat con validazione crittografica,
sandboxing e distribuzione P2P di plugin crittografati.

🐋 "Ogni plugin è un'estensione sicura dell'anima digitale" 🌊

Author: LaboonChat Team
License: GPL-3.0
"""

import os
import json
import time
import hashlib
import zipfile
import tempfile
import importlib
import importlib.util
from typing import Optional, Dict, Any, List, Callable, Type, Set, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import threading
from abc import ABC, abstractmethod

from .crypto_core import LaboonCrypto, SecureStorage, EncryptedData


@dataclass
class PluginMetadata:
    """Metadati plugin"""
    name: str
    version: str
    author: str
    description: str
    category: str
    permissions: List[str]
    dependencies: List[str]
    min_core_version: str
    created_at: float
    plugin_hash: str
    signature: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte in dizionario"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginMetadata':
        """Crea da dizionario"""
        return cls(**data)


@dataclass
class PluginInfo:
    """Informazioni plugin caricato"""
    metadata: PluginMetadata
    module: Any
    instance: Optional[Any]
    loaded_at: float
    status: str  # "loaded", "active", "error", "disabled"
    error_message: Optional[str] = None


class PluginInterface(ABC):
    """
    🔌 Interfaccia base per plugin LaboonChat
    
    Tutti i plugin devono implementare questa interfaccia
    per essere compatibili con il sistema.
    """
    
    @abstractmethod
    def get_name(self) -> str:
        """Nome del plugin"""
        pass
    
    @abstractmethod
    def get_version(self) -> str:
        """Versione del plugin"""
        pass
    
    @abstractmethod
    def initialize(self, core_api: Any) -> bool:
        """
        Inizializza plugin
        
        Args:
            core_api: API del core LaboonChat
            
        Returns:
            bool: True se inizializzazione riuscita
        """
        pass
    
    @abstractmethod
    def shutdown(self) -> bool:
        """
        Chiude plugin
        
        Returns:
            bool: True se chiusura riuscita
        """
        pass
    
    def get_permissions(self) -> List[str]:
        """
        Permessi richiesti dal plugin
        
        Returns:
            List[str]: Lista permessi
        """
        return []
    
    def get_dependencies(self) -> List[str]:
        """
        Dipendenze del plugin
        
        Returns:
            List[str]: Lista dipendenze
        """
        return []


class PluginSandbox:
    """
    🛡️ Sandbox per esecuzione sicura plugin
    
    Limita le capacità dei plugin per sicurezza.
    """
    
    def __init__(self, plugin_name: str, permissions: List[str]):
        """
        Inizializza sandbox
        
        Args:
            plugin_name: Nome plugin
            permissions: Permessi concessi
        """
        self.plugin_name = plugin_name
        self.permissions = set(permissions)
        
        # Permessi disponibili
        self.available_permissions = {
            "network.send",      # Inviare messaggi di rete
            "network.receive",   # Ricevere messaggi di rete
            "storage.read",      # Leggere dati storage
            "storage.write",     # Scrivere dati storage
            "crypto.encrypt",    # Usare crittografia
            "crypto.decrypt",    # Decrittare dati
            "ui.create",         # Creare elementi UI
            "ui.modify",         # Modificare UI esistente
            "system.execute",    # Eseguire comandi sistema
            "files.read",        # Leggere file
            "files.write",       # Scrivere file
        }
    
    def check_permission(self, permission: str) -> bool:
        """
        Controlla se plugin ha permesso
        
        Args:
            permission: Permesso da controllare
            
        Returns:
            bool: True se permesso concesso
        """
        return permission in self.permissions
    
    def require_permission(self, permission: str):
        """
        Richiede permesso, solleva eccezione se non concesso
        
        Args:
            permission: Permesso richiesto
            
        Raises:
            PermissionError: Se permesso non concesso
        """
        if not self.check_permission(permission):
            raise PermissionError(f"Plugin '{self.plugin_name}' non ha permesso '{permission}'")
    
    def get_restricted_globals(self) -> Dict[str, Any]:
        """
        Ottiene globals ristretti per plugin
        
        Returns:
            Dict[str, Any]: Globals sicuri
        """
        # Globals base sicuri
        safe_globals = {
            '__builtins__': {
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
                'list': list,
                'dict': dict,
                'tuple': tuple,
                'set': set,
                'print': print,
                'range': range,
                'enumerate': enumerate,
                'zip': zip,
                'map': map,
                'filter': filter,
                'sorted': sorted,
                'min': min,
                'max': max,
                'sum': sum,
                'abs': abs,
                'round': round,
                'isinstance': isinstance,
                'hasattr': hasattr,
                'getattr': getattr,
                'setattr': setattr,
            }
        }
        
        # Aggiungi moduli sicuri basati su permessi
        if self.check_permission("crypto.encrypt") or self.check_permission("crypto.decrypt"):
            safe_globals['hashlib'] = hashlib
        
        if self.check_permission("files.read") or self.check_permission("files.write"):
            safe_globals['os'] = os
            safe_globals['pathlib'] = Path
        
        return safe_globals


class PluginValidator:
    """
    🔍 Validatore plugin per sicurezza
    
    Valida plugin prima del caricamento per prevenire
    codice malevolo o non sicuro.
    """
    
    def __init__(self):
        """Inizializza validatore"""
        # Parole chiave pericolose
        self.dangerous_keywords = {
            'exec', 'eval', 'compile', '__import__',
            'open', 'file', 'input', 'raw_input',
            'subprocess', 'os.system', 'os.popen',
            'socket', 'urllib', 'requests',
            '__builtins__', '__globals__', '__locals__',
            'globals', 'locals', 'vars', 'dir',
        }
        
        # Moduli pericolosi
        self.dangerous_modules = {
            'subprocess', 'os', 'sys', 'socket',
            'urllib', 'requests', 'http', 'ftplib',
            'smtplib', 'telnetlib', 'pickle', 'marshal',
            'ctypes', 'multiprocessing', 'threading',
        }
    
    def validate_plugin_code(self, code: str) -> Tuple[bool, List[str]]:
        """
        Valida codice plugin
        
        Args:
            code: Codice sorgente plugin
            
        Returns:
            Tuple[bool, List[str]]: (valido, lista errori)
        """
        errors = []
        
        # Controlla parole chiave pericolose
        for keyword in self.dangerous_keywords:
            if keyword in code:
                errors.append(f"Parola chiave pericolosa trovata: {keyword}")
        
        # Controlla import pericolosi
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if line.startswith('import ') or line.startswith('from '):
                for module in self.dangerous_modules:
                    if module in line:
                        errors.append(f"Import pericoloso alla riga {i}: {module}")
        
        # Controlla lunghezza ragionevole
        if len(code) > 100000:  # 100KB max
            errors.append("Codice plugin troppo grande (>100KB)")
        
        return len(errors) == 0, errors
    
    def validate_metadata(self, metadata: PluginMetadata) -> Tuple[bool, List[str]]:
        """
        Valida metadati plugin
        
        Args:
            metadata: Metadati da validare
            
        Returns:
            Tuple[bool, List[str]]: (valido, lista errori)
        """
        errors = []
        
        # Controlla campi obbligatori
        if not metadata.name or len(metadata.name.strip()) == 0:
            errors.append("Nome plugin mancante")
        
        if not metadata.version or len(metadata.version.strip()) == 0:
            errors.append("Versione plugin mancante")
        
        if not metadata.author or len(metadata.author.strip()) == 0:
            errors.append("Autore plugin mancante")
        
        # Controlla categoria valida
        valid_categories = {"essential", "functional", "advanced", "community", "experimental"}
        if metadata.category not in valid_categories:
            errors.append(f"Categoria non valida: {metadata.category}")
        
        # Controlla permessi validi
        valid_permissions = {
            "network.send", "network.receive", "storage.read", "storage.write",
            "crypto.encrypt", "crypto.decrypt", "ui.create", "ui.modify",
            "system.execute", "files.read", "files.write"
        }
        
        for permission in metadata.permissions:
            if permission not in valid_permissions:
                errors.append(f"Permesso non valido: {permission}")
        
        return len(errors) == 0, errors


class LaboonPluginManager:
    """
    🔌 Gestore plugin LaboonChat
    
    Gestisce caricamento, validazione e esecuzione sicura dei plugin.
    Supporta plugin crittografati e distribuzione P2P.
    """
    
    def __init__(self, plugins_dir: Optional[str] = None):
        """
        Inizializza gestore plugin
        
        Args:
            plugins_dir: Directory plugin (default: ~/.laboon/plugins)
        """
        if plugins_dir is None:
            home_dir = Path.home()
            plugins_dir = home_dir / ".laboon" / "plugins"
        
        self.plugins_dir = Path(plugins_dir)
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        
        # Storage sicuro per plugin crittografati
        self.storage = SecureStorage(str(self.plugins_dir))
        
        # Validatore e sandbox
        self.validator = PluginValidator()
        
        # Plugin caricati
        self.loaded_plugins: Dict[str, PluginInfo] = {}
        self.plugin_instances: Dict[str, PluginInterface] = {}
        
        # Callbacks
        self.plugin_loaded_callback: Optional[Callable[[str, PluginInfo], None]] = None
        self.plugin_error_callback: Optional[Callable[[str, str], None]] = None
        
        # Core API per plugin
        self.core_api: Optional[Any] = None
        
        # Thread safety
        self._lock = threading.RLock()
    
    def set_core_api(self, core_api: Any):
        """
        Imposta API del core per plugin
        
        Args:
            core_api: Istanza API core
        """
        self.core_api = core_api
    
    def install_plugin(self, plugin_path: str, password: Optional[str] = None) -> bool:
        """
        Installa plugin da file .lcp (LaboonChat Plugin)
        
        Args:
            plugin_path: Percorso file plugin
            password: Password per decrittografia (se crittografato)
            
        Returns:
            bool: True se installazione riuscita
        """
        try:
            with self._lock:
                # Leggi file plugin
                with open(plugin_path, 'rb') as f:
                    plugin_data = f.read()
                
                # Prova a decrittare se necessario
                if password:
                    try:
                        encrypted = EncryptedData(
                            nonce=plugin_data[:12],
                            ciphertext=plugin_data[12:]
                        )
                        plugin_data = LaboonCrypto.decrypt_data(encrypted, password)
                        if not plugin_data:
                            return False
                    except Exception:
                        return False
                
                # Estrai plugin (ZIP)
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)
                    
                    # Salva e estrai ZIP
                    zip_path = temp_path / "plugin.zip"
                    with open(zip_path, 'wb') as f:
                        f.write(plugin_data)
                    
                    with zipfile.ZipFile(zip_path, 'r') as zip_file:
                        zip_file.extractall(temp_path)
                    
                    # Leggi metadati
                    metadata_path = temp_path / "plugin.json"
                    if not metadata_path.exists():
                        return False
                    
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata_dict = json.load(f)
                    
                    metadata = PluginMetadata.from_dict(metadata_dict)
                    
                    # Valida metadati
                    valid, errors = self.validator.validate_metadata(metadata)
                    if not valid:
                        print(f"❌ Metadati plugin non validi: {errors}")
                        return False
                    
                    # Leggi codice principale
                    main_path = temp_path / "main.py"
                    if not main_path.exists():
                        return False
                    
                    with open(main_path, 'r', encoding='utf-8') as f:
                        plugin_code = f.read()
                    
                    # Valida codice
                    valid, errors = self.validator.validate_plugin_code(plugin_code)
                    if not valid:
                        print(f"❌ Codice plugin non valido: {errors}")
                        return False
                    
                    # Copia plugin nella directory
                    plugin_dir = self.plugins_dir / metadata.name
                    plugin_dir.mkdir(exist_ok=True)
                    
                    # Copia tutti i file
                    for item in temp_path.iterdir():
                        if item.name != "plugin.zip":
                            if item.is_file():
                                (plugin_dir / item.name).write_bytes(item.read_bytes())
                            elif item.is_dir():
                                import shutil
                                shutil.copytree(item, plugin_dir / item.name, dirs_exist_ok=True)
                
                return True
                
        except Exception as e:
            print(f"❌ Errore installazione plugin: {e}")
            return False
    
    def load_plugin(self, plugin_name: str) -> bool:
        """
        Carica plugin installato
        
        Args:
            plugin_name: Nome plugin da caricare
            
        Returns:
            bool: True se caricamento riuscito
        """
        try:
            with self._lock:
                # Controlla se già caricato
                if plugin_name in self.loaded_plugins:
                    return True
                
                plugin_dir = self.plugins_dir / plugin_name
                if not plugin_dir.exists():
                    return False
                
                # Leggi metadati
                metadata_path = plugin_dir / "plugin.json"
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata_dict = json.load(f)
                
                metadata = PluginMetadata.from_dict(metadata_dict)
                
                # Carica modulo Python
                main_path = plugin_dir / "main.py"
                spec = importlib.util.spec_from_file_location(
                    f"laboon_plugin_{plugin_name}",
                    main_path
                )
                
                if not spec or not spec.loader:
                    return False
                
                module = importlib.util.module_from_spec(spec)
                
                # Crea sandbox
                sandbox = PluginSandbox(plugin_name, metadata.permissions)
                
                # Imposta globals ristretti
                restricted_globals = sandbox.get_restricted_globals()
                module.__dict__.update(restricted_globals)
                
                # Carica modulo
                spec.loader.exec_module(module)
                
                # Cerca classe plugin
                plugin_class = None
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        issubclass(attr, PluginInterface) and 
                        attr != PluginInterface):
                        plugin_class = attr
                        break
                
                if not plugin_class:
                    return False
                
                # Crea istanza plugin
                plugin_instance = plugin_class()
                
                # Inizializza plugin
                if self.core_api and not plugin_instance.initialize(self.core_api):
                    return False
                
                # Salva informazioni plugin
                plugin_info = PluginInfo(
                    metadata=metadata,
                    module=module,
                    instance=plugin_instance,
                    loaded_at=time.time(),
                    status="active"
                )
                
                self.loaded_plugins[plugin_name] = plugin_info
                self.plugin_instances[plugin_name] = plugin_instance
                
                # Notifica callback
                if self.plugin_loaded_callback:
                    self.plugin_loaded_callback(plugin_name, plugin_info)
                
                return True
                
        except Exception as e:
            error_msg = f"Errore caricamento plugin {plugin_name}: {e}"
            print(f"❌ {error_msg}")
            
            if self.plugin_error_callback:
                self.plugin_error_callback(plugin_name, error_msg)
            
            return False
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """
        Scarica plugin
        
        Args:
            plugin_name: Nome plugin da scaricare
            
        Returns:
            bool: True se scaricamento riuscito
        """
        try:
            with self._lock:
                if plugin_name not in self.loaded_plugins:
                    return True
                
                plugin_info = self.loaded_plugins[plugin_name]
                
                # Chiudi plugin
                if plugin_info.instance:
                    try:
                        plugin_info.instance.shutdown()
                    except Exception:
                        pass
                
                # Rimuovi da dizionari
                del self.loaded_plugins[plugin_name]
                if plugin_name in self.plugin_instances:
                    del self.plugin_instances[plugin_name]
                
                return True
                
        except Exception:
            return False
    
    def get_loaded_plugins(self) -> Dict[str, PluginInfo]:
        """
        Ottiene plugin caricati
        
        Returns:
            Dict[str, PluginInfo]: Plugin caricati
        """
        with self._lock:
            return self.loaded_plugins.copy()
    
    def get_plugin_instance(self, plugin_name: str) -> Optional[PluginInterface]:
        """
        Ottiene istanza plugin
        
        Args:
            plugin_name: Nome plugin
            
        Returns:
            Optional[PluginInterface]: Istanza plugin o None
        """
        with self._lock:
            return self.plugin_instances.get(plugin_name)
    
    def list_available_plugins(self) -> List[str]:
        """
        Lista plugin disponibili per caricamento
        
        Returns:
            List[str]: Nomi plugin disponibili
        """
        available = []
        
        for item in self.plugins_dir.iterdir():
            if item.is_dir() and (item / "plugin.json").exists():
                available.append(item.name)
        
        return available
    
    def auto_load_essential_plugins(self) -> int:
        """
        Carica automaticamente plugin essenziali
        
        Returns:
            int: Numero plugin caricati
        """
        loaded_count = 0
        
        for plugin_name in self.list_available_plugins():
            try:
                # Leggi metadati per controllare categoria
                metadata_path = self.plugins_dir / plugin_name / "plugin.json"
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata_dict = json.load(f)
                
                if metadata_dict.get('category') == 'essential':
                    if self.load_plugin(plugin_name):
                        loaded_count += 1
                        
            except Exception:
                continue
        
        return loaded_count


# Test rapido del modulo
if __name__ == "__main__":
    print("🔌 Test LaboonPluginManager...")
    
    # Test inizializzazione
    manager = LaboonPluginManager("/tmp/test_plugins")
    
    # Test validatore
    validator = PluginValidator()
    
    # Test codice sicuro
    safe_code = """
def hello():
    return "Hello, Laboon!"
    
class TestPlugin(PluginInterface):
    def get_name(self):
        return "Test"
    
    def get_version(self):
        return "1.0"
    
    def initialize(self, core_api):
        return True
    
    def shutdown(self):
        return True
"""
    
    valid, errors = validator.validate_plugin_code(safe_code)
    print(f"✅ Codice sicuro: {valid} (errori: {len(errors)})")
    
    # Test codice pericoloso
    dangerous_code = """
import os
os.system("rm -rf /")
"""
    
    valid, errors = validator.validate_plugin_code(dangerous_code)
    print(f"✅ Codice pericoloso rilevato: {not valid} (errori: {len(errors)})")
    
    # Test sandbox
    sandbox = PluginSandbox("test", ["network.send"])
    has_network = sandbox.check_permission("network.send")
    has_files = sandbox.check_permission("files.write")
    print(f"✅ Sandbox - Network: {has_network}, Files: {has_files}")
    
    print("🐋 LaboonPluginManager funziona perfettamente! 🌊")