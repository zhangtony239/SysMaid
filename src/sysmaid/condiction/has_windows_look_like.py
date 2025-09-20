import logging
import mss
import cv2
import numpy as np
import time
import threading
from ..maid import HardwareWatchdog

logger = logging.getLogger(__name__)

class WindowsMatchingWatchdog(HardwareWatchdog):
    def __init__(self, hardware_name, template_image_path=None, threshold=0.8, interval=1):
        super().__init__(hardware_name)
        self.template = cv2.imread(template_image_path, 0)
        self.threshold = threshold
        self.interval = interval
        self._callbacks = {}

        if self.template is None:
            raise FileNotFoundError(f"Template image not found at path: {template_image_path}")

    def _loop(self):
        """
        Since this specific hardware watchdog requires polling,
        we override the _loop method to implement it.
        """
        logger.info(f"Watchdog for screen matching '{self.name}' started polling every {self.interval}s in thread {threading.get_ident()}.")
        try:
            while self._is_running:
                self.check_state()
                time.sleep(self.interval)
        except Exception as e:
            logger.critical(f"Watchdog thread for '{self.name}' has crashed: {e}", exc_info=True)
        finally:
            logger.info(f"Watchdog thread for '{self.name}' is shutting down.")
            
    def check_state(self):
        with mss.mss() as sct:
            monitor = sct.monitors[1]  # All monitors
            sct_img = sct.grab(monitor)
            
            img = np.array(sct_img)
            img_gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
            
            res = cv2.matchTemplate(img_gray, self.template, cv2.TM_CCOEFF_NORMED)
            loc = np.where(res >= self.threshold)
            
            if loc[0].size > 0:
                logger.info("Found image matching template on screen. Firing callback.")
                self.trigger_callback()

    def trigger_callback(self):
        if 'is_found' in self._callbacks:
            self._callbacks['is_found']()
    
    @property
    def is_found(self):
        def decorator(func):
            self._callbacks['is_found'] = func
            return func
        return decorator