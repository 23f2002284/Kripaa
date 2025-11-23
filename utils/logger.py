import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional

# Try to import rich for pretty console logging
try:
    from rich.logging import RichHandler
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

def setup_logger(
    name: str = "kripaa",
    log_level: int = logging.INFO,
    log_file: Optional[str] = "logs/app.log"
) -> logging.Logger:
    """
    Sets up a logger with console (Rich) and file handlers.
    
    Args:
        name: Name of the logger.
        log_level: Logging level (default: INFO).
        log_file: Path to the log file. If None, file logging is disabled.
    
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    
    # If logger already has handlers, assume it's configured and return it
    if logger.handlers:
        return logger
    
    # Set logger to lowest level to allow handlers to filter
    logger.setLevel(logging.DEBUG)
    
    # Formatters
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_formatter = logging.Formatter(
        "%(message)s"
    )

    # Console Handler
    if HAS_RICH:
        console_handler = RichHandler(
            rich_tracebacks=True,
            markup=True,
            show_time=False # Rich shows time by default in a different way, or we can enable it
        )
        # RichHandler has its own formatting, usually we don't set a formatter for it 
        # unless we want to override the message part.
    else:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
    
    console_handler.setLevel(log_level)
    logger.addHandler(console_handler)
    
    # File Handler
    if log_file:
        # Ensure directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5, encoding="utf-8"
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG) # Always capture DEBUG in file if possible
        logger.addHandler(file_handler)
        
    # Prevent propagation to root logger to avoid double logging if root is configured
    logger.propagate = False
    
    return logger

def get_logger(name: str = "kripaa") -> logging.Logger:
    """
    Convenience function to get a logger. 
    If it's the main 'kripaa' logger, it ensures it's initialized.
    """
    if name == "kripaa":
        return setup_logger(name)
    return logging.getLogger(name)
