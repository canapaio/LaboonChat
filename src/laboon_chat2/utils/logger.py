"""
Advanced Logging System for LaboonChat v2.0

Provides structured logging with rotation, filtering, and plugin-specific loggers.
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass
import json


@dataclass
class LogConfig:
    """Configurazione logging."""
    name: str
    level: str = "INFO"
    log_file: Optional[str] = None
    console_output: bool = True
    max_size_mb: int = 10
    backup_count: int = 5
    format_string: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"


class PluginLogFilter(logging.Filter):
    """Filtro per log specifici dei plugin."""
    
    def __init__(self, plugin_name: str):
        super().__init__()
        self.plugin_name = plugin_name
    
    def filter(self, record):
        # Aggiungi informazioni plugin al record
        record.plugin_name = self.plugin_name
        return True


class JSONFormatter(logging.Formatter):
    """Formatter JSON per log strutturati."""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Aggiungi informazioni plugin se disponibili
        if hasattr(record, 'plugin_name'):
            log_entry["plugin"] = record.plugin_name
        
        # Aggiungi exception info se presente
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Aggiungi campi extra
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'getMessage', 'exc_info', 
                          'exc_text', 'stack_info']:
                log_entry[key] = value
        
        return json.dumps(log_entry, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """Formatter colorato per output console."""
    
    # Codici colore ANSI
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        # Applica colore al livello
        level_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{level_color}{record.levelname}{self.COLORS['RESET']}"
        
        # Formatta il messaggio
        formatted = super().format(record)
        
        return formatted


class LoggerManager:
    """
    Gestore centralizzato dei logger per LaboonChat v2.0.
    
    Caratteristiche:
    - Logger specifici per plugin
    - Rotazione automatica file
    - Output colorato console
    - Log strutturati JSON
    - Filtri personalizzati
    """
    
    def __init__(self):
        self._loggers: Dict[str, logging.Logger] = {}
        self._handlers: Dict[str, logging.Handler] = {}
        self._default_config = LogConfig(name="laboon_chat2")
    
    def setup_logger(
        self,
        name: str,
        level: Union[str, int] = "INFO",
        log_file: Optional[str] = None,
        console_output: bool = True,
        max_size_mb: int = 10,
        backup_count: int = 5,
        format_string: Optional[str] = None,
        json_format: bool = False,
        plugin_name: Optional[str] = None
    ) -> logging.Logger:
        """
        Configura un logger.
        
        Args:
            name: Nome del logger
            level: Livello di logging
            log_file: File di log (opzionale)
            console_output: Se abilitare output console
            max_size_mb: Dimensione massima file log in MB
            backup_count: Numero di file backup
            format_string: Formato personalizzato
            json_format: Se usare formato JSON
            plugin_name: Nome plugin (per filtri specifici)
            
        Returns:
            logging.Logger: Logger configurato
        """
        # Se logger già esiste, restituiscilo
        if name in self._loggers:
            return self._loggers[name]
        
        # Crea logger
        logger = logging.getLogger(name)
        logger.setLevel(self._get_log_level(level))
        
        # Rimuovi handler esistenti per evitare duplicati
        logger.handlers.clear()
        
        # Formato di default
        if format_string is None:
            format_string = self._default_config.format_string
        
        # Handler console
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self._get_log_level(level))
            
            if json_format:
                console_formatter = JSONFormatter()
            else:
                console_formatter = ColoredFormatter(
                    format_string,
                    datefmt=self._default_config.date_format
                )
            
            console_handler.setFormatter(console_formatter)
            
            # Aggiungi filtro plugin se specificato
            if plugin_name:
                console_handler.addFilter(PluginLogFilter(plugin_name))
            
            logger.addHandler(console_handler)
            self._handlers[f"{name}_console"] = console_handler
        
        # Handler file
        if log_file:
            # Crea directory se non esiste
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Handler con rotazione
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_size_mb * 1024 * 1024,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(self._get_log_level(level))
            
            if json_format:
                file_formatter = JSONFormatter()
            else:
                file_formatter = logging.Formatter(
                    format_string,
                    datefmt=self._default_config.date_format
                )
            
            file_handler.setFormatter(file_formatter)
            
            # Aggiungi filtro plugin se specificato
            if plugin_name:
                file_handler.addFilter(PluginLogFilter(plugin_name))
            
            logger.addHandler(file_handler)
            self._handlers[f"{name}_file"] = file_handler
        
        # Memorizza logger
        self._loggers[name] = logger
        
        return logger
    
    def get_logger(self, name: str) -> Optional[logging.Logger]:
        """
        Ottiene un logger esistente.
        
        Args:
            name: Nome del logger
            
        Returns:
            Optional[logging.Logger]: Logger se esiste
        """
        return self._loggers.get(name)
    
    def setup_plugin_logger(
        self,
        plugin_name: str,
        level: Union[str, int] = "INFO",
        separate_file: bool = True
    ) -> logging.Logger:
        """
        Configura logger specifico per un plugin.
        
        Args:
            plugin_name: Nome del plugin
            level: Livello di logging
            separate_file: Se creare file separato per il plugin
            
        Returns:
            logging.Logger: Logger del plugin
        """
        logger_name = f"plugin.{plugin_name}"
        
        log_file = None
        if separate_file:
            log_file = f"logs/plugins/{plugin_name}.log"
        
        return self.setup_logger(
            name=logger_name,
            level=level,
            log_file=log_file,
            plugin_name=plugin_name
        )
    
    def set_level(self, name: str, level: Union[str, int]) -> bool:
        """
        Cambia livello di un logger esistente.
        
        Args:
            name: Nome del logger
            level: Nuovo livello
            
        Returns:
            bool: True se cambiamento riuscito
        """
        if name not in self._loggers:
            return False
        
        logger = self._loggers[name]
        logger.setLevel(self._get_log_level(level))
        
        # Aggiorna anche gli handler
        for handler in logger.handlers:
            handler.setLevel(self._get_log_level(level))
        
        return True
    
    def add_handler(
        self,
        logger_name: str,
        handler: logging.Handler,
        handler_name: Optional[str] = None
    ) -> bool:
        """
        Aggiunge handler a un logger esistente.
        
        Args:
            logger_name: Nome del logger
            handler: Handler da aggiungere
            handler_name: Nome dell'handler (opzionale)
            
        Returns:
            bool: True se aggiunta riuscita
        """
        if logger_name not in self._loggers:
            return False
        
        logger = self._loggers[logger_name]
        logger.addHandler(handler)
        
        if handler_name:
            self._handlers[handler_name] = handler
        
        return True
    
    def remove_handler(self, logger_name: str, handler_name: str) -> bool:
        """
        Rimuove handler da un logger.
        
        Args:
            logger_name: Nome del logger
            handler_name: Nome dell'handler
            
        Returns:
            bool: True se rimozione riuscita
        """
        if logger_name not in self._loggers or handler_name not in self._handlers:
            return False
        
        logger = self._loggers[logger_name]
        handler = self._handlers[handler_name]
        
        logger.removeHandler(handler)
        handler.close()
        
        del self._handlers[handler_name]
        
        return True
    
    def cleanup(self) -> None:
        """Cleanup di tutti i logger e handler."""
        # Chiudi tutti gli handler
        for handler in self._handlers.values():
            handler.close()
        
        # Pulisci strutture
        self._handlers.clear()
        self._loggers.clear()
    
    def get_log_stats(self) -> Dict[str, Any]:
        """
        Ottiene statistiche sui logger.
        
        Returns:
            Dict: Statistiche logging
        """
        stats = {
            "loggers_count": len(self._loggers),
            "handlers_count": len(self._handlers),
            "loggers": {}
        }
        
        for name, logger in self._loggers.items():
            stats["loggers"][name] = {
                "level": logging.getLevelName(logger.level),
                "handlers_count": len(logger.handlers),
                "effective_level": logging.getLevelName(logger.getEffectiveLevel())
            }
        
        return stats
    
    # === Private Methods ===
    
    def _get_log_level(self, level: Union[str, int]) -> int:
        """Converte livello in intero."""
        if isinstance(level, str):
            return getattr(logging, level.upper(), logging.INFO)
        return level


# === Global Logger Manager ===
_logger_manager = LoggerManager()


# === Convenience Functions ===

def setup_logger(
    name: str,
    level: Union[str, int] = "INFO",
    log_file: Optional[str] = None,
    console_output: bool = True,
    max_size_mb: int = 10,
    backup_count: int = 5,
    format_string: Optional[str] = None,
    json_format: bool = False,
    plugin_name: Optional[str] = None
) -> logging.Logger:
    """
    Configura un logger usando il manager globale.
    
    Args:
        name: Nome del logger
        level: Livello di logging
        log_file: File di log (opzionale)
        console_output: Se abilitare output console
        max_size_mb: Dimensione massima file log in MB
        backup_count: Numero di file backup
        format_string: Formato personalizzato
        json_format: Se usare formato JSON
        plugin_name: Nome plugin (per filtri specifici)
        
    Returns:
        logging.Logger: Logger configurato
    """
    return _logger_manager.setup_logger(
        name=name,
        level=level,
        log_file=log_file,
        console_output=console_output,
        max_size_mb=max_size_mb,
        backup_count=backup_count,
        format_string=format_string,
        json_format=json_format,
        plugin_name=plugin_name
    )


def setup_plugin_logger(
    plugin_name: str,
    level: Union[str, int] = "INFO",
    separate_file: bool = True
) -> logging.Logger:
    """
    Configura logger per un plugin.
    
    Args:
        plugin_name: Nome del plugin
        level: Livello di logging
        separate_file: Se creare file separato
        
    Returns:
        logging.Logger: Logger del plugin
    """
    return _logger_manager.setup_plugin_logger(
        plugin_name=plugin_name,
        level=level,
        separate_file=separate_file
    )


def get_logger(name: str) -> Optional[logging.Logger]:
    """
    Ottiene un logger esistente.
    
    Args:
        name: Nome del logger
        
    Returns:
        Optional[logging.Logger]: Logger se esiste
    """
    return _logger_manager.get_logger(name)


def set_log_level(name: str, level: Union[str, int]) -> bool:
    """
    Cambia livello di un logger.
    
    Args:
        name: Nome del logger
        level: Nuovo livello
        
    Returns:
        bool: True se cambiamento riuscito
    """
    return _logger_manager.set_level(name, level)


def cleanup_loggers() -> None:
    """Cleanup di tutti i logger."""
    _logger_manager.cleanup()


def get_logging_stats() -> Dict[str, Any]:
    """
    Ottiene statistiche logging.
    
    Returns:
        Dict: Statistiche
    """
    return _logger_manager.get_log_stats()


# === Context Manager per Logging Temporaneo ===

class TemporaryLogger:
    """Context manager per logger temporaneo."""
    
    def __init__(
        self,
        name: str,
        level: str = "INFO",
        log_file: Optional[str] = None
    ):
        self.name = name
        self.level = level
        self.log_file = log_file
        self.logger: Optional[logging.Logger] = None
    
    def __enter__(self) -> logging.Logger:
        self.logger = setup_logger(
            name=self.name,
            level=self.level,
            log_file=self.log_file
        )
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.logger:
            # Rimuovi handler per cleanup
            for handler in self.logger.handlers[:]:
                self.logger.removeHandler(handler)
                handler.close()


# === Decoratori per Logging ===

def log_function_calls(logger_name: str = "function_calls"):
    """
    Decoratore per loggare chiamate a funzioni.
    
    Args:
        logger_name: Nome del logger da usare
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger(logger_name) or setup_logger(logger_name)
            
            logger.debug(f"Chiamata {func.__name__} con args={args}, kwargs={kwargs}")
            
            try:
                result = func(*args, **kwargs)
                logger.debug(f"Risultato {func.__name__}: {result}")
                return result
            except Exception as e:
                logger.error(f"Errore in {func.__name__}: {e}")
                raise
        
        return wrapper
    return decorator


def log_async_function_calls(logger_name: str = "async_function_calls"):
    """
    Decoratore per loggare chiamate a funzioni async.
    
    Args:
        logger_name: Nome del logger da usare
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            logger = get_logger(logger_name) or setup_logger(logger_name)
            
            logger.debug(f"Chiamata async {func.__name__} con args={args}, kwargs={kwargs}")
            
            try:
                result = await func(*args, **kwargs)
                logger.debug(f"Risultato async {func.__name__}: {result}")
                return result
            except Exception as e:
                logger.error(f"Errore in async {func.__name__}: {e}")
                raise
        
        return wrapper
    return decorator