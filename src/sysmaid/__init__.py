import ctypes
import logging
import os
from .i18n import get_text
from .maid import attend, start
from .action.kill_process import kill_process
from .action.stop_service import stop_service
from .action.lock_volume import lock_volume

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

def _is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:  # noqa: E722
        return False

# Library requires Admin privileges.
# Skip this check in CI environments where admin rights are not available.
if "CI" in os.environ:
    logger.warning(get_text("init.admin.skip.message"))
else:
    if not _is_admin():
        ctypes.windll.user32.MessageBoxW(0, get_text("init.admin.error.message"), get_text("init.admin.error.title"), 0x10)
        exit(0)

__all__ = [
    "attend",
    "kill_process",
    "stop_service",
    "lock_volume",
    "start",
    "set_log_level",
]