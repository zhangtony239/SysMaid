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
        self._zombie_candidates = {} # {pid: checks_count}
        self.GRACE_PERIOD = 3 # 3 seconds

    def has_no_window(self, func):
        self._callbacks['has_no_window'] = func
        return func

    def check_state(self, c, pids_with_windows):
        process_name = self.process_name
        try:
            processes = c.Win32_Process(name=process_name)
            current_pids = {p.ProcessId for p in processes}

            # Check all running instances of the target process
            for pid in current_pids:
                if pid not in pids_with_windows:
                    # It's running but has no window, it's a candidate.
                    self._zombie_candidates[pid] = self._zombie_candidates.get(pid, 0) + 1
                    logger.debug(f"Process '{process_name}' (PID: {pid}) is a zombie candidate. Count: {self._zombie_candidates[pid]}")
                    if self._zombie_candidates[pid] >= self.GRACE_PERIOD:
                        logger.info(f"ZOMBIE CONFIRMED for '{process_name}' (PID: {pid}). Firing callback.")
                        if 'has_no_window' in self._callbacks:
                            self._callbacks['has_no_window']()
                            self._zombie_candidates = {} # Reset after firing
                            return # Exit to fire only once per tick
                else:
                    # It has a window, so it's not a zombie. Reset its candidacy.
                    if pid in self._zombie_candidates:
                        logger.debug(f"Process '{process_name}' (PID: {pid}) has a window. Vindicating.")
                        del self._zombie_candidates[pid]
            
            # Clean up candidates that are no longer running
            stale_candidates = set(self._zombie_candidates.keys()) - current_pids
            for pid in stale_candidates:
                del self._zombie_candidates[pid]
                            
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
