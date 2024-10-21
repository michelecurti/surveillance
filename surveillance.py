import os

# set FFMPEG environment variables to use hardware encoding acceleration
os.environ["OPENCV_FFMPEG_WRITER_OPTIONS"] = "vcodec;h264_qsv"

# disable opencv errors trying to open unexisting cameras, remove in debug
os.environ["OPENCV_LOG_LEVEL"]="FATAL"

import cv2
import time
from camera import Camera
from detect import Detect
from recorder import Recorder
from exposure import Exposure

# start recorder thread
reco = Recorder("/surveillance/")

# start exposure thread
expo = Exposure()

# start detection thread
detect = Detect("/surveillance/detect/", Detect.TYPE_BODY)

# find cameras
cameras = []

if False:
    cameras += [Camera("../asd.mp4", "/surveillance/")]
else:
    for i in range (0, 6):
        time.sleep(1)
        cap = cv2.VideoCapture(i)
        if cap is not None and cap.isOpened():
            cap.release()
            print("Found camera " + str(i))
            cameras += [Camera(i, reco, expo)]

# foreach camera detect last frame every half second
curr = 0
while True:
    try:
        time.sleep(0.5)
    except:
        print("killed")
        break
    valid, frame = cameras[curr].last_frame()
    if valid:
        detect.frame(frame)
    curr += 1
    if curr >= len(cameras):
        curr = 0

for camera in cameras:
    camera.exit()

reco.exit()
expo.exit()
detect.exit()
