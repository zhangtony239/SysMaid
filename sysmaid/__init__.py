import ctypes
import logging
from .maid import _event_manager
from .i18n import get_text
from .condiction.no_window import attend
from .action.kill_proc import kill

logger = logging.getLogger(__name__)

def set_log_level(level):
    """
    Sets the logging level for the SysMaid library.

    Args:
        level (str): The desired logging level. Can be one of 'DEBUG', 'INFO',
                     'WARNING', 'ERROR', 'CRITICAL'.
    """
    # Set up a basic, user-friendly logger for the library.
    # The user can override this configuration if they wish.
    logging.basicConfig(
        level=level,
        format='[%(asctime)s] {%(name)-16s} %(message)s',
        datefmt='%H:%M:%S'
    )

def start():
    logger.info("SysMaid service starting...")
    _event_manager.start()

def _is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:  # noqa: E722
        return False

# Library requires Admin privileges to correctly access window information.
if not _is_admin():
    ctypes.windll.user32.MessageBoxW(0, get_text("init.admin.error.message"), get_text("init.admin.error.title"), 0x10)
    exit(0)

__all__ = [
    "attend",
    "kill",
    "start",
    "set_log_level",
]