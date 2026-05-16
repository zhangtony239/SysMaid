import logging
from ..maid import BaseWmiEvent

logger = logging.getLogger(__name__)

class RunningWatchdog(BaseWmiEvent):
    def __init__(self, process_name):
        super().__init__(name=process_name, event_type='__InstanceCreationEvent')
        self._initial_check_done = False

    def start(self):
        # 在启动事件监听前，先做一次性检查
        # 这避免了重写_loop所带来的代码重复
        if not self._initial_check_done:
            import pythoncom
            import wmi
            
            pythoncom.CoInitialize()
            try:
                c = wmi.WMI()
                existing_processes = c.Win32_Process(Name=self.name)
                if existing_processes:
                    logger.info(f"'{self.name}' is already running. Firing callback on start.")
                    if 'is_running' in self._callbacks:
                        self._callbacks['is_running']()
            finally:
                pythoncom.CoUninitialize()

            self._initial_check_done = True
        
        # 调用父类的start，启动标准的事件监听循环
        super().start()

    def is_running(self, func):
        self._callbacks['is_running'] = func
        return func

    def handle_event(self, event):
        logger.info(f"'{self.name}' has started. Firing callback.")
        if 'is_running' in self._callbacks:
            self._callbacks['is_running']()