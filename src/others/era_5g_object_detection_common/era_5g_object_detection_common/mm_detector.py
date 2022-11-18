import json
import os
from queue import Empty, Queue

import cv2
import flask_socketio
import numpy as np
from era_5g_object_detection_common import ImageDetector, InitializationFailed
from era_5g_object_detection_common.mmdet_utils import MODEL_VARIANTS, convert_mmdet_result
from mmdet.apis import init_detector, inference_detector


class MMDetector(ImageDetector):

    def __init__(self, logger, name,):
        super().__init__(logger, name)
        self.path_to_mmdet = os.getenv("NETAPP_MMDET_PATH", None)
        self.model_variant = os.getenv("NETAPP_MODEL_VARIANT", None)
        self.torch_device = os.getenv("NETAPP_TORCH_DEVICE", 'cpu') # 'cpu', 'cuda', 'cuda:0', etc.
        if not self.path_to_mmdet:
            raise InitializationFailed(f"Failed to load mmdet module, env variable NETAPP_MMDET_PATH not set")
        if not os.path.exists(self.path_to_mmdet):
            raise InitializationFailed(f"Failed to load mmdet module, path {self.path_to_mmdet} does not exist")
        elif not self.model_variant:
            raise InitializationFailed(f"Failed to load model, env variable NETAPP_MODEL_VARIANT not set")
        config_file = os.path.join(self.path_to_mmdet, MODEL_VARIANTS[self.model_variant]['config_file'])
        checkpoint_file = os.path.join(self.path_to_mmdet, MODEL_VARIANTS[self.model_variant]['checkpoint_file'])
        self.model = init_detector(config_file, checkpoint_file, device=self.torch_device)

    

    def process_image(self, frame):
        result = inference_detector(self.model, frame)
        return convert_mmdet_result(result, merged_data=True)

    
        
