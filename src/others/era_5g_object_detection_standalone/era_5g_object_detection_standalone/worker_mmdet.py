from queue import Queue

from era_5g_object_detection_common import MMDetector
from worker import Worker


class MMDetectorWorker(Worker, MMDetector):

    def __init__(self, logger, name, image_queue: Queue, app):
        super().__init__(logger=logger, name=name, image_queue=image_queue, app=app)