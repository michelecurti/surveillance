import numpy as np
import threading
import queue
import cv2
import time

class Exposure:

    EXPO_FRAME = 1
    EXPO_EXIT = 2

    que = queue.Queue()

    def __init__(self, cap):

        self.cap = cap

        self.thread = threading.Thread(target=self.thread_function)
        self.thread.start()

    def thread_function(self):

        EXP_NON = 1 # exposure is fixes
        EXP_INC = 2 # exposure is increasing
        EXP_DEC = 3 # exposure is decreasing
        exp_act = EXP_NON

        EXPOSURE_COEFF = 1
        EXPOSURE_INITIAL = 78
        EXPOSURE_MIN = 1 * EXPOSURE_COEFF
        EXPOSURE_MAX = 100 * 10 * EXPOSURE_COEFF
        exposure = EXPOSURE_INITIAL * EXPOSURE_COEFF
        exposure_last = EXPOSURE_INITIAL

        self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1) # manual mode
        self.cap.set(cv2.CAP_PROP_EXPOSURE, EXPOSURE_INITIAL)
        #cap.set(cv2.CAP_PROP_AUTO_WB, 0)

        while True:
            e, f = self.que.get()
            if e == self.EXPO_FRAME:
                gray = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
                bright = np.average(gray)
                if bright < 128 - 10:
                    # if brightness is below the lower threshold, increase
                    exp_act = EXP_INC
                elif bright > 128 + 10:
                    # if brightness is above the higher threshold, decrease
                    exp_act = EXP_DEC
                if ((exp_act == EXP_INC and bright >= 128) or 
                        (exp_act == EXP_DEC and bright <= 128)):
                    # is setpoint is reached, stop the algorithm
                    exp_act = EXP_NON
                # increase or decrease the exposure time
                if exp_act == EXP_INC:
                    exposure += 1 + exposure // (EXPOSURE_COEFF * 128)
                elif exp_act == EXP_DEC:
                    exposure -= 1 - exposure // (EXPOSURE_COEFF * 128)
                # check the limits
                if exposure < EXPOSURE_MIN:
                    exposure = ESPOSURE_MIN
                elif exposure > EXPOSURE_MAX:
                    exposure = EXPOSURE_MAX
                # apply the exposure
                val = exposure // EXPOSURE_COEFF
                if val != exposure_last:
                    self.cap.set(cv2.CAP_PROP_EXPOSURE, val)
                    exposure_last = val
                #print(bright, val)
            else:
                break

    def frame(self, frame):
        self.que.put((self.EXPO_FRAME, frame))

    def exit(self):
        self.que.put((self.EXPO_EXIT, None))
        self.thread.join()
