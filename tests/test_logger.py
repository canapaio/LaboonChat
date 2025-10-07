"""
Test suite per il sistema di logging

Testa LoggerManager, formattatori, filtri e decoratori
per il logging avanzato dell'applicazione.
"""

import pytest
import logging
import tempfile
import shutil
import json
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from io import StringIO
from typing import Dict, Any

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from laboon_chat2.utils.logger import (
    LoggerManager, LogConfig, PluginLogFilter, JSONFormatter,
    ColoredFormatter, TemporaryLogger, log_function_calls,
    log_async_function_calls, setup_logger, get_logger,
    cleanup_loggers
)


@pytest.fixture
def temp_log_dir():
    """Crea una directory temporanea per i log"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def log_config():
    """Configurazione di logging per i test"""
    return LogConfig(
        level="DEBUG",
        file_rotation=True,
        max_file_size="1MB",
        backup_count=3,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        console_output=True,
        json_format=False
    )


@pytest.fixture
def logger_manager(temp_log_dir, log_config):
    """Crea un'istanza di LoggerManager per i test"""
    manager = LoggerManager(str(temp_log_dir), log_config)
    yield manager
    manager.cleanup()


class TestLogConfig:
    """Test per LogConfig dataclass"""
    
    def test_log_config_creation(self):
        """Testa creazione LogConfig"""
        config = LogConfig(
            level="INFO",
            file_rotation=True,
            max_file_size="5MB",
            backup_count=5
        )
        
        assert config.level == "INFO"
        assert config.file_rotation is True
        assert config.max_file_size == "5MB"
        assert config.backup_count == 5
        assert config.format == "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        assert config.console_output is True
        assert config.json_format is False
    
    def test_log_config_defaults(self):
        """Testa valori di default LogConfig"""
        config = LogConfig()
        
        assert config.level == "INFO"
        assert config.file_rotation is True
        assert config.max_file_size == "10MB"
        assert config.backup_count == 5


