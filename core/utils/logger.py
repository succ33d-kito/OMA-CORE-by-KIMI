"""
OMA-CORE Logger Module
Guarda errores, warnings y eventos importantes en archivos de log
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
import traceback


class OMACoreLogger:
    """
    Logger centralizado para OMA-CORE.
    
    Crea logs en:
    - logs/oma-core.log (INFO y superior)
    - logs/oma-core-errors.log (ERROR y superior)
    - logs/oma-core-debug.log (DEBUG y superior)
    """
    
    def __init__(self, log_dir: str = "logs", app_name: str = "oma-core"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.app_name = app_name
        
        # Crear loggers
        self.logger = logging.getLogger(app_name)
        self.logger.setLevel(logging.DEBUG)
        
        # Evitar duplicados si ya hay handlers
        if self.logger.handlers:
            return
        
        # Formato
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # Handler 1: INFO+ -> oma-core.log
        info_handler = logging.FileHandler(self.log_dir / f"{app_name}.log")
        info_handler.setLevel(logging.INFO)
        info_handler.setFormatter(formatter)
        self.logger.addHandler(info_handler)
        
        # Handler 2: ERROR+ -> oma-core-errors.log
        error_handler = logging.FileHandler(self.log_dir / f"{app_name}-errors.log")
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        self.logger.addHandler(error_handler)
        
        # Handler 3: DEBUG+ -> oma-core-debug.log
        debug_handler = logging.FileHandler(self.log_dir / f"{app_name}-debug.log")
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(formatter)
        self.logger.addHandler(debug_handler)
        
        # Handler 4: Console -> stdout
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def info(self, message: str):
        """Log nivel INFO."""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Log nivel WARNING."""
        self.logger.warning(message)
    
    def error(self, message: str, exception: Optional[Exception] = None):
        """Log nivel ERROR. Si hay excepcion, guarda el traceback."""
        if exception:
            tb = traceback.format_exception(type(exception), exception, exception.__traceback__)
            message = f"{message}\nException: {str(exception)}\nTraceback:\n{''.join(tb)}"
        self.logger.error(message)
    
    def critical(self, message: str, exception: Optional[Exception] = None):
        """Log nivel CRITICAL. Para errores graves del sistema."""
        if exception:
            tb = traceback.format_exception(type(exception), exception, exception.__traceback__)
            message = f"{message}\nException: {str(exception)}\nTraceback:\n{''.join(tb)}"
        self.logger.critical(message)
    
    def debug(self, message: str):
        """Log nivel DEBUG. Para desarrollo."""
        self.logger.debug(message)
    
    def log_pipeline_error(self, event_source: str, event_id: str, error: Exception, context: str = ""):
        """Log especifico para errores del pipeline."""
        self.error(
            f"PIPELINE ERROR | Source: {event_source} | Event: {event_id} | Context: {context}",
            exception=error
        )
    
    def log_backtest_result(self, result: dict):
        """Log de resultados de backtest."""
        self.info(f"BACKTEST | Trades: {result.get('total_trades')} | PnL: {result.get('total_pnl')} | WR: {result.get('win_rate')}")
    
    def log_opportunity(self, opp_type: str, priority: str, score: float, source: str):
        """Log de oportunidades generadas."""
        self.info(f"OPPORTUNITY | {opp_type} | {priority} | Score: {score:.1f} | Source: {source}")
    
    def get_recent_errors(self, n: int = 10) -> list:
        """Obtiene los N errores mas recientes del log."""
        error_file = self.log_dir / f"{self.app_name}-errors.log"
        if not error_file.exists():
            return []
        
        with open(error_file, 'r') as f:
            lines = f.readlines()
        
        return lines[-n:] if len(lines) > n else lines
    
    def get_log_summary(self) -> dict:
        """Resumen de logs: conteo por nivel."""
        log_file = self.log_dir / f"{self.app_name}.log"
        if not log_file.exists():
            return {"info": 0, "warning": 0, "error": 0, "critical": 0}
        
        counts = {"INFO": 0, "WARNING": 0, "ERROR": 0, "CRITICAL": 0}
        with open(log_file, 'r') as f:
            for line in f:
                for level in counts:
                    if f"[{level}]" in line:
                        counts[level] += 1
        
        return counts


# Singleton para uso global
_logger_instance = None

def get_logger(log_dir: str = "logs", app_name: str = "oma-core") -> OMACoreLogger:
    """Obtiene la instancia singleton del logger."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = OMACoreLogger(log_dir, app_name)
    return _logger_instance
