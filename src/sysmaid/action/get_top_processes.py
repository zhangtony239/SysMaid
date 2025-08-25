import psutil
import logging

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
                p.info['cpu_percent'] = p.cpu_percent(interval=0.1)
                processes.append(p)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Exclude System Idle Process
        processes = [p for p in processes if p.info['name'] != 'System Idle Process']

        # Sort processes by CPU usage
        processes.sort(key=lambda p: p.info['cpu_percent'], reverse=True)

        # Format the output string
        top_processes = processes[:count]
        result = [f"Top {count} CPU-consuming processes:"]
        for p in top_processes:
            try:
                result.append(
                    f"  - PID: {p.info['pid']}, "
                    f"Name: {p.info['name']}, "
                    f"CPU: {p.info['cpu_percent']:.2f}%"
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                result.append(f"  - PID: {p.info.get('pid', 'N/A')}, Name: {p.info.get('name', 'N/A')}, CPU: N/A (process has exited)")
        return "\n".join(result)

    except Exception as e:
        logger.error(f"Failed to get top processes: {e}", exc_info=True)
        return f"Error: Could not retrieve top processes. {e}"