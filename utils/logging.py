"""
Central logging utility for BinBot
Provides consistent logging setup across all modules
"""

import logging
import os
import sys
from datetime import datetime
from typing import Optional


def setup_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Set up a logger with consistent formatting across the application
    
    Args:
        name (str): Logger name (typically __name__ from calling module)
        level (str, optional): Log level override. If None, uses LOG_LEVEL env var or INFO
        
    Returns:
        logging.Logger: Configured logger instance
        
    Example:
        >>> from utils.logging import setup_logger
        >>> logger = setup_logger(__name__)
        >>> logger.info("This is a log message")
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if logger already configured
    if logger.handlers:
        return logger
    
    # Set level from parameter, environment variable, or default to INFO
    log_level = level or os.getenv('LOG_LEVEL', 'INFO')
    try:
        logger.setLevel(getattr(logging, log_level.upper()))
    except AttributeError:
        logger.setLevel(logging.INFO)
        logger.warning(f"Invalid log level '{log_level}', defaulting to INFO")
    
    # Create formatter with timestamp, module name, level, and message
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Don't propagate to root logger to avoid duplicate messages
    logger.propagate = False
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger with standard configuration
    Convenience function that calls setup_logger
    
    Args:
        name (str): Logger name (typically __name__ from calling module)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    return setup_logger(name)


def set_global_log_level(level: str):
    """
    Set log level for all existing loggers
    
    Args:
        level (str): Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    try:
        log_level = getattr(logging, level.upper())
        
        # Update all existing loggers
        for logger_name in logging.Logger.manager.loggerDict:
            logger = logging.getLogger(logger_name)
            logger.setLevel(log_level)
            
        # Update root logger
        logging.getLogger().setLevel(log_level)
        
        print(f"✅ Global log level set to {level.upper()}")
        
    except AttributeError:
        print(f"❌ Invalid log level '{level}'. Valid levels: DEBUG, INFO, WARNING, ERROR, CRITICAL")


def log_function_call(logger: logging.Logger, func_name: str, *args, **kwargs):
    """
    Helper function to log function calls with arguments
    
    Args:
        logger: Logger instance
        func_name: Name of the function being called
        *args: Positional arguments
        **kwargs: Keyword arguments
    """
    args_str = ', '.join([repr(arg) for arg in args])
    kwargs_str = ', '.join([f"{k}={repr(v)}" for k, v in kwargs.items()])
    
    all_args = []
    if args_str:
        all_args.append(args_str)
    if kwargs_str:
        all_args.append(kwargs_str)
    
    logger.info(f"CALL {func_name}({', '.join(all_args)})")


def log_function_result(logger: logging.Logger, func_name: str, result: any, success: bool = True):
    """
    Helper function to log function results
    
    Args:
        logger: Logger instance
        func_name: Name of the function
        result: Function result or error message
        success: Whether the function succeeded
    """
    level = "info" if success else "error"
    status = "RESULT" if success else "ERROR"
    getattr(logger, level)(f"{status} {func_name}: {result}")
