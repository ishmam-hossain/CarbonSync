import logging
import sys

def setup_logger():
    """Configures and returns a central logger instance."""
    
    logger = logging.getLogger('metric_logger')
    # Capture all messages
    logger.setLevel(logging.DEBUG)
    
    # Prevent log messages from propagating to the root logger.
    # This prevents duplicate messages if the root logger is also configured.
    logger.propagate = False
    
    # Console handler with a higher log level for general use.
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # File handler to store all debug messages.
    file_handler = logging.FileHandler('metric_collection.log')
    file_handler.setLevel(logging.DEBUG)
    
    # Custom formatter.
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Formatter for both handlers.
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Handlers to the logger.
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger
