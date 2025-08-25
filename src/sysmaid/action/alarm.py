import ctypes
import logging
import threading
from ..i18n import get_text

logger = logging.getLogger(__name__)

def _show_messagebox(content: str):
    """
    Helper function to display a message box.
    This avoids blocking the main thread if the user doesn't close the box immediately.
    """
    try:
        # MessageBoxW(HWND, text, caption, type)
        # HWND = 0 for no owner window
        # text = content to display
        # caption = window title
        # type = 0x40 (MB_ICONINFORMATION)
        ctypes.windll.user32.MessageBoxW(0, str(content), get_text("alarm.title"), 0x40)
    except Exception as e:
        logger.error(f"Failed to show alarm messagebox: {e}", exc_info=True)

def alarm(content: str):
    """
    在一个独立的线程中安全地弹出一个包含指定内容的系统消息框。

    Args:
        content (str): 要显示在消息框中的文本内容。
    """
    logger.info(f"Triggering alarm with content: {content}")
    # Run the GUI part in a separate thread to avoid blocking the main loop
    thread = threading.Thread(target=_show_messagebox, args=(content,))
    thread.daemon = True
    thread.start()