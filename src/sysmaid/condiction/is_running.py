import logging
import wmi
from ..maid import Watchdog

logger = logging.getLogger(__name__)

class RunningWatchdog(Watchdog):
    def __init__(self, process_name):
        super().__init__(process_name)
        self._is_running = False

    def is_running(self, func):
        self._callbacks['is_running'] = func
        return func

    def check_state(self, c, pids_with_windows):
        process_name = self.process_name
        try:
            processes = c.Win32_Process(name=process_name)
            if processes:
                # Process is running
                if not self._is_running:
                    logger.info(f"'{process_name}' is running. Firing callback.")
                    if 'is_running' in self._callbacks:
                        self._callbacks['is_running']()
                    self._is_running = True
            else:
                # Process is not running
                if self._is_running:
                    logger.info(f"'{process_name}' has stopped. Resetting state.")
                    self._is_running = False
        except wmi.x_wmi as e:
            logger.error(f"WMI query for '{process_name}' failed: {e}")