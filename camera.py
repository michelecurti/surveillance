import cv2
import threading
import numpy as np
import recorder
import exposure

# capture flags
CAPFLAGS = (cv2.CAP_PROP_HW_ACCELERATION, cv2.CAP_PROP_HW_DEVICE)

# minimum detection pixel count
MIN_WHITE = 64 * 64

# max recording minutes
MAX_RECO_MINS = 5

class Camera:

    def __init__(self, idx, reco, expo, move):
        """
        Class initialization, pass the camera index and the output
        folder where to store the detected videos.
        The index can be a video path+filename, to test the detection
        algotihm with an existing video
        """
        self.lastframe = None
        self.lastvalid = False

        self.move = move
        self.idx = idx
        self.reco = reco
        self.expo = expo
        self.is_file = not isinstance(idx, int)
        self.go_on = True

        self.thread = threading.Thread(target=self.thread_function)
        self.thread.start()

    def thread_function(self):
        """
        The detection method is based on the backgroung subtracion method.
        The detection image is cleaned up with an erode + dilate to
        remove noise then, if a movement is detected the video is stored
        into the output folder.
        There is a buffer of 5 seconds, so we record the 5 seconds before
        the movement, and there is a follow-up time of 20 seconds, so the
        recording stops after 20 seconds from the last movement
        """

        print("Starting camera " + str(self.idx))

        fgbg = cv2.createBackgroundSubtractorMOG2(detectShadows = False)
        kern_erode = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (8, 8))
        kern_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (8, 8))

        # capure device, set resolution and frame rate
        if self.is_file:
            cap = cv2.VideoCapture(self.idx)
            output_folder = "./"
            STOP_SIZE = 5
        else:
            cap = cv2.VideoCapture(self.idx)
            #cap = cv2.VideoCapture(self.idx, cv2.CAP_V4L2, CAPFLAGS)
            output_folder = "/surveillance/"
            # set camera properties
            #cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1600)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1200)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)
            STOP_SIZE = 20

        # get capture info, width, height, frames per second
        capw = int(cap.get(3))
        caph = int(cap.get(4))
        capf = int(cap.get(5))

        # start movement detection for this camera
        self.move.start(self.idx, cap)

        while self.go_on:
            ret, frame = cap.read()
            if not ret:
                break
            self.move.frame(self.idx, frame)
        # release the capture instance
        cap.release()
        # destroy all cv2 windows, if any
        cv2.destroyAllWindows()

    def last_frame(self):
        """ get the last detection frame, used to find faces or bodies """
        return self.move.last_frame(self.idx)

    def exit(self):
        """ join the camera thread """
        self.go_on = False
        self.thread.join()
