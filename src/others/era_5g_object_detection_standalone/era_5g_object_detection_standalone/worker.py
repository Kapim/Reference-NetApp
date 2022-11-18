from queue import Empty, Queue
import flask_socketio
from era_5g_object_detection_common import ImageDetector

class Worker(ImageDetector):

    def __init__(self, image_queue: Queue, app, **kw):
        super().__init__(**kw)
        self.image_queue = image_queue
        self.app = app

    def run(self):
        self.logger.debug(f"{self.name} thread is running.")
        
        while not self.stopped:
            # Get image and metadata from input queue
            try:
                metadata, image = self.image_queue.get(block=False)
            except Empty:
                continue
            
            detections = self.process_image(image)

            self.publish_results(detections, metadata)
            


    def publish_results(self, results, metadata):
        detections = list()
        for (bbox, score, cls_id, cls_name) in results:
            det = dict()
            det["bbox"] = [float(i) for i in bbox]
            det["score"] = float(score)
            det["class"] = int(cls_id)
            det["class_name"] = str(cls_name)
            
            detections.append(det)
        
        r = {"timestamp": metadata["timestamp"],
                "detections": detections}
            
            
        with self.app.app_context():              
                flask_socketio.send(r, namespace='/results', to=metadata["websocket_id"])