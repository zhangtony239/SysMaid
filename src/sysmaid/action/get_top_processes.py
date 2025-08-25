import wmi
import pythoncom
from ..i18n import get_text

def get_top_processes(count: int) -> str:
    """
    获取当前CPU使用率最高的几个进程。

    Args:
        count (int): 要获取的进程数量。

    Returns:
        str: 一个格式化的字符串，包含进程名、PID和CPU使用率。
    """
    pythoncom.CoInitialize()
    try:
        c = wmi.WMI()
        processes = c.Win32_PerfFormattedData_PerfProc_Process()
        num_processors = c.Win32_ComputerSystem()[0].NumberOfLogicalProcessors
        processes = [p for p in processes if p.Name not in ["_Total", "Idle"]]
        sorted_processes = sorted(processes, key=lambda p: int(p.PercentProcessorTime), reverse=True)
        top_processes = sorted_processes[:count]

        result = [get_text("get_top_processes.result.header").format(count=count)]
        for p in top_processes:
            try:
                usage = int(p.PercentProcessorTime) / int(num_processors)
                pid = p.IDProcess
                name = p.Name
                result.append(get_text("get_top_processes.result.item").format(pid=pid, name=name, cpu=f"{usage:.2f}"))
            except Exception:
                # 进程可能在获取信息时退出
                result.append(get_text("get_top_processes.result.item.error").format(pid=p.IDProcess, name=p.Name))

        return "\n".join(result)
    finally:
        pythoncom.CoUninitialize()