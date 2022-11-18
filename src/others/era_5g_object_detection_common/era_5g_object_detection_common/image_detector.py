from abc import ABCMeta, abstractmethod
from asyncio import Queue

from era_5g_netapp_interface import ThreadBase


class InitializationFailed(Exception):
    pass


class ImageDetector(ThreadBase):
    def __init__(self, logger, name):
        super().__init__(logger, name)
        self.stopped = False
        self.time = None
        self.fps = 0.0

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def process_image(self, frame):
        pass

    @abstractmethod

    def publish_results(self, data):
        pass
        