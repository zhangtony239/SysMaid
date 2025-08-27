import os
import logging

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
        # 修复Nuitka打包+UAC提权导致的相对路径指向System32的问题
        if not os.path.isabs(path):
            path = os.path.abspath(path)

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