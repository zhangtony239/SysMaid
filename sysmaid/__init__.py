import ctypes
import logging
from .taskkill import attend, kill, start

def _is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:  # noqa: E722
        return False

# Library requires Admin privileges to correctly access window information.
if not _is_admin():
    raise PermissionError("SysMaid requires administrator privileges to run correctly. Please restart your script with administrator rights.")

# Set up a basic, user-friendly logger for the library.
# The user can override this configuration if they wish.
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] {%(name)-16s} [%(levelname)-5.5s]  %(message)s',
    datefmt='%H:%M:%S'
)

__all__ = [
    "attend",
    "kill",
    "start",
]