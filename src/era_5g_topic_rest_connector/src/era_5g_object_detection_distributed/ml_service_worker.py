# Celery worker

import logging
import os
#import cv2
import numpy as np

from celery import Celery, Task
from celery.signals import worker_process_init

from typing import Dict  # for Python 3.9, just 'dict' will be fine

import rospy


broker_url = "amqp://" + rospy.get_param('~rabbitmq_URL') + ":5672"  #os.environ.get("CELERY_BROKER_URL", "amqp://af7a0517bee554c1a95910dfb61565ce-1587996923.eu-west-1.elb.amazonaws.com:5672")
redis_url = "redis://" + rospy.get_param('~redis_URL') + ":6379"  #os.environ.get("CELERY_RESULT_BACKEND", "redis://a79eab390f0754dbfbdd6206b1cfaf3c-262201860.eu-west-1.elb.amazonaws.com:6379")

rospy.loginfo(broker_url)
rospy.loginfo(redis_url)
app = Celery('tasks', broker=broker_url, backend=redis_url)
app.conf.task_serializer = 'pickle'
app.conf.result_serializer = 'pickle'
app.conf.accept_content = ['pickle']
@app.task()
def detector_task(data):

    from mmdet.apis import init_detector, inference_detector
    from mmdet.core import get_classes

    from era_5g_helpers import get_path_to_assets, get_path_from_env
    from era_5g_helpers.mmdet_utils import MODEL_VARIANTS, convert_mmdet_result
    metadata, image = data
    
    detections = detector_worker.inference(image)
    
    results = (metadata, detections)
    return results



