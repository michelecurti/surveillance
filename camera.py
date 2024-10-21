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

    def __init__(self, idx, reco, expo):
        """
        Class initialization, pass the camera index and the output
        folder where to store the detected videos.
        The index can be a video path+filename, to test the detection
        algotihm with an existing video
        """
        self.lastframe = None
        self.lastvalid = False

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
            #cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
            cap = cv2.VideoCapture(self.idx, cv2.CAP_V4L2, CAPFLAGS)
            output_folder = "/surveillance/"
            # set camera properties
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1600)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1200)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)
            STOP_SIZE = 20

        # get capture info, width, height, frames per second
        capw = int(cap.get(3))
        caph = int(cap.get(4))
        capf = int(cap.get(5))

        start_size = capf * 5 # start recording 5 seconds before movement
        stop_size = capf * STOP_SIZE # stop recording 20 seconds after movement

        # print detection information
        print(str(capw)+'x'+str(caph)+'@'+str(capf)+'fps', start_size, stop_size)

        self.expo.start(self.idx, cap)

        history = []
        consec = 0
        register = 0
        regi_cnt = 0
        curr_frame = 0

        while self.go_on:
            ret, frame = cap.read()
            if not ret:
                break
            # update exposure
            curr_frame += 1
            if curr_frame % (capf * 2) == 0:
                self.expo.frame(self.idx, frame)
            # update background
            fgmask = fgbg.apply(frame, learningRate = 0.015)
            # fixed size frame history
            if len(history) >= start_size:
                history.pop(0)
            history.append(frame)
            # if not enough history, wait
            if len(history) < start_size:
                continue
            # cleanup movement mask
            fgmask = cv2.erode(fgmask, kern_erode)
            fgmask = cv2.dilate(fgmask, kern_dilate)
            if np.sum(fgmask == 255) > MIN_WHITE:
            #if curr_frame > 5 * capf:
                consec += 1
                if register == 0:
                    if consec >= capf // 2:
                        register = stop_size
                        regi_cnt = 0
                        # start saving video
                        self.reco.start(self.idx, capw, caph, capf)
                        # write all history frames
                        for frm in history:
                            self.reco.frame(self.idx, frm)
                            regi_cnt += 1
                else:
                    register = stop_size
            else:
                consec = 0
            if regi_cnt >= MAX_RECO_MINS * 60 * capf:
                # max recording exceeded
                regi_cnt = 0
                register = 1
            if register > 0:
                register -= 1
                if register == 0:
                    self.reco.stop(self.idx)
            if register > 0:
                regi_cnt += 1
                self.reco.frame(self.idx, frame)
                self.lastframe = frame
                self.lastvalid = True
            #cv2.imshow('Motion Mask', fgmask)
        # release the capture instance
        cap.release()
        # destroy all cv2 windows, if any
        cv2.destroyAllWindows()

    def last_frame(self):
        """ get the last detection frame, used to find faces or bodies """
        if self.lastvalid:
            self.lastvalid = False
            return True, self.lastframe
        return False, None

    def exit(self):
        """ join the camera thread """
        self.go_on = False
        self.thread.join()
