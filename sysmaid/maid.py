import logging
import threading
import pythoncom
import wmi
import time
import win32gui
import win32process

logger = logging.getLogger(__name__)

class _EventManager:
    _lock = threading.Lock()
    _watchdogs = []
    _runner_thread = None
    _is_running = False

    @classmethod
    def add_watchdog(cls, watchdog):
        with cls._lock:
            cls._watchdogs.append(watchdog)

    @classmethod
    def _loop(cls):
        try:
            pythoncom.CoInitialize()
            c = wmi.WMI()
            logger.info("WMI connection successful. Starting polling loop.")
            while cls._is_running:
                pids_with_windows = set()
                def enum_windows_callback(hwnd, _):
                    if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                        _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
                        pids_with_windows.add(found_pid)
                win32gui.EnumWindows(enum_windows_callback, None)
                
                with cls._lock:
                    for dog in cls._watchdogs:
                        dog.check_state(c, pids_with_windows)
                time.sleep(1)
        except Exception as e:
            logger.critical(f"SysMaid background thread has crashed: {e}", exc_info=True)
        finally:
            logger.info("SysMaid background thread is shutting down.")
            pythoncom.CoUninitialize()

    @classmethod
    def start(cls):
        if not cls._runner_thread:
            cls._is_running = True
            cls._runner_thread = threading.Thread(target=cls._loop)
            cls._runner_thread.start()

class Watchdog:
    def __init__(self, process_name):
        self.process_name = process_name
        self._callbacks = {}

    def check_state(self, c, pids_with_windows):
        # This method is intended to be overridden by subclasses.
        raise NotImplementedError

class ProcessWatcher:
    def __init__(self, process_name):
        self._process_name = process_name
        self._watchdogs = {}

    @property
    def has_no_window(self):
        if 'no_window' not in self._watchdogs:
            from .condiction.no_window import NoWindowWatchdog
            dog = NoWindowWatchdog(self._process_name)
            _EventManager.add_watchdog(dog)
            self._watchdogs['no_window'] = dog
        return self._watchdogs['no_window'].has_no_window
    
    @property
    def is_exited(self):
        if 'is_exited' not in self._watchdogs:
            from .condiction.is_exited import ExitedWatchdog
            dog = ExitedWatchdog(self._process_name)
            _EventManager.add_watchdog(dog)
            self._watchdogs['is_exited'] = dog
        return self._watchdogs['is_exited'].is_exited

def attend(process_name):
    return ProcessWatcher(process_name)

def start():
    logger.info("SysMaid service starting...")
    _EventManager.start()