class TestPluginLogFilter:
    """Test per PluginLogFilter"""
    
    def test_plugin_filter_creation(self):
        """Testa creazione filtro plugin"""
        filter_obj = PluginLogFilter("test_plugin")
        assert filter_obj.plugin_name == "test_plugin"
    
    def test_plugin_filter_accept(self):
        """Testa filtro che accetta record"""
        filter_obj = PluginLogFilter("test_plugin")
        
        # Crea record di log
        record = logging.LogRecord(
            name="test_plugin.module",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        assert filter_obj.filter(record) is True
    
    def test_plugin_filter_reject(self):
        """Testa filtro che rifiuta record"""
        filter_obj = PluginLogFilter("test_plugin")
        
        # Crea record di log da altro plugin
        record = logging.LogRecord(
            name="other_plugin.module",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        assert filter_obj.filter(record) is False


class TestJSONFormatter:
    """Test per JSONFormatter"""
    
    def test_json_formatter_creation(self):
        """Testa creazione JSONFormatter"""
        formatter = JSONFormatter()
        assert formatter is not None
    
    def test_json_formatter_format(self):
        """Testa formattazione JSON"""
        formatter = JSONFormatter()
        
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        
        # Verifica che sia JSON valido
        parsed = json.loads(formatted)
        
        assert parsed["name"] == "test.logger"
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "Test message"
        assert parsed["pathname"] == "/path/to/file.py"
        assert parsed["lineno"] == 42
        assert "timestamp" in parsed
    
    def test_json_formatter_with_exception(self):
        """Testa formattazione JSON con eccezione"""
        formatter = JSONFormatter()
        
        try:
            raise ValueError("Test exception")
        except ValueError:
            exc_info = sys.exc_info()
        
        record = logging.LogRecord(
            name="test.logger",
            level=logging.ERROR,
            pathname="/path/to/file.py",
            lineno=42,
            msg="Error occurred",
            args=(),
            exc_info=exc_info
        )
        
        formatted = formatter.format(record)
        parsed = json.loads(formatted)
        
        assert parsed["level"] == "ERROR"
        assert parsed["message"] == "Error occurred"
        assert "exception" in parsed
        assert "ValueError" in parsed["exception"]


class TestColoredFormatter:
    """Test per ColoredFormatter"""
    
    def test_colored_formatter_creation(self):
        """Testa creazione ColoredFormatter"""
        formatter = ColoredFormatter()
        assert formatter is not None
    
    def test_colored_formatter_format(self):
        """Testa formattazione colorata"""
        formatter = ColoredFormatter()
        
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        
        # Verifica che contenga il messaggio
        assert "Test message" in formatted
        assert "test.logger" in formatted
    
    def test_colored_formatter_different_levels(self):
        """Testa formattazione per diversi livelli"""
        formatter = ColoredFormatter()
        
        levels = [
            (logging.DEBUG, "DEBUG"),
            (logging.INFO, "INFO"),
            (logging.WARNING, "WARNING"),
            (logging.ERROR, "ERROR"),
            (logging.CRITICAL, "CRITICAL")
        ]
        
        for level_num, level_name in levels:
            record = logging.LogRecord(
                name="test.logger",
                level=level_num,
                pathname="",
                lineno=0,
                msg=f"Test {level_name} message",
                args=(),
                exc_info=None
            )
            
            formatted = formatter.format(record)
            assert f"Test {level_name} message" in formatted


class TestLoggerManager:
    """Test per LoggerManager"""
    
    def test_logger_manager_initialization(self, logger_manager):
        """Testa inizializzazione LoggerManager"""
        assert logger_manager.log_dir is not None
        assert logger_manager.config is not None
        assert logger_manager._loggers == {}
    
    def test_setup_main_logger(self, logger_manager):
        """Testa setup del logger principale"""
        logger = logger_manager.setup_main_logger()
        
        assert logger is not None
        assert logger.name == "laboon_chat2"
        assert logger.level == logging.DEBUG
    
    def test_setup_plugin_logger(self, logger_manager):
        """Testa setup del logger per plugin"""
        logger = logger_manager.setup_plugin_logger("test_plugin")
        
        assert logger is not None
        assert logger.name == "laboon_chat2.plugin.test_plugin"
        assert "test_plugin" in logger_manager._loggers
    
    def test_get_logger_existing(self, logger_manager):
        """Testa recupero logger esistente"""
        # Crea logger
        original_logger = logger_manager.setup_plugin_logger("test_plugin")
        
        # Recupera logger esistente
        retrieved_logger = logger_manager.get_logger("test_plugin")
        
        assert retrieved_logger is original_logger
    
    def test_get_logger_new(self, logger_manager):
        """Testa recupero logger non esistente (creazione automatica)"""
        logger = logger_manager.get_logger("new_plugin")
        
        assert logger is not None
        assert logger.name == "laboon_chat2.plugin.new_plugin"
        assert "new_plugin" in logger_manager._loggers
    
    def test_remove_logger(self, logger_manager):
        """Testa rimozione logger"""
        # Crea logger
        logger_manager.setup_plugin_logger("test_plugin")
        assert "test_plugin" in logger_manager._loggers
        
        # Rimuovi logger
        result = logger_manager.remove_logger("test_plugin")
        
        assert result is True
        assert "test_plugin" not in logger_manager._loggers
    
    def test_remove_logger_nonexistent(self, logger_manager):
        """Testa rimozione logger non esistente"""
        result = logger_manager.remove_logger("nonexistent")
        assert result is False
    
    def test_list_loggers(self, logger_manager):
        """Testa elenco logger"""
        # Crea alcuni logger
        logger_manager.setup_plugin_logger("plugin1")
        logger_manager.setup_plugin_logger("plugin2")
        
        loggers = logger_manager.list_loggers()
        
        assert "plugin1" in loggers
        assert "plugin2" in loggers
        assert len(loggers) == 2
    
    def test_update_log_level(self, logger_manager):
        """Testa aggiornamento livello di log"""
        logger = logger_manager.setup_plugin_logger("test_plugin")
        
        # Aggiorna livello
        logger_manager.update_log_level("test_plugin", "ERROR")
        
        assert logger.level == logging.ERROR
    
    def test_update_log_level_nonexistent(self, logger_manager):
        """Testa aggiornamento livello per logger non esistente"""
        result = logger_manager.update_log_level("nonexistent", "ERROR")
        assert result is False
    
    def test_cleanup(self, logger_manager):
        """Testa pulizia logger"""
        # Crea alcuni logger
        logger_manager.setup_plugin_logger("plugin1")
        logger_manager.setup_plugin_logger("plugin2")
        
        assert len(logger_manager._loggers) == 2
        
        # Pulizia
        logger_manager.cleanup()
        
        assert len(logger_manager._loggers) == 0
    
    def test_file_logging(self, logger_manager, temp_log_dir):
        """Testa logging su file"""
        logger = logger_manager.setup_plugin_logger("test_plugin")
        
        # Scrivi log
        logger.info("Test log message")
        
        # Verifica che il file sia stato creato
        log_files = list(temp_log_dir.glob("*.log"))
        assert len(log_files) > 0
        
        # Verifica contenuto
        log_content = log_files[0].read_text()
        assert "Test log message" in log_content
    
    def test_json_logging(self, temp_log_dir):
        """Testa logging in formato JSON"""
        json_config = LogConfig(
            level="INFO",
            json_format=True,
            console_output=False
        )
        
        manager = LoggerManager(str(temp_log_dir), json_config)
        logger = manager.setup_plugin_logger("test_plugin")
        
        # Scrivi log
        logger.info("Test JSON message")
        
        # Verifica formato JSON
        log_files = list(temp_log_dir.glob("*.log"))
        assert len(log_files) > 0
        
        log_content = log_files[0].read_text().strip()
        lines = log_content.split('\n')
        
        # Verifica che sia JSON valido
        for line in lines:
            if line.strip():
                parsed = json.loads(line)
                assert "message" in parsed
                assert "timestamp" in parsed
        
        manager.cleanup()


class TestTemporaryLogger:
    """Test per TemporaryLogger context manager"""
    
    def test_temporary_logger_context(self, temp_log_dir):
        """Testa context manager TemporaryLogger"""
        config = LogConfig(level="DEBUG")
        
        with TemporaryLogger("temp_test", str(temp_log_dir), config) as logger:
            assert logger is not None
            assert logger.name == "temp_test"
            
            # Usa il logger
            logger.info("Temporary log message")
        
        # Verifica che il logger sia stato pulito
        # (Questo test è più concettuale, la pulizia dipende dall'implementazione)
    
    def test_temporary_logger_exception(self, temp_log_dir):
        """Testa TemporaryLogger con eccezione"""
        config = LogConfig(level="DEBUG")
        
        try:
            with TemporaryLogger("temp_test", str(temp_log_dir), config) as logger:
                logger.info("Before exception")
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Il logger dovrebbe essere pulito anche in caso di eccezione


class TestLogDecorators:
    """Test per i decoratori di logging"""
    
    def test_log_function_calls_decorator(self, logger_manager):
        """Testa decoratore log_function_calls"""
        logger = logger_manager.setup_plugin_logger("test_plugin")
        
        @log_function_calls(logger)
        def test_function(x, y):
            return x + y
        
        # Cattura output di log
        with patch.object(logger, 'debug') as mock_debug:
            result = test_function(2, 3)
            
            assert result == 5
            assert mock_debug.call_count >= 2  # Chiamata di ingresso e uscita
    
    def test_log_function_calls_with_exception(self, logger_manager):
        """Testa decoratore con eccezione"""
        logger = logger_manager.setup_plugin_logger("test_plugin")
        
        @log_function_calls(logger)
        def failing_function():
            raise ValueError("Test error")
        
        with patch.object(logger, 'debug'), \
             patch.object(logger, 'error') as mock_error:
            
            with pytest.raises(ValueError):
                failing_function()
            
            # Verifica che l'errore sia stato loggato
            mock_error.assert_called()
    
    @pytest.mark.asyncio
    async def test_log_async_function_calls_decorator(self, logger_manager):
        """Testa decoratore log_async_function_calls"""
        logger = logger_manager.setup_plugin_logger("test_plugin")
        
        @log_async_function_calls(logger)
        async def async_test_function(x, y):
            await asyncio.sleep(0.01)
            return x * y
        
        with patch.object(logger, 'debug') as mock_debug:
            result = await async_test_function(3, 4)
            
            assert result == 12
            assert mock_debug.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_log_async_function_calls_with_exception(self, logger_manager):
        """Testa decoratore async con eccezione"""
        logger = logger_manager.setup_plugin_logger("test_plugin")
        
        @log_async_function_calls(logger)
        async def async_failing_function():
            await asyncio.sleep(0.01)
            raise RuntimeError("Async test error")
        
        with patch.object(logger, 'debug'), \
             patch.object(logger, 'error') as mock_error:
            
            with pytest.raises(RuntimeError):
                await async_failing_function()
            
            mock_error.assert_called()


class TestLoggerUtilityFunctions:
    """Test per le funzioni di utilità del logging"""
    
    def test_setup_logger_function(self, temp_log_dir):
        """Testa funzione setup_logger"""
        config = LogConfig(level="INFO")
        
        logger = setup_logger("test_logger", str(temp_log_dir), config)
        
        assert logger is not None
        assert logger.name == "test_logger"
        assert logger.level == logging.INFO
    
    def test_get_logger_function(self, temp_log_dir):
        """Testa funzione get_logger"""
        config = LogConfig(level="DEBUG")
        
        # Setup manager globale
        with patch('laboon_chat2.utils.logger._global_manager') as mock_manager:
            mock_logger = Mock()
            mock_manager.get_logger.return_value = mock_logger
            
            logger = get_logger("test_plugin")
            
            assert logger is mock_logger
            mock_manager.get_logger.assert_called_with("test_plugin")
    
    def test_cleanup_loggers_function(self):
        """Testa funzione cleanup_loggers"""
        with patch('laboon_chat2.utils.logger._global_manager') as mock_manager:
            cleanup_loggers()
            mock_manager.cleanup.assert_called_once()


class TestLoggerIntegration:
    """Test di integrazione per il sistema di logging"""
    
    def test_complete_logging_workflow(self, temp_log_dir):
        """Testa workflow completo di logging"""
        config = LogConfig(
            level="DEBUG",
            file_rotation=True,
            console_output=True,
            json_format=False
        )
        
        manager = LoggerManager(str(temp_log_dir), config)
        
        try:
            # 1. Setup logger principale
            main_logger = manager.setup_main_logger()
            main_logger.info("Application started")
            
            # 2. Setup logger plugin
            plugin_logger = manager.setup_plugin_logger("security")
            plugin_logger.debug("Security plugin initialized")
            
            # 3. Setup altro plugin
            messaging_logger = manager.setup_plugin_logger("messaging")
            messaging_logger.warning("Connection timeout")
            
            # 4. Test decoratore
            @log_function_calls(plugin_logger)
            def secure_operation(data):
                return f"encrypted_{data}"
            
            result = secure_operation("test_data")
            assert result == "encrypted_test_data"
            
            # 5. Verifica file di log
            log_files = list(temp_log_dir.glob("*.log"))
            assert len(log_files) > 0
            
            # 6. Verifica contenuto
            for log_file in log_files:
                content = log_file.read_text()
                # Almeno uno dei messaggi dovrebbe essere presente
                assert any(msg in content for msg in [
                    "Application started",
                    "Security plugin initialized",
                    "Connection timeout"
                ])
            
            # 7. Test aggiornamento livello
            manager.update_log_level("security", "ERROR")
            plugin_logger.debug("This should not appear")
            plugin_logger.error("This should appear")
            
            # 8. Lista logger
            loggers = manager.list_loggers()
            assert "security" in loggers
            assert "messaging" in loggers
            
        finally:
            manager.cleanup()
    
    @pytest.mark.asyncio
    async def test_concurrent_logging(self, temp_log_dir):
        """Testa logging concorrente"""
        config = LogConfig(level="INFO")
        manager = LoggerManager(str(temp_log_dir), config)
        
        try:
            # Crea logger per diversi plugin
            loggers = []
            for i in range(5):
                logger = manager.setup_plugin_logger(f"plugin_{i}")
                loggers.append(logger)
            
            # Funzione di logging asincrona
            async def log_messages(logger, plugin_id):
                for j in range(10):
                    logger.info(f"Message {j} from plugin {plugin_id}")
                    await asyncio.sleep(0.001)
            
            # Esegui logging concorrente
            tasks = [
                log_messages(logger, i) 
                for i, logger in enumerate(loggers)
            ]
            
            await asyncio.gather(*tasks)
            
            # Verifica che tutti i messaggi siano stati scritti
            log_files = list(temp_log_dir.glob("*.log"))
            assert len(log_files) > 0
            
            total_content = ""
            for log_file in log_files:
                total_content += log_file.read_text()
            
            # Verifica presenza messaggi da tutti i plugin
            for i in range(5):
                assert f"plugin_{i}" in total_content
            
        finally:
            manager.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])