import os

import cv2
import numpy as np
from era_5g_object_detection_common import ImageDetector, InitializationFailed


MODEL_FILE = os.getenv("NETAPP_FACE_DETECTOR_MODEL_FILE", None)

class FaceDetector(ImageDetector):

    def __init__(self, logger, name, **kw):
        super().__init__(logger, name)
        print("face_detector")
        if MODEL_FILE is None:
            raise InitializationFailed("Failed to initialize detector, env variable NETAPP_FACE_DETECTOR_MODEL_FILE not set")
        elif not os.path.exists(MODEL_FILE):
            raise InitializationFailed(f"Failed to initialize detector, {MODEL_FILE} does not exist!")
        self.detection_cascade = cv2.CascadeClassifier(MODEL_FILE)

   
    def process_image(self, frame):
            # Detect the faces
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.detection_cascade.detectMultiScale(gray, 1.35, 4)

            detections_raw = []
            
            for bbox in faces:
                
                # Transform from x,y,w,h to x1,y1,x2,y2 (bbox top-left bottom-right corners)
                bbox[2] += bbox[0] 
                bbox[3] += bbox[1]

                # Generate random class
                cls = 1  # np.random.randint(0, 80)
                cls_name = "face"

                # Generate random detection score
                score = 0
                det = bbox, score, cls, cls_name

                # Add to other detections for processed frame
                detections_raw.append(det)

            

            return detections_raw

    
        
