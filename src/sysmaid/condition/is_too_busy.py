import time
import psutil
import logging
from ..maid import HardwareWatchdog

logger = logging.getLogger(__name__)

class IsTooBusyWatchdog(HardwareWatchdog):
    def __init__(self, hardware_name, over, duration):
        super().__init__(hardware_name)
        if self.name.lower() != 'cpu':
            raise ValueError("is_too_busy condition is currently only supported for 'CPU'")
        
        self.percpu = isinstance(over, list)
        if self.percpu:
            core_count = psutil.cpu_count()
            if len(over) != core_count:
                raise ValueError(f"The length of 'over' list ({len(over)}) must match the number of CPU cores ({core_count}).")
            if not all(isinstance(x, int) for x in over):
                raise ValueError("All elements in the 'over' list must be integers.")

        self.over = over
        self.duration = duration
        self.busy_start_time = None
        self._callbacks = []

    def check_state(self):
        # Currently, only CPU is implemented
        if self.name != 'cpu':
            return
            
        is_currently_busy = False
        usages = psutil.cpu_percent(interval=self.interval, percpu=self.percpu)
        
        if self.percpu:
            # When percpu is True, usages is a list of floats
            if isinstance(usages, list):
                for i, (usage, threshold) in enumerate(zip(usages, self.over)):
                    if threshold != -1 and usage > threshold:
                        is_currently_busy = True
                        logger.debug(f"CPU core {i} usage {usage}% exceeded threshold {threshold}%.")
                        break
        else:
            # When percpu is False, usages is a single float or int
            usage = usages
            if isinstance(usage, (float, int)) and usage > self.over:
                is_currently_busy = True
                logger.debug(f"Overall CPU usage {usage}% exceeded threshold {self.over}.")

        if is_currently_busy:
            if self.busy_start_time is None:
                self.busy_start_time = time.time()
                logger.debug(f"CPU busy condition met. Starting timer for {self.duration} seconds.")
            elif time.time() - self.busy_start_time >= self.duration:
                logger.info(f"CPU has been too busy for {self.duration} seconds. Triggering action.")
                for callback in self._callbacks:
                    callback()
                # Reset after triggering to avoid continuous firing
                self.busy_start_time = None
        else:
            if self.busy_start_time is not None:
                logger.debug("CPU usage fell below threshold(s). Resetting timer.")
            self.busy_start_time = None

    @property
    def is_too_busy(self):
        def decorator(func):
            self._callbacks.append(func)
            return func
        return decorator