from threading import Thread
from queue import Queue
from era_5g_netapp_interface.task_handler_gstreamer import TaskHandlerGstreamer


class TaskHandlerGstreamerInternalQ(TaskHandlerGstreamer):

    def __init__(self, logger, sid, websocket_id, port: str, image_queue: Queue):
        super().__init__(logger, sid, websocket_id, port)
        self._q = image_queue
        self.port = port
        self.sid = sid
        self.websocket_id = websocket_id
        self.logger = logger

    def store_image(self, metadata, image):
        self._q.put((metadata, image), block=False)
