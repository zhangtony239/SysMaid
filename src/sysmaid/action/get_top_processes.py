import psutil
import logging
from ..i18n import get_text

logger = logging.getLogger(__name__)

def get_top_processes(count: int) -> str:
    """
    获取CPU占用率最高的N个进程的信息。

    Args:
        count (int): 要获取的进程数量。

    Returns:
        str: 格式化的进程信息字符串。
    """
    try:
        processes = []
        for p in psutil.process_iter(['pid', 'name']):
            try:
                # The pre-warming is now handled by the IsTooBusyWatchdog.
                # This call retrieves the CPU usage since the watchdog was initialized.
                p.info['cpu_percent'] = p.cpu_percent(interval=None)
                processes.append(p)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Exclude System Idle Process
        processes = [p for p in processes if p.info['name'] != 'System Idle Process']

        # Sort processes by CPU usage
        processes.sort(key=lambda p: p.info['cpu_percent'], reverse=True)

        # Format the output string
        top_processes = processes[:count]
        result = [get_text("get_top_processes.result.header").format(count=count)]
        for p in top_processes:
            try:
                result.append(
                    get_text("get_top_processes.result.item").format(
                        pid=p.info['pid'],
                        name=p.info['name'],
                        cpu=f"{p.info['cpu_percent']:.2f}"
                    )
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                result.append(
                    get_text("get_top_processes.result.item.error").format(
                        pid=p.info.get('pid', 'N/A'),
                        name=p.info.get('name', 'N/A')
                    )
                )
        return "\n".join(result)

    except Exception as e:
        logger.error(f"Failed to get top processes: {e}", exc_info=True)
        return get_text("get_top_processes.return.general_error").format(error=e)