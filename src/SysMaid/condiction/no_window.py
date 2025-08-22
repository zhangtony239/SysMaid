import logging
import wmi
from ..maid import Watchdog

logger = logging.getLogger(__name__)

class NoWindowWatchdog(Watchdog):
    def __init__(self, process_name):
        super().__init__(process_name)
        self._no_window_checks_count = 0
        self.GRACE_PERIOD = 3  # 3 seconds

    def has_no_window(self, func):
        self._callbacks['has_no_window'] = func
        return func

    def check_state(self, c, pids_with_windows):
        process_name = self.process_name
        try:
            processes = c.Win32_Process(name=process_name)
            if not processes:
                if self._no_window_checks_count > 0:
                    logger.debug(f"'{process_name}' is no longer running. Resetting zombie check.")
                    self._no_window_checks_count = 0
                return

            current_pids = {p.ProcessId for p in processes}
            
            app_has_a_window = any(pid in pids_with_windows for pid in current_pids)

            if app_has_a_window:
                if self._no_window_checks_count > 0:
                    logger.debug(f"'{process_name}' has a visible window. Vindicating.")
                    self._no_window_checks_count = 0
            else:
                self._no_window_checks_count += 1
                logger.debug(f"'{process_name}' has no visible windows. Zombie check count: {self._no_window_checks_count}/{self.GRACE_PERIOD}")
                if self._no_window_checks_count >= self.GRACE_PERIOD:
                    logger.info(f"ZOMBIE CONFIRMED for app '{process_name}'. All processes lack windows. Firing callback.")
                    if 'has_no_window' in self._callbacks:
                        self._callbacks['has_no_window']()
                        self._no_window_checks_count = 0
                        
        except wmi.x_wmi as e:
            logger.error(f"WMI query for '{process_name}' failed: {e}")
