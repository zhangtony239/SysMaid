import logging
import threading
import pythoncom
import wmi
import time
import win32gui
import win32process

logger = logging.getLogger(__name__)

# 全局的 watchdog 列表，为统一Start做准备
_watchdogs = []

class Watchdog:
    """
    每个 Watchdog 实例都是一个独立的监控单元，
    拥有自己的后台线程来轮询检查进程状态。
    """
    def __init__(self, process_name):
        self.process_name = process_name
        self._callbacks = {}
        self._thread = None
        self._is_running = False

        # 将自身注册到全局列表
        _watchdogs.append(self)

    def _loop(self):
        """每个 watchdog 自己的轮询循环。"""
        try:
            pythoncom.CoInitialize()
            c = wmi.WMI()
            logger.info(f"Watchdog for '{self.process_name}' started polling in thread {threading.get_ident()}.")
            
            while self._is_running:
                pids_with_windows = set()
                def enum_windows_callback(hwnd, _):
                    if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                        _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
                        pids_with_windows.add(found_pid)
                
                # 每个线程独立获取窗口信息
                win32gui.EnumWindows(enum_windows_callback, None)
                
                self.check_state(c, pids_with_windows)
                time.sleep(1) # 轮询间隔
        except Exception as e:
            logger.critical(f"Watchdog thread for '{self.process_name}' has crashed: {e}", exc_info=True)
        finally:
            logger.info(f"Watchdog thread for '{self.process_name}' is shutting down.")
            pythoncom.CoUninitialize()

    def start(self):
        """启动该 watchdog 的后台监控线程。"""
        if not self._is_running:
            self._is_running = True
            self._thread = threading.Thread(target=self._loop)
            self._thread.daemon = True # 设置为守护线程，主程序退出时自动结束
            self._thread.start()

    def check_state(self, c, pids_with_windows):
        # 此方法由子类实现具体的检查逻辑
        raise NotImplementedError

class ProcessWatcher:
    def __init__(self, process_name):
        self._process_name = process_name
        self._watchdogs = {}

    def _get_or_create_watchdog(self, key, factory):
        if key not in self._watchdogs:
            # 创建 watchdog，它会自动注册到全局列表
            dog = factory(self._process_name)
            self._watchdogs[key] = dog
        return self._watchdogs[key]

    @property
    def has_no_window(self):
        from .condiction.no_window import NoWindowWatchdog
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
        
def attend(process_name):
    """
    关注一个进程，返回一个 ProcessWatcher 实例用于设置监控条件。
    """
    return ProcessWatcher(process_name)

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
