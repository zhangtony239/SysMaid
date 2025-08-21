import logging
import wmi
import pythoncom
import threading
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
                    # We check IsWindowVisible and also if the window has a title.
                    # This helps filter out many background/utility windows.
                    if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                        _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
                        pids_with_windows.add(found_pid)
                win32gui.EnumWindows(enum_windows_callback, None)
                logger.debug(f"PIDs with visible windows: {pids_with_windows if pids_with_windows else 'None'}")
                
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
        self._no_window_checks_count = 0
        self.GRACE_PERIOD = 3 # 3 seconds

    def has_no_window(self, func):
        self._callbacks['has_no_window'] = func
        return func

    def check_state(self, c, pids_with_windows):
        process_name = self.process_name
        try:
            processes = c.Win32_Process(name=process_name)
            if not processes:
                # The application is not running at all. Reset our state.
                if self._no_window_checks_count > 0:
                    logger.debug(f"'{process_name}' is no longer running. Resetting zombie check.")
                    self._no_window_checks_count = 0
                return

            current_pids = {p.ProcessId for p in processes}
            
            # The logic is: the APP is a zombie if NONE of its processes have a window.
            app_has_a_window = any(pid in pids_with_windows for pid in current_pids)

            if app_has_a_window:
                # If any process has a window, the whole app is considered active. Reset the count.
                if self._no_window_checks_count > 0:
                    logger.debug(f"'{process_name}' has a visible window. Vindicating.")
                    self._no_window_checks_count = 0
            else:
                # None of the processes have a window. Increment the zombie countdown.
                self._no_window_checks_count += 1
                logger.debug(f"'{process_name}' has no visible windows. Zombie check count: {self._no_window_checks_count}/{self.GRACE_PERIOD}")
                if self._no_window_checks_count >= self.GRACE_PERIOD:
                    logger.info(f"ZOMBIE CONFIRMED for app '{process_name}'. All processes lack windows. Firing callback.")
                    if 'has_no_window' in self._callbacks:
                        self._callbacks['has_no_window']()
                        self._no_window_checks_count = 0 # Reset after firing
                        
        except wmi.x_wmi as e:
            logger.error(f"WMI query for '{process_name}' failed: {e}")

_event_manager = _EventManager()

def Setup(process_name):
    dog = Watchdog(process_name)
    _event_manager.add_watchdog(dog)
    return dog

def start():
    logger.info("SysMaid service starting...")
    _event_manager.start()

def kill(watchdog_instance):
    process_name = watchdog_instance.process_name
    logger.info(f"Executing kill for '{process_name}'.")
    try:
        pythoncom.CoInitialize()
        c = wmi.WMI()
        killed_count = 0
        processes_to_kill = c.Win32_Process(name=process_name)
        
        if not processes_to_kill:
            logger.info(f"Kill command ran, but no active '{process_name}' processes were found.")
            return

        for process in processes_to_kill:
            try:
                process.Terminate()
                killed_count += 1
                logger.info(f"Sent Terminate signal to '{process_name}' (PID: {process.ProcessId}).")
            except wmi.x_wmi as e:
                # This handles the race condition where the process dies right before Terminate() is called.
                logger.warning(f"Could not terminate '{process_name}' (PID: {process.ProcessId}). It may have already exited. Details: {e}")
        
        logger.info(f"Kill command finished. Terminated {killed_count} instance(s) of '{process_name}'.")
        
    except Exception as e:
        logger.error(f"A critical error occurred during WMI kill for '{process_name}': {e}", exc_info=True)
    finally:
        pythoncom.CoUninitialize()
