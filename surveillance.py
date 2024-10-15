import os
import time
from camera import Camera
from detect import Detect

# set FFMPEG environment variables to use hardware encoding acceleration
os.environ["OPENCV_FFMPEG_WRITER_OPTIONS"] = "vcodec;h264_qsv"

#camera = Camera("../asd.mp4", "/surveillance/")
camera = Camera(0, "/surveillance/")
detect = Detect("/surveillance/detect/", Detect.TYPE_BODY)

while True:
    time.sleep(0.5)
    valid, frame = camera.last_frame()
    if valid:
        detect.frame(frame)

camera.exit()
