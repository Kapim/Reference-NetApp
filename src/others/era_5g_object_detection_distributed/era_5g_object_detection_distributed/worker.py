import json
import os
from queue import Empty, Queue

import cv2
import flask_socketio
import numpy as np
from era_5g_netapp_interface import ImageDetector


class FaceDetector(ImageDetector):

    def __init__(self, logger, name, image_queue: Queue, app):
        super().__init__(logger, name)
        self.image_queue = image_queue
        self.app = app
        self.detection_cascade = cv2.CascadeClassifier(
            os.path.join("/home/ikapinus/projects/Reference-NetApp/assets", 'haarcascade_frontalface_default.xml'))

    def run(self):
        self.logger.debug(f"{self.name} thread is running.")
        
        while not self.stopped:
            # Get image and metadata from input queue
            try:
                metadata, image = self.image_queue.get(block=False)
            except Empty:
                continue
            detections = []

            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            results = self.process_image(gray)
            self.publish_results(results, metadata)
            

    def process_image(self, frame):
        # gray = cv2.resize(gray,(640,360))
            # Detect the faces
            faces = self.detection_cascade.detectMultiScale(frame, 1.35, 4)

            detections = []
            
            for bbox in faces:
                
                # Transform from x,y,w,h to x1,y1,x2,y2 (bbox top-left bottom-right corners)
                bbox[2] += bbox[0] 
                bbox[3] += bbox[1]

                # Generate random class
                cls = 1  # np.random.randint(0, 80)
                cls_name = "face"

                # Generate random detection score
                score = np.random.random()
                det = bbox, score, cls, cls_name

                # Add to other detections for processed frame
                detections.append(det)
            
            return detections

    def publish_results(self, raw_results, metadata):
        detections = list()
        for (bbox, score, cls_id, cls_name) in raw_results:
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
        
