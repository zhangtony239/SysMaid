import wmi
import threading
import time

class Watchdog:
    def __init__(self, process_name):
        self.process_name = process_name
        self._exit_callback = None
        self._watcher_thread = None

    def is_exited(self, func):
        self._exit_callback = func
        if self._watcher_thread is None:
            self._watcher_thread = threading.Thread(target=self._watch, daemon=True)
            self._watcher_thread.start()
        return func

    def _watch(self):
        w = wmi.WMI()
        while True:
            # Check if process is running
            running_processes = w.Win32_Process(name=self.process_name)
            if not running_processes:
                if self._exit_callback:
                    self._exit_callback()
                break  # Exit the watch loop once the process has exited
            time.sleep(1)

def SetWatchdog(process_name):
    return Watchdog(process_name)

def kill(watchdog_instance):
    w = wmi.WMI()
    for process in w.Win32_Process(name=watchdog_instance.process_name):
        process.Terminate()
