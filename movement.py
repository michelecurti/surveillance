import os
import cv2
import numpy as np
import time
from datetime import datetime
import threading
import queue
from camera import Camera

# set FFMPEG environment variables to use hardware encoding acceleration
os.environ["OPENCV_FFMPEG_WRITER_OPTIONS"] = "vcodec;h264_qsv"

camera = Camera(0, "/surveillance/")

camera.exit()
