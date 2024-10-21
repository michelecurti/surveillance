import numpy as np
import threading
import queue
import cv2
import time

EXPO_SETP = 128 # brightness setpoint
EXPO_HYST = 10 # brightness hysteresis

class Exposure:

    EXPO_FRAME = 1
    EXPO_EXIT = 2

    def __init__(self, cap):
        """
        Class initialization, pass the opencv Capure instance so we can
        set the exposure parameters
        """
        self.cap = cap

        self.que = queue.Queue()
        self.thread = threading.Thread(target=self.thread_function)
        self.thread.start()

    def thread_function(self):
        """
        Wait for a new frame or an exit event, when a new frame is
        received, calculate the average brightness and set the exposure
        accordingly.
        There is some hysteresis:
         - when the brightness is less than the lower threshold,
           increase the exposure until the setpoint is reached
         - when the brightness is more than the higher threshold,
           decrease the exposure until the setpoint is reached
        """

        print("Exposure algorithm for cap " + str(self.cap))

        EXP_NON = 1 # exposure is fixed
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
                if bright < EXPO_SETP - EXPO_HYST:
                    # if brightness is below the lower threshold, increase
                    exp_act = EXP_INC
                elif bright > EXPO_SETP + EXPO_HYST:
                    # if brightness is above the higher threshold, decrease
                    exp_act = EXP_DEC
                if ((exp_act == EXP_INC and bright >= EXPO_SETP) or
                        (exp_act == EXP_DEC and bright <= EXPO_SETP)):
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
        """ add frame to the frame queue """
        self.que.put((self.EXPO_FRAME, frame))

    def exit(self):
        """ exit from the thread function and join the thread """
        self.que.put((self.EXPO_EXIT, None))
        self.thread.join()
