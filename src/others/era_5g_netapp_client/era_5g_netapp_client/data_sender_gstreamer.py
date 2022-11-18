from threading import Thread

import cv2


class DataSenderGStreamer(Thread):

    def __init__(self, ip, port, data_source: str):
        self.ip = ip
        self.port = port
        #v4l2src device=/dev/video0
        gst_str = f"{data_source} ! video/x-raw, format=YUY2, width=640, height=480, pixel-aspect-ratio=1/1 ! videoconvert ! appsink"

        gst_str_rtp = f'appsrc ! videoconvert ! queue ! x264enc  speed-preset=ultrafast  tune=zerolatency  byte-stream=true threads=4 key-int-max=15 intra-refresh=true ! h264parse ! rtph264pay ! queue ! udpsink host={self.ip} port={self.port} '
        self.out = cv2.VideoWriter(gst_str_rtp, cv2.CAP_GSTREAMER, 0, float(52), (640, 360), True)
        self.cap = cv2.VideoCapture(gst_str,cv2.CAP_GSTREAMER)
        t = Thread(target=self.run, args=())
        t.daemon = True
        t.start()

    def run(self):
        while True:
            ret, frame = self.cap.read()
            if ret == False:
                break
            self.out.write(frame)