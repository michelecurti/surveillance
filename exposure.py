import numpy as np
import threading
import queue
import cv2
import time

EXPOSURE_COEFF = 1
EXPOSURE_INITIAL = 78
EXPOSURE_MIN = 1 * EXPOSURE_COEFF
EXPOSURE_MAX = 5000 * EXPOSURE_COEFF

EXPO_SETP = 128 # brightness setpoint
EXPO_HYST = 10 # brightness hysteresis

EXP_NON = 1 # exposure is fixed
EXP_INC = 2 # exposure is increasing
EXP_DEC = 3 # exposure is decreasing

class Exposure:

    EXPO_START = 1
    EXPO_FRAME = 2
    EXPO_EXIT = 3

    def __init__(self):
        """
        Class initialization, pass the opencv Capure instance so we can
        set the exposure parameters
        """
        self.que = queue.Queue()
        self.thread = threading.Thread(target=self.thread_function)
        self.thread.start()

        self.caps = [ None ] * 10
        self.exp_act = [ EXP_NON ] * 10
        self.exposure = [ 0 ] * 10
        self.exposure_last = [ 0 ] * 10

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

        while True:
            e, i, f = self.que.get()
            if e == self.EXPO_START:
                self.caps[i] = f
                self.caps[i].set(cv2.CAP_PROP_AUTO_EXPOSURE, 1) # manual mode
                self.caps[i].set(cv2.CAP_PROP_EXPOSURE, EXPOSURE_INITIAL)
                self.exposure[i] = EXPOSURE_INITIAL * EXPOSURE_COEFF
                self.exposure_last[i] = EXPOSURE_INITIAL
                print("Exposure algorithm for cap ", i, f)
            elif e == self.EXPO_FRAME:
                gray = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
                bright = np.average(gray)
                if bright < EXPO_SETP - EXPO_HYST:
                    # if brightness is below the lower threshold, increase
                    self.exp_act[i] = EXP_INC
                elif bright > EXPO_SETP + EXPO_HYST:
                    # if brightness is above the higher threshold, decrease
                    self.exp_act[i] = EXP_DEC
                if ((self.exp_act[i] == EXP_INC and bright >= EXPO_SETP) or
                        (self.exp_act[i] == EXP_DEC and bright <= EXPO_SETP)):
                    # is setpoint is reached, stop the algorithm
                    self.exp_act[i] = EXP_NON
                # increase or decrease the exposure time
                if self.exp_act[i] == EXP_INC:
                    self.exposure[i] += 1 + self.exposure[i] // (EXPOSURE_COEFF * 128)
                elif self.exp_act[i] == EXP_DEC:
                    self.exposure[i] -= 1 - self.exposure[i] // (EXPOSURE_COEFF * 128)
                # check the limits
                if self.exposure[i] < EXPOSURE_MIN:
                    self.exposure[i] = ESPOSURE_MIN
                elif self.exposure[i] > EXPOSURE_MAX:
                    self.exposure[i] = EXPOSURE_MAX
                # apply the exposure
                val = self.exposure[i] // EXPOSURE_COEFF
                if val != self.exposure_last[i]:
                    self.caps[i].set(cv2.CAP_PROP_EXPOSURE, val)
                    self.exposure_last[i] = val
                #print(bright, val)
            else:
                break

    def start(self, idx, cap):
        self.que.put((self.EXPO_START, idx, cap))

    def frame(self, idx, frame):
        """ add frame to the frame queue """
        self.que.put((self.EXPO_FRAME, idx, frame))

    def exit(self):
        """ exit from the thread function and join the thread """
        self.que.put((self.EXPO_EXIT, 0, None))
        self.thread.join()
