import logging
import threading
import pythoncom
import wmi
import time
import win32gui
import win32process
from typing import overload, Literal
import pywintypes

@overload
def attend(name: Literal['cpu', 'ram', 'gpu', 'CPU', 'RAM', 'GPU', 'Screen']) -> 'HardwareWatcher': ... # type: ignore
@overload
def attend(name: str) -> 'ProcessWatcher': ...

logger = logging.getLogger(__name__)

# 全局的 watchdog 列表，为统一Start做准备
_watchdogs = []

HARDWARE_KEYWORDS = ['cpu', 'ram', 'gpu', 'CPU', 'RAM', 'GPU', 'Screen']

class BaseWatchdog:
    """
    所有 Watchdog 的基类，处理通用的线程管理和事件循环。
    """
    def __init__(self, name):
        self.name = name
        self.interval = 1 # 默认轮询间隔（秒）
        self._callbacks = {}
        self._thread = None
        self._is_running = False
        self._is_paused = False  # 新增：员工的暂停状态
        _watchdogs.append(self)

    def pause(self):
        """暂停工作循环。"""
        self._is_paused = True

    def resume(self):
        """恢复工作循环。"""
        self._is_paused = False

    def _check_and_wait(self):
        """封装了暂停检查、任务执行和等待的原子操作。"""
        if self._is_paused:
            time.sleep(1)  # 在暂停时休眠，以降低CPU使用率
            return

        self.check_state()
        time.sleep(self.interval)

    def _loop(self):
        """每个watchdog自己的轮询循环（模板方法）。"""
        logger.info(f"Watchdog for '{self.name}' started polling in thread {threading.get_ident()}.")
        try:
            while self._is_running:
                self._check_and_wait()
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
        为进程监控定制的循环，在基类循环的基础上增加了WMI初始化和反初始化。
        """
        try:
            pythoncom.CoInitialize()
            self.c = wmi.WMI()
            logger.info(f"Process watchdog for '{self.name}' started polling with WMI in thread {threading.get_ident()}.")
            
            # 调用基类的循环模板
            super()._loop()

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

class BaseWmiEvent:
    def __init__(self, name, event_type):
        self.name = name
        self.event_type = event_type
        self._callbacks = {}
        self._thread = None
        self._is_running = False
        self._is_paused = False # 新增：员工的暂停状态
        self.query = self._build_query()
        _watchdogs.append(self)

    def pause(self):
        """暂停工作循环。"""
        self._is_paused = True

    def resume(self):
        """恢复工作循环。"""
        self._is_paused = False

    def _build_query(self):
        """构建 WMI 事件查询语句。"""
        return (f"SELECT * FROM {self.event_type} "
                f"WITHIN 2 WHERE TargetInstance ISA 'Win32_Process' "
                f"AND TargetInstance.Name = '{self.name}'")

    def _loop(self):
        """WMI事件订阅循环。"""
        logger.info(f"WMI event watcher for '{self.name}' ({self.event_type}) started in thread {threading.get_ident()}.")
        try:
            pythoncom.CoInitialize()
            c = wmi.WMI()
            watcher = c.ExecNotificationQuery(self.query)
            while self._is_running:
                if self._is_paused:
                    time.sleep(1) # 在暂停时休眠
                    continue
                try:
                    event = watcher.NextEvent(100)
                    self.handle_event(event)
                except pywintypes.com_error as e:
                    # The HRESULT for WBEM_S_TIMEDOUT is -2147209215. This indicates an expected timeout.
                    # It's nested deep inside the exception object at e.args[2][5].
                    if len(e.args) > 2 and e.args[2] and e.args[2][5] == -2147209215:
                        continue  # This is a timeout, just continue waiting
                    raise  # Re-raise other unexpected COM errors
        except Exception as e:
            logger.critical(f"WMI event watcher for '{self.name}' has crashed: {e}", exc_info=True)
        finally:
            logger.info(f"WMI event watcher for '{self.name}' is shutting down.")
            pythoncom.CoUninitialize()

    def start(self):
        if not self._is_running:
            self._is_running = True
            self._thread = threading.Thread(target=self._loop)
            self._thread.daemon = True
            self._thread.start()

    def handle_event(self, event):
        raise NotImplementedError("This method should be implemented by subclasses.")


class HardwareWatchdog(BaseWatchdog):
    """专门用于监控硬件状态的 Watchdog"""
    def __init__(self, hardware_name):
        super().__init__(name=hardware_name)

    def check_state(self):
        raise NotImplementedError("This method should be implemented by subclasses like IsTooBusyWatchdog.")

class ProcessWatcher:
    def __init__(self, process_name):
        self.name = process_name
        self._watchdogs = {}
        self._is_active = True

    def start(self):
        """激活此看护实例，并恢复其下所有已创建的规则。"""
        logger.info(f"Attendant for '{self.name}' activated.")
        self._is_active = True
        for dog in self._watchdogs.values():
            dog.resume()

    def stop(self):
        """停用此看护实例，并暂停其下所有已创建的规则。"""
        logger.info(f"Attendant for '{self.name}' deactivated.")
        self._is_active = False
        for dog in self._watchdogs.values():
            dog.pause()

    def _get_or_create_watchdog(self, key, factory, *args, **kwargs):
        if key not in self._watchdogs:
            dog = factory(self.name, *args, **kwargs)
            # 在创建时，让所有dog继承当前状态
            if not self._is_active:
                dog.pause()
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
        self.name = hardware_name
        self._watchdogs = {}
        self._is_active = True
        self._start_ref_count = 0

    def start(self):
        """激活此看护实例，并恢复其下所有已创建的规则。"""
        self._start_ref_count += 1
        logger.info(f"Attendant for '{self.name}' start requested. Ref count: {self._start_ref_count}.")
        if self._start_ref_count == 1:
            logger.info(f"Attendant for '{self.name}' activated.")
            self._is_active = True
            for dog in self._watchdogs.values():
                dog.resume()

    def stop(self):
        """停用此看护实例，并暂停其下所有已创建的规则。"""
        if self._start_ref_count > 0:
            self._start_ref_count -= 1
        logger.info(f"Attendant for '{self.name}' stop requested. Ref count: {self._start_ref_count}.")
        if self._start_ref_count == 0:
            logger.info(f"Attendant for '{self.name}' deactivated.")
            self._is_active = False
            for dog in self._watchdogs.values():
                dog.pause()

    def _get_or_create_watchdog(self, key, factory, *args, **kwargs):
        if key not in self._watchdogs:
            dog = factory(self.name, *args, **kwargs)
            # 在创建时，让所有dog继承当前状态
            if not self._is_active:
                dog.pause()
            self._watchdogs[key] = dog
        return self._watchdogs[key]

    def is_too_busy(self, over, duration):
        from .condiction.is_too_busy import IsTooBusyWatchdog
        # 产生一个唯一的key，以便相同的参数得到同一个watchdog
        key = f'is_too_busy_{over}_{duration}'
        dog = self._get_or_create_watchdog(key, IsTooBusyWatchdog, over=over, duration=duration)
        return dog.is_too_busy

    def has_windows_look_like(self, template_image_path: str, threshold: float = 0.8, interval: int = 1):
        from .condiction.has_windows_look_like import WindowsMatchingWatchdog
        key = f'look_like_{template_image_path}_{threshold}_{interval}'
        dog = self._get_or_create_watchdog(key, WindowsMatchingWatchdog, template_image_path=template_image_path, threshold=threshold, interval=interval)
        return dog.is_found
        
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
