import time
import psutil
import logging
import threading
from ..maid import HardwareWatchdog

logger = logging.getLogger(__name__)

class IsTooBusyWatchdog(HardwareWatchdog):
    def __init__(self, hardware_name, over, duration):
        super().__init__(hardware_name)
        if self.name.lower() != 'cpu':
            raise ValueError("is_too_busy condition is currently only supported for 'CPU'")
        self.over = over
        self.duration = duration
        self.busy_start_time = None
        self._callbacks = []

        # Asynchronously pre-warm all processes' CPU usage stats in the background
        prewarm_thread = threading.Thread(target=self._async_prewarm_processes, daemon=True)
        prewarm_thread.start()

    def _async_prewarm_processes(self):
        """
        Iterates through all processes to initialize their cpu_percent calculation.
        This is intended to run in a background thread to not block startup.
        """
        logger.debug("Starting background pre-warming of process CPU stats...")
        for p in psutil.process_iter():
            try:
                p.cpu_percent(interval=None)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        logger.debug("Background pre-warming of process CPU stats completed.")

    def check_state(self):
        # 目前只实现CPU
        if self.name == 'cpu':
            usage = psutil.cpu_percent(interval=1)
            if usage > self.over:
                if self.busy_start_time is None:
                    self.busy_start_time = time.time()
                    logger.debug(f"CPU usage {usage}% exceeded {self.over}%. Starting timer.")
                elif time.time() - self.busy_start_time >= self.duration:
                    logger.info(f"CPU usage has been over {self.over}% for {self.duration} seconds. Triggering action.")
                    for callback in self._callbacks:
                        callback()
                    # Reset after triggering to avoid continuous firing
                    self.busy_start_time = None 
            else:
                if self.busy_start_time is not None:
                    logger.debug(f"CPU usage {usage}% fell below {self.over}%. Resetting timer.")
                self.busy_start_time = None

    @property
    def is_too_busy(self):
        def decorator(func):
            self._callbacks.append(func)
            return func
        return decorator