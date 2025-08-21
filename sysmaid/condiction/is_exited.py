import logging
import wmi
from ..maid import Watchdog

logger = logging.getLogger(__name__)

class ExitedWatchdog(Watchdog):
    def __init__(self, process_name):
        super().__init__(process_name)
        self._has_appeared = False

    def is_exited(self, func):
        self._callbacks['is_exited'] = func
        return func

    def check_state(self, c, pids_with_windows):
        process_name = self.process_name
        try:
            processes = c.Win32_Process(name=process_name)
            if not processes:
                # Process is not running
                if self._has_appeared:
                    logger.info(f"'{process_name}' has exited after appearing. Firing callback.")
                    if 'is_exited' in self._callbacks:
                        self._callbacks['is_exited']()
                    self._has_appeared = False  # Reset for next appearance
            else:
                # Process is running
                if not self._has_appeared:
                    logger.info(f"'{process_name}' has appeared. Monitoring for exit.")
                    self._has_appeared = True
        except wmi.x_wmi as e:
            logger.error(f"WMI query for '{process_name}' failed: {e}")