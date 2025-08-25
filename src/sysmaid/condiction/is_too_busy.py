import time
from collections import deque
import logging
from ..maid import HardwareWatchdog

logger = logging.getLogger(__name__)

class IsTooBusyWatchdog(HardwareWatchdog):
    def __init__(self, hardware_name, over, duration):
        super().__init__(hardware_name)
        self._over = over
        self._duration = duration
        self._history = deque(maxlen=duration)
        self._is_busy = False
        self._last_trigger_time = 0
        self._callbacks = []

    def check_state(self):
        """
        检查硬件利用率，并根据是否超过阈值来触发回调。
        """
        if self.name == 'cpu':
            processors = self.c.Win32_Processor()
            current_load = sum(p.LoadPercentage for p in processors) / len(processors) if processors else 0
            
            self._history.append(current_load > self._over)

            is_currently_busy = all(self._history) and len(self._history) == self._duration

            if is_currently_busy:
                current_time = time.time()
                # 首次进入繁忙状态，或者距离上次触发已超过duration，则再次触发
                if not self._is_busy or (current_time - self._last_trigger_time) >= self._duration:
                    if not self._is_busy:
                        logger.info(f"CPU usage has been over {self._over}% for {self._duration} seconds. Entering busy state.")
                    else:
                        logger.info("CPU usage remains high. Re-triggering actions.")
                    
                    for callback in self._callbacks:
                        callback()
                    
                    self._is_busy = True
                    self._last_trigger_time = current_time
            
            # 如果之前是繁忙状态，但现在不再满足条件，则重置
            elif self._is_busy and not is_currently_busy:
                logger.info("CPU usage has returned to normal. Exiting busy state.")
                self._is_busy = False
                # 当退出繁忙时，清空历史，以便下一次能快速判断
                self._history.clear()
        else:
            # RAM/GPU 的实现可以稍后添加
            pass

    @property
    def is_too_busy(self):
        """
        一个装饰器属性，用于注册当硬件过于繁忙时要执行的回调函数。
        """
        def decorator(func):
            self._callbacks.append(func)
            return func
        return decorator