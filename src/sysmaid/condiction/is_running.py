import logging
from ..maid import BaseWmiEvent

logger = logging.getLogger(__name__)

class RunningWatchdog(BaseWmiEvent):
    def __init__(self, process_name):
        super().__init__(name=process_name, event_type='__InstanceCreationEvent')

    def is_running(self, func):
        self._callbacks['is_running'] = func
        return func

    def handle_event(self, event):
        logger.info(f"'{self.name}' has started. Firing callback.")
        if 'is_running' in self._callbacks:
            self._callbacks['is_running']()