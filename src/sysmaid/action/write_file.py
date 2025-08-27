import os
import sys
import logging
import win32api

logger = logging.getLogger(__name__)

def write_file(path: str, content: str, append: bool = False):
    """
    将内容按原样写入指定文件。

    Args:
        path (str): 目标文件的路径。
        content (str): 要写入的内容。
        append (bool, optional): 是否追加到文件末尾。默认为 False，会覆盖整个文件。
    """
    try:
        # Nuitka编译后，需要将相对路径转换为基于可执行文件位置的绝对路径
        if not os.path.isabs(path) and getattr(sys, 'frozen', False):
            # 在UAC提权后，sys.argv[0]和sys.executable都可能指向System32
            # 使用win32api可以更可靠地获取程序自身的路径
            base_dir = os.path.dirname(win32api.GetModuleFileName(win32api.GetModuleHandle(None)))
            path = os.path.join(base_dir, path)
            
        # 确保目录存在
        dir_name = os.path.dirname(path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        mode = 'a' if append else 'w'
        with open(path, mode, encoding='utf-8') as f:
            f.write(str(content))

        logger.info(f"Successfully wrote to file: {path}")

    except Exception as e:
        logger.error(f"Failed to write to file {path}: {e}", exc_info=True)