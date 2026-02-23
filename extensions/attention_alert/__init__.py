import logging
from .config import get_config
from .attention_observer import AttentionObserver
from .event_bus import get_global_bus
from .subprocess_patch import apply_patch

logger = logging.getLogger(__name__)

__version__ = "1.0.0"

def init():
    """Initializes and registers the Attention Alert extension."""
    config = get_config()
    
    if not config.enabled:
        logger.info("Attention Alert extension is disabled in config.")
        return

    # 1. Start Event Bus
    bus = get_global_bus()
    
    # 2. Patch subprocess.Popen for observability
    apply_patch()
    
    # 3. Start Watchdog Thread
    from .watchdog import get_watchdog
    watchdog = get_watchdog(timeout_seconds=config.stall_timeout_seconds)
    watchdog.start()
    
    # 4. Start Observer (subscribes to bus and handles alerts)
    observer = AttentionObserver(bus=bus)
    observer.start()
    
    # Optional Step 5: Hook into existing tool frameworks if running within 
    # a known environment (e.g. patching notify_user tool here if possible
    # without deeper agent coupling).
    
    logger.info(f"Attention Alert extension v{__version__} initialized.")
