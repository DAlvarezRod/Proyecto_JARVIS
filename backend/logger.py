"""
Logger configuration for JARVIS
Provides centralized logging with file rotation and console output
"""

import logging
import logging.handlers
import os
from pathlib import Path
import yaml

# Load configuration
config_path = Path(__file__).parent / "config.yaml"
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

log_config = config.get('logging', {})
log_level = getattr(logging, log_config.get('level', 'DEBUG'))
log_format = log_config.get('format', "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
log_file = log_config.get('file', 'logs/jarvis.log')
max_size = log_config.get('max_size_mb', 10) * (1024 * 1024)  # Convert MB to bytes
backup_count = log_config.get('backup_count', 5)

# Create logs directory if it doesn't exist
Path(log_file).parent.mkdir(parents=True, exist_ok=True)

# Create root logger
logger = logging.getLogger('jarvis')
logger.setLevel(log_level)

# Remove existing handlers to avoid duplicates
logger.handlers = []

# Create formatter
formatter = logging.Formatter(log_format)

# Console handler (output to terminal)
console_handler = logging.StreamHandler()
console_handler.setLevel(log_level)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# File handler with rotation
file_handler = logging.handlers.RotatingFileHandler(
    log_file,
    maxBytes=max_size,
    backupCount=backup_count
)
file_handler.setLevel(log_level)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def get_logger(name):
    """
    Get a logger instance for a specific module
    
    Args:
        name: Module name (typically __name__)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(f'jarvis.{name}')


# Log startup
logger.info("=" * 70)
logger.info("JARVIS Logger Initialized")
logger.info(f"Log level: {log_level}")
logger.info(f"Log file: {log_file}")
logger.info("=" * 70)
