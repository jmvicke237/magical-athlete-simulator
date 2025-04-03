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

def track_recursion_depth(func):
    """Decorator to track recursion depth of a function."""
    import sys
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Get current recursion depth
        frame = sys._getframe()
        depth = 0
        func_name = func.__name__
        
        # Count how many times this function appears in the call stack
        while frame:
            if frame.f_code.co_name == func_name:
                depth += 1
            frame = frame.f_back
        
        # Log if depth is getting high
        if depth > 10:
            logger.warning(f"High recursion depth ({depth}) detected in {func_name}")
            
        if depth > 20:
            logger.error(f"Excessive recursion depth ({depth}) detected in {func_name}! This may cause a crash.")
            # Optionally raise an exception here instead of continuing
            # raise RecursionError(f"Maximum safe recursion depth exceeded in {func_name}")
            
        return func(*args, **kwargs)
    
    return wrapper

def log_recursion_state(game, operation, player=None):
    """Log the current recursion state with detailed information, but only when needed"""
    # Only log if we're approaching recursion limits
    if any(depth >= game._max_recursion_depth - 1 for depth in game._recursion_depths.values()):
        player_info = f" for {player.name} ({player.piece})" if player else ""
        message = f"Recursion state{player_info}: "
        for op, depth in game._recursion_depths.items():
            message += f"{op}={depth} "
        logger.warning(f"Approaching recursion limit on {operation}{player_info}: {message}")
        
        # Get a stack trace for better debugging
        import traceback
        stack = traceback.format_stack()[:-1]  # Exclude this function call
        logger.warning(f"Stack trace approaching recursion limit:\n{''.join(stack)}")