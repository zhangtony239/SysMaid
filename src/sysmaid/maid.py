import logging
import threading
import pythoncom
import wmi
import time
import win32gui
import win32process
from typing import overload, Literal

@overload
def attend(name: Literal['cpu', 'ram', 'gpu', 'CPU', 'RAM', 'GPU']) -> 'HardwareWatcher': ...
@overload
def attend(name: str) -> 'ProcessWatcher': ...

logger = logging.getLogger(__name__)

# 全局的 watchdog 列表，为统一Start做准备
_watchdogs = []

HARDWARE_KEYWORDS = ['cpu', 'ram', 'gpu', 'CPU', 'RAM', 'GPU']

class BaseWatchdog:
    """
    所有 Watchdog 的基类，处理通用的线程管理和事件循环。
    """
    def __init__(self, name):
        self.name = name
        self._callbacks = {}
        self._thread = None
        self._is_running = False
        _watchdogs.append(self)

    def _loop(self):
        """每个 watchdog 自己的轮询循环。"""
        logger.info(f"Watchdog for '{self.name}' started polling in thread {threading.get_ident()}.")
        try:
            while self._is_running:
                self.check_state()
        except Exception as e:
            logger.critical(f"Watchdog thread for '{self.name}' has crashed: {e}", exc_info=True)
        finally:
            logger.info(f"Watchdog thread for '{self.name}' is shutting down.")

    def start(self):
        if not self._is_running:
            self._is_running = True
            self._thread = threading.Thread(target=self._loop)
            self._thread.daemon = True
            self._thread.start()

    def check_state(self):
        raise NotImplementedError

class ProcessWatchdog(BaseWatchdog):
    """专门用于监控进程状态的 Watchdog"""
    def __init__(self, process_name):
        super().__init__(name=process_name)
    
    def _loop(self):
        """
        为进程监控定制的循环，包含WMI初始化。
        """
        try:
            pythoncom.CoInitialize()
            self.c = wmi.WMI()
            logger.info(f"Process watchdog for '{self.name}' started polling with WMI in thread {threading.get_ident()}.")
            
            while self._is_running:
                self.check_state()
                time.sleep(1) # 轮询间隔
        except Exception as e:
            logger.critical(f"Watchdog thread for '{self.name}' has crashed: {e}", exc_info=True)
        finally:
            logger.info(f"Watchdog thread for '{self.name}' is shutting down.")
            pythoncom.CoUninitialize()

    def check_state(self):
        """
        覆盖基类方法，加入进程特有的窗口信息获取，
        然后调用子类（如NoWindowWatchdog）的最终实现。
        """
        pids_with_windows = set()
        def enum_windows_callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
                pids_with_windows.add(found_pid)
        win32gui.EnumWindows(enum_windows_callback, None)
        
        # 调用真正的检查逻辑，这个方法将在NoWindowWatchdog等子类中实现
        self.check_process_state(pids_with_windows)

    def check_process_state(self, pids_with_windows):
        raise NotImplementedError("This method should be implemented by specific process condition subclasses.")

class HardwareWatchdog(BaseWatchdog):
    """专门用于监控硬件状态的 Watchdog"""
    def __init__(self, hardware_name):
        super().__init__(name=hardware_name)

    def check_state(self):
        raise NotImplementedError("This method should be implemented by subclasses like IsTooBusyWatchdog.")

class ProcessWatcher:
    def __init__(self, process_name):
        self._process_name = process_name
        self._watchdogs = {}

    def _get_or_create_watchdog(self, key, factory, *args, **kwargs):
        if key not in self._watchdogs:
            dog = factory(self._process_name, *args, **kwargs)
            self._watchdogs[key] = dog
        return self._watchdogs[key]

    @property
    def has_no_window(self):
        from .condiction.has_no_window import NoWindowWatchdog
        dog = self._get_or_create_watchdog('no_window', NoWindowWatchdog)
        return dog.has_no_window
    
    @property
    def is_exited(self):
        from .condiction.is_exited import ExitedWatchdog
        dog = self._get_or_create_watchdog('is_exited', ExitedWatchdog)
        return dog.is_exited

    @property
    def is_running(self):
        from .condiction.is_running import RunningWatchdog
        dog = self._get_or_create_watchdog('is_running', RunningWatchdog)
        return dog.is_running

class HardwareWatcher:
    def __init__(self, hardware_name):
        self._hardware_name = hardware_name
        self._watchdogs = {}

    def _get_or_create_watchdog(self, key, factory, *args, **kwargs):
        if key not in self._watchdogs:
            dog = factory(self._hardware_name, *args, **kwargs)
            self._watchdogs[key] = dog
        return self._watchdogs[key]

    def is_too_busy(self, over, duration):
        from .condiction.is_too_busy import IsTooBusyWatchdog
        # 产生一个唯一的key，以便相同的参数得到同一个watchdog
        key = f'is_too_busy_{over}_{duration}'
        dog = self._get_or_create_watchdog(key, IsTooBusyWatchdog, over=over, duration=duration)
        return dog.is_too_busy

def attend(name: str):
    """
    关注一个进程或硬件，返回一个 Watcher 实例用于设置监控条件。
    """
    if name in HARDWARE_KEYWORDS:
        return HardwareWatcher(name.lower())
    else:
        return ProcessWatcher(name)

# --- Public Actions ---
def get_top_processes(count: int) -> str:
   from .action.get_top_processes import get_top_processes as get_top_processes_func
   return get_top_processes_func(count)

def alarm(content: str):
    from .action.alarm import alarm as alarm_func
    alarm_func(content)

def write_file(path: str, content: str, append: bool = False):
    from .action.write_file import write_file as write_file_func
    write_file_func(path, content, append)

def start():
    """
    启动所有已配置的 watchdog 的监控线程，并保持主线程存活直到所有监控结束。
    """
    logger.info("SysMaid service starting all watchdogs...")
    dogs_to_watch = list(_watchdogs)
    if not dogs_to_watch:
        logger.warning("No watchdogs configured, SysMaid will exit.")
        return
    
    for dog in dogs_to_watch:
        dog.start()
    logger.info("All watchdogs have been started.")

    # 只要还有任何一个 watchdog 线程在运行，主线程就保持存活。
    # 这是一个容错机制，防止所有监控线程意外崩溃后主进程僵死。
    while any(dog._thread and dog._thread.is_alive() for dog in dogs_to_watch):
        time.sleep(10)

    logger.warning("All watchdog threads have stopped. SysMaid service is shutting down.")
