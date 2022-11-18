import cv2
from era_5g_netapp_interface.task_handler import TaskHandler
from queue import Full


class TaskHandlerGstreamer(TaskHandler):

    def __init__(self, logger, sid, websocket_id, port: str):
        super().__init__(logger, sid, websocket_id)
        self.port = port
        
    def _run(self):
        camSet=f'udpsrc port={self.port} caps="application/x-rtp,media=(string)video,encoding-name=(string)H264,payload=(int)96"   ! rtpjitterbuffer ! rtph264depay ! avdec_h264 ! videorate ! videoconvert ! appsink'
        
        try:
            self.logger.info(f"creating capture on port {self.port}")
            cap = cv2.VideoCapture(camSet)
            self.logger.info("capture created")
        except:
            self.logger.info("capture fail")
            exit(1)

        while (True):
            _, frame = cap.read()
            timestamp = cap.get(cv2.CAP_PROP_POS_MSEC)
            try:
                self._q.put(({"sid": self.sid, "websocket_id": self.websocket_id, "timestamp": timestamp}, frame), block=False)
                
            except Full:
                pass
