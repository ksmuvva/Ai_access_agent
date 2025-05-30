"""
Logger utility for the AI Accessibility Testing Agent
"""

import logging
import sys
from typing import Optional

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Set up a logger with consistent formatting"""
    logger = logging.getLogger(name)
    
    if not logger.handlers:  # Avoid adding multiple handlers
        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level)
    
    return logger
