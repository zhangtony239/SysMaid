import logging
from ..maid import BaseWmiEvent

logger = logging.getLogger(__name__)

class ExitedWatchdog(BaseWmiEvent):
    def __init__(self, process_name):
        super().__init__(name=process_name, event_type='__InstanceDeletionEvent')

    def is_exited(self, func):
        self._callbacks['is_exited'] = func
        return func

    def handle_event(self, event):
        logger.info(f"'{self.name}' has exited. Firing callback.")
        if 'is_exited' in self._callbacks:
            self._callbacks['is_exited']()