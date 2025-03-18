# debug_utils.py
import traceback
import logging
import sys
import os
from datetime import datetime

# Set up logging
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_filename = os.path.join(log_dir, f"debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("magical_athlete")

def log_exception(e, context=""):
    """Log an exception with full traceback information."""
    tb_str = traceback.format_exc()
    logger.error(f"Exception in {context}: {str(e)}\n{tb_str}")
    return tb_str

def get_full_error_message(e, context=""):
    """Get a detailed error message including the traceback."""
    tb_str = traceback.format_exc()
    return f"Error in {context}:\n{str(e)}\n\nTraceback:\n{tb_str}"