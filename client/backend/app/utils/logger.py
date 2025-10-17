"""
Centralized logging configuration for Scrim.GG Client Backend.
Provides consistent logging across all client backend modules.
"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Get base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Create logs directory
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        level: Logging level (default: INFO)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Don't configure if already configured
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # ==================== FORMATTERS ====================
    # Verbose format for file logs
    file_formatter = logging.Formatter(
        '[{levelname}] {asctime} | {name} | {funcName}:{lineno} | {message}',
        style='{',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Concise format for console
    console_formatter = logging.Formatter(
        '[{levelname:8}] {name:25} | {message}',
        style='{'
    )
    
    # ==================== HANDLERS ====================
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    # File handler for all logs
    file_handler = RotatingFileHandler(
        LOGS_DIR / 'client.log',
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    
    # Error file handler
    error_handler = RotatingFileHandler(
        LOGS_DIR / 'client_errors.log',
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    
    return logger


def setup_root_logger():
    """Setup root logger for the entire application."""
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove any existing handlers
    root_logger.handlers.clear()
    
    # Add handlers
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(
        logging.Formatter('[{levelname:8}] {name:25} | {message}', style='{')
    )
    
    file_handler = RotatingFileHandler(
        LOGS_DIR / 'client.log',
        maxBytes=10 * 1024 * 1024,
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter(
            '[{levelname}] {asctime} | {name} | {funcName}:{lineno} | {message}',
            style='{',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    )
    
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    
    return root_logger

