import logging
import mss
import cv2
import numpy as np
import os
from ..maid import HardwareWatchdog

logger = logging.getLogger(__name__)

# 避免在SYSTEM账户下运行时，工作目录被强制指向System32的问题
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class WindowsMatchingWatchdog(HardwareWatchdog):
    def __init__(self, hardware_name, template_image_path=None, threshold=0.8, interval=1):
        super().__init__(hardware_name)
        self.interval = interval  # 设置轮询间隔，基类的_loop将会使用它

        if not template_image_path:
            raise ValueError("A template image path must be provided for WindowsMatchingWatchdog.")

        # 如果路径是相对路径，则转换为基于项目根目录的绝对路径
        if not os.path.isabs(template_image_path):
            path = os.path.join(_BASE_DIR, template_image_path)
        else:
            path = template_image_path
        
        self.template = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
        self.threshold = threshold
        self._callbacks = {}

        if self.template is None:
            raise FileNotFoundError(f"Template image not found at path: {path}")
            
    def check_state(self):
        if self.template is None:
            # This path should not be reached due to the check in __init__,
            # but we add it for type checker robustness and safety.
            logger.warning("Template image is not loaded, skipping screen check.")
            return

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