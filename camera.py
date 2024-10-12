import cv2
import threading
import numpy as np
import recorder
import exposure

# capture flags
CAPFLAGS = (cv2.CAP_PROP_HW_ACCELERATION, cv2.CAP_PROP_HW_DEVICE)

# minimum detection pixel count
MIN_WHITE = 64 * 64

class Camera:

    def __init__(self, idx, outfolder):

        self.idx = idx
        self.outfolder = outfolder
        self.is_file = not isinstance(idx, int)
        
        self.thread = threading.Thread(target=self.thread_function)
        self.thread.start()
    
    def thread_function(self):

        fgbg = cv2.createBackgroundSubtractorMOG2(detectShadows = False)
        kern_erode = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (8, 8))
        kern_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (8, 8))

        # capure device, set resolution and frame rate
        if self.is_file:
            cap = cv2.VideoCapture('vtest.webm')
            output_folder = "./"
            STOP_SIZE = 5
        else:
            #cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
            cap = cv2.VideoCapture(0, cv2.CAP_V4L2, CAPFLAGS)
            output_folder = "/surveillance/"
            # set camera properties
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1600)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1200)
            STOP_SIZE = 20

        capw = int(cap.get(3))
        caph = int(cap.get(4))
        capf = int(cap.get(5))

        # start recorder thread
        reco = recorder.Recorder(self.idx, self.outfolder, (capw, caph, capf))

        # start exposure algorithm thread
        expo = exposure.Exposure(cap)

        start_size = capf * 5 # start recording 5 seconds before movement
        stop_size = capf * STOP_SIZE # stop recording 20 seconds after movement

        # print detection information
        print(str(capw)+'x'+str(caph)+'@'+str(capf)+'fps', start_size, stop_size)

        history = []
        consec = 0
        register = 0
        curr_frame = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            # update exposure
            curr_frame += 1
            if curr_frame % 10 == 0:
                expo.frame(frame)
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
                consec += 1
                if register == 0:
                    if consec == capf // 2:
                        register = stop_size
                        # start saving video 
                        reco.start()
                        # write all history frames
                        for frm in history:
                            reco.frame(frm)
                else:
                    register = stop_size
            else:
                consec = 0
            if register > 0:
                register -= 1
                if register == 0:
                    reco.stop()
            if register > 0:
                reco.frame(frame)
            #cv2.imshow('Motion Mask', fgmask)
        reco.exit()
        expo.exit()
        cap.release()
        cv2.destroyAllWindows()

    def exit(self):
        self.thread.join()