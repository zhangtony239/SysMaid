import logging
import threading
from ..maid import BaseWmiEvent

logger = logging.getLogger(__name__)

class RunningWatchdog(BaseWmiEvent):
    def __init__(self, process_name):
        super().__init__(name=process_name, event_type='__InstanceCreationEvent')
        self._initial_check_done = False

    def _loop(self):
        """
        重写 _loop 以在启动时检查进程是否已在运行,
        然后再进入WMI事件监听循环。
        """
        import pythoncom
        import wmi
        import pywintypes
        
        logger.info(f"WMI event watcher for '{self.name}' ({self.event_type}) started in thread {threading.get_ident()}.")
        try:
            pythoncom.CoInitialize()
            c = wmi.WMI()

            # 启动时检查
            if not self._initial_check_done:
                existing_processes = c.Win32_Process(Name=self.name)
                if existing_processes:
                    logger.info(f"'{self.name}' is already running. Firing callback on start.")
                    if 'is_running' in self._callbacks:
                        self._callbacks['is_running']()
                self._initial_check_done = True

            # 进入事件监听循环
            watcher = c.ExecNotificationQuery(self.query)
            while self._is_running:
                try:
                    event = watcher.NextEvent(1000)
                    self.handle_event(event)
                except pywintypes.com_error as e:
                    if len(e.args) > 2 and e.args[2] and e.args[2][5] == -2147209215: # WBEM_S_TIMEDOUT
                        continue
                    raise
        except Exception as e:
            logger.critical(f"WMI event watcher for '{self.name}' has crashed: {e}", exc_info=True)
        finally:
            logger.info(f"WMI event watcher for '{self.name}' is shutting down.")
            pythoncom.CoUninitialize()

    def is_running(self, func):
        self._callbacks['is_running'] = func
        return func

    def handle_event(self, event):
        logger.info(f"'{self.name}' has started. Firing callback.")
        if 'is_running' in self._callbacks:
            self._callbacks['is_running']()