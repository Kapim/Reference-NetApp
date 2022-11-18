from threading import Thread
from abc import abstractmethod, ABCMeta

class TaskHandler(Thread):
    __metaclass__ = ABCMeta

    def __init__(self, logger, sid, websocket_id):
        super().__init__()
        self.sid = sid
        self.websocket_id = websocket_id
        self.logger = logger

    def start(self, daemon):
        self.logger.debug("Starting %s thread", self.name)
        t = Thread(target=self._run, args=())
        t.daemon = daemon
        t.start()

    def stop(self):
        self.logger.debug("Stopping %s thread", self.name)
        self.stopped = True

    @abstractmethod
    def _run(self):
        pass

    @abstractmethod
    def store_image(self, metadata, image):
        pass


