import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path

def setup_logging(log_level: str = "INFO", log_file: str = None):
    """
    Centralized logging configuration for ShadowLink application.
    
    args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path. If None, logs to console only.
    """
    
    # Create logs directory if it doesn't exist
    if log_file:
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Define log format
    formatter = logging.Formatter(
        fmt='%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation (if log_file specified)
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    return root_logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (usually __name__ from calling module)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

# Default loggers for different modules
def get_api_logger() -> logging.Logger:
    """Logger for API operations"""
    return get_logger("SHADOWLINK.API")

def get_scanner_logger() -> logging.Logger:
    """Logger for scanning operations"""
    return get_logger("SHADOWLINK.SCANNER")

def get_worker_logger() -> logging.Logger:
    """Logger for Celery worker operations"""
    return get_logger("SHADOWLINK.WORKER")

def get_db_logger() -> logging.Logger:
    """Logger for database operations"""
    return get_logger("SHADOWLINK.DB")

def get_security_logger() -> logging.Logger:
    """Logger for security events"""
    return get_logger("SHADOWLINK.SECURITY")

# Initialize logging with environment-based configuration
def init_logging():
    """Initialize logging based on environment variables"""
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_file = os.getenv("LOG_FILE")
    
    if log_file:
        # Default to logs/shadowlink.log if directory specified
        if os.path.isdir(log_file):
            log_file = os.path.join(log_file, "shadowlink.log")
    else:
        # Default log file in production
        if os.getenv("ENVIRONMENT", "development").lower() == "production":
            log_file = "logs/shadowlink.log"
    
    return setup_logging(log_level, log_file)
