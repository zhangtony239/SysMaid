import logging
import threading
import pythoncom
import wmi
import time
import win32gui
import win32process

logger = logging.getLogger(__name__)

class _EventManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._watchdogs = []
        self._runner_thread = None
        self._is_running = False

    def add_watchdog(self, watchdog):
        with self._lock:
            self._watchdogs.append(watchdog)

    def _loop(self):
        try:
            pythoncom.CoInitialize()
            c = wmi.WMI()
            logger.info("WMI connection successful. Starting polling loop.")
            while self._is_running:
                pids_with_windows = set()
                def enum_windows_callback(hwnd, _):
                    if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                        _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
                        pids_with_windows.add(found_pid)
                win32gui.EnumWindows(enum_windows_callback, None)
                
                with self._lock:
                    for dog in self._watchdogs:
                        dog.check_state(c, pids_with_windows)
                time.sleep(1)
        except Exception as e:
            logger.critical(f"SysMaid background thread has crashed: {e}", exc_info=True)
        finally:
            logger.info("SysMaid background thread is shutting down.")
            pythoncom.CoUninitialize()

    def start(self):
        if not self._runner_thread:
            self._is_running = True
            self._runner_thread = threading.Thread(target=self._loop)
            self._runner_thread.start()

class Watchdog:
    def __init__(self, process_name):
        self.process_name = process_name
        self._callbacks = {}

    def check_state(self, c, pids_with_windows):
        # This method is intended to be overridden by subclasses.
        raise NotImplementedError

_event_manager = _EventManager()