import logging
from logging.handlers import RotatingFileHandler
import sys
from pathlib import Path
from datetime import datetime
from app.config import settings

class CustomFormatter(logging.Formatter):
    """Custom formatter with color support"""
    
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    
    FORMATS = {
        logging.DEBUG: grey + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + reset,
        logging.INFO: grey + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + reset,
        logging.WARNING: yellow + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + reset,
        logging.ERROR: red + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + reset,
        logging.CRITICAL: bold_red + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)

def setup_logger(name: str) -> logging.Logger:
    """Setup logger with file and console handlers"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)

    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Create rotating file handler
    timestamp = datetime.utcnow().strftime("%Y%m%d")
    file_handler = RotatingFileHandler(
        filename=log_dir / f"{name}_{timestamp}.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    file_handler.setLevel(logging.DEBUG)

    # Create console handler with custom formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(CustomFormatter())
    console_handler.setLevel(logging.INFO)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

def log_function_call(logger: logging.Logger):
    """Decorator to log function calls"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            logger.debug(f"Calling function: {func_name}")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"Function {func_name} completed successfully")
                return result
            except Exception as e:
                logger.error(f"Error in function {func_name}: {str(e)}")
                raise
        return wrapper
    return decorator

def log_async_function_call(logger: logging.Logger):
    """Decorator to log async function calls"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            func_name = func.__name__
            logger.debug(f"Calling async function: {func_name}")
            try:
                result = await func(*args, **kwargs)
                logger.debug(f"Async function {func_name} completed successfully")
                return result
            except Exception as e:
                logger.error(f"Error in async function {func_name}: {str(e)}")
                raise
        return wrapper
    return decorator