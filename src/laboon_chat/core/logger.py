"""
🐋 LaboonChat Logger
===================

Sistema di logging leggero e sicuro per LaboonChat.
Supporta file, console e rotazione automatica.

🌊 "Ogni log è una goccia nell'oceano della conoscenza" 🐋
"""

import logging
import logging.handlers
import sys
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime


class LaboonFormatter(logging.Formatter):
    """
    🌊 Formatter personalizzato per LaboonChat
    
    Aggiunge emoji e colori per migliore leggibilità.
    """
    
    # Mapping livelli -> emoji
    LEVEL_EMOJI = {
        'DEBUG': '🔍',
        'INFO': '💬',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'CRITICAL': '🚨'
    }
    
    # Colori ANSI per console
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def __init__(self, use_colors: bool = False, use_emoji: bool = True):
        """
        Inizializza formatter
        
        Args:
            use_colors: Usa colori ANSI
            use_emoji: Usa emoji per livelli
        """
        self.use_colors = use_colors
        self.use_emoji = use_emoji
        
        # Formato base
        fmt = '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
        super().__init__(fmt, datefmt='%H:%M:%S')
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Formatta record di log
        
        Args:
            record: Record da formattare
            
        Returns:
            str: Record formattato
        """
        # Copia record per non modificare originale
        record_copy = logging.makeLogRecord(record.__dict__)
        
        # Aggiungi emoji se abilitato
        if self.use_emoji:
            emoji = self.LEVEL_EMOJI.get(record_copy.levelname, '📝')
            record_copy.levelname = f"{emoji} {record_copy.levelname}"
        
        # Formatta base
        formatted = super().format(record_copy)
        
        # Aggiungi colori se abilitato
        if self.use_colors:
            color = self.COLORS.get(record.levelname, '')
            reset = self.COLORS['RESET']
            formatted = f"{color}{formatted}{reset}"
        
        return formatted


class Logger:
    """
    🐋 Logger principale LaboonChat
    
    Gestisce logging su file e console con rotazione automatica.
    """
    
    def __init__(self, config: Optional[Any] = None):
        """
        Inizializza logger
        
        Args:
            config: Configurazione LaboonChat
        """
        self.config = config
        self.logger = logging.getLogger('laboon')
        
        # Evita duplicazione handler
        if self.logger.handlers:
            return
        
        # Configura logger
        self._setup_logger()
    
    def _setup_logger(self):
        """Setup configurazione logger"""
        # Livello di default
        level_name = 'INFO'
        log_file = 'laboon.log'
        max_size_mb = 10
        backup_count = 3
        
        # Carica da configurazione se disponibile
        if self.config:
            level_name = self.config.get('logging.level', 'INFO')
            log_file = self.config.get('logging.file', 'laboon.log')
            max_size_mb = self.config.get('logging.max_size_mb', 10)
            backup_count = self.config.get('logging.backup_count', 3)
        
        # Imposta livello
        level = getattr(logging, level_name.upper(), logging.INFO)
        self.logger.setLevel(level)
        
        # Handler console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        
        # Formatter console con colori ed emoji
        console_formatter = LaboonFormatter(
            use_colors=sys.stdout.isatty(),  # Colori solo se terminale
            use_emoji=True
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # Handler file con rotazione
        try:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.handlers.RotatingFileHandler(
                log_path,
                maxBytes=max_size_mb * 1024 * 1024,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(level)
            
            # Formatter file senza colori
            file_formatter = LaboonFormatter(
                use_colors=False,
                use_emoji=False
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
            
        except Exception as e:
            # Se non riusciamo a creare file handler, continua solo con console
            self.logger.warning(f"Impossibile creare file log {log_file}: {e}")
        
        # Log inizializzazione
        self.logger.info("🐋 Logger LaboonChat inizializzato")
    
    def debug(self, message: str, *args, **kwargs):
        """Log debug"""
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """Log informativo"""
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """Log warning"""
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """Log errore"""
        self.logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """Log critico"""
        self.logger.critical(message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs):
        """Log eccezione con traceback"""
        self.logger.exception(message, *args, **kwargs)
    
    def log_startup(self, component: str, duration: float, details: Optional[Dict[str, Any]] = None):
        """
        Log avvio componente
        
        Args:
            component: Nome componente
            duration: Durata avvio in secondi
            details: Dettagli aggiuntivi
        """
        details_str = ""
        if details:
            details_list = [f"{k}={v}" for k, v in details.items()]
            details_str = f" ({', '.join(details_list)})"
        
        self.info(f"🚀 {component} avviato in {duration:.2f}s{details_str}")
    
    def log_shutdown(self, component: str, duration: Optional[float] = None):
        """
        Log chiusura componente
        
        Args:
            component: Nome componente
            duration: Durata chiusura in secondi
        """
        duration_str = f" in {duration:.2f}s" if duration else ""
        self.info(f"🛑 {component} chiuso{duration_str}")
    
    def log_performance(self, operation: str, duration: float, details: Optional[Dict[str, Any]] = None):
        """
        Log performance operazione
        
        Args:
            operation: Nome operazione
            duration: Durata in secondi
            details: Dettagli aggiuntivi
        """
        details_str = ""
        if details:
            details_list = [f"{k}={v}" for k, v in details.items()]
            details_str = f" ({', '.join(details_list)})"
        
        # Emoji basato su performance
        if duration < 0.1:
            emoji = "⚡"
        elif duration < 1.0:
            emoji = "🏃"
        else:
            emoji = "🐌"
        
        self.debug(f"{emoji} {operation}: {duration:.3f}s{details_str}")
    
    def log_security(self, event: str, details: Optional[Dict[str, Any]] = None):
        """
        Log evento sicurezza
        
        Args:
            event: Descrizione evento
            details: Dettagli aggiuntivi
        """
        details_str = ""
        if details:
            details_list = [f"{k}={v}" for k, v in details.items()]
            details_str = f" ({', '.join(details_list)})"
        
        self.warning(f"🔒 SECURITY: {event}{details_str}")
    
    def get_logger(self) -> logging.Logger:
        """
        Ottiene logger Python standard
        
        Returns:
            logging.Logger: Logger standard
        """
        return self.logger
    
    def set_level(self, level: str):
        """
        Imposta livello logging
        
        Args:
            level: Livello (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        log_level = getattr(logging, level.upper(), logging.INFO)
        self.logger.setLevel(log_level)
        
        # Aggiorna anche handler
        for handler in self.logger.handlers:
            handler.setLevel(log_level)
        
        self.info(f"📊 Livello logging impostato a {level.upper()}")


# Istanza globale logger (lazy loading)
_global_logger: Optional[Logger] = None


def get_logger(config: Optional[Any] = None) -> Logger:
    """
    Ottiene istanza globale logger
    
    Args:
        config: Configurazione (solo al primo accesso)
        
    Returns:
        Logger: Istanza logger
    """
    global _global_logger
    
    if _global_logger is None:
        _global_logger = Logger(config)
    
    return _global_logger


def reset_logger():
    """Reset istanza globale logger (per test)"""
    global _global_logger
    _global_logger = None
    
    # Reset anche logger Python
    logging.getLogger('laboon').handlers.clear()


# Export
__all__ = ['Logger', 'LaboonFormatter', 'get_logger', 'reset_logger']