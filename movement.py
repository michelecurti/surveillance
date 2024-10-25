import cv2
import threading
import queue
import time 
import numpy as np
import recorder
import exposure

# minimum detection pixel count
MIN_WHITE = 64 * 64

# max recording minutes
MAX_RECO_MINS = 1

class Movement:
    
    # fsm events
    MOVEM_START = 1
    MOVEM_FRAME = 2
    MOVEM_STOP = 3
    MOVEM_EXIT = 3

    def __init__(self, reco, expo):
       
        self.go_on = True
        self.reco = reco
        self.expo = expo
        
        self.caps = [ None ] * 10
        self.capws = [ 1600 ] * 10
        self.caphs = [ 1200 ] * 10
        self.capfs = [ 20 ] * 10
        self.lastframe = [ None ] * 10
        self.lastvalid = [ False ] * 10
        
        self.history = [ None ] * 10
        self.ticks = [ None ] * 10
        self.consec = [ 0 ] * 10
        self.register = [ 0 ] * 10
        self.regi_cnt = [ 0 ] * 10
        self.curr_frame = [ 0 ] * 10
        
        self.fgbgs = [ None ] * 10

        self.que = queue.Queue()
        self.thread = threading.Thread(target=self.thread_function)
        self.thread.start()

    def thread_function(self):

        kern_erode = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (8, 8))
        kern_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (8, 8))

        # get capture info, width, height, frames per second
        start_size = 30
        stop_size = 120

        while self.go_on:
            if self.que.empty():
                time.sleep(0.1)
                continue
            e, i, t, f = self.que.get()
            if e == self.MOVEM_START:
                # intialize variables
                self.history[i] = []
                self.ticks[i] = []
                # get capture information
                capw = int(self.caps[i].get(3))
                caph = int(self.caps[i].get(4))
                capf = int(self.caps[i].get(5))
                # get capture information
                self.capws[i] = capw
                self.caphs[i] = caph
                self.capfs[i] = capf
                # start exposure for this camera
                self.expo.start(i, self.caps[i])
                #initialize background subtractor
                self.fgbgs[i] = cv2.createBackgroundSubtractorMOG2(detectShadows = False)
                print(str(capw)+'x'+str(caph)+'@'+str(capf)+'fps', start_size, stop_size)
            if e == self.MOVEM_FRAME:
                # convert to gray
                gray = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
                # update exposure
                self.curr_frame[i] += 1
                if self.curr_frame[i] % (self.capfs[i] * 2) == 0:
                    self.expo.frame(i, gray)
                # update background
                fgmask = self.fgbgs[i].apply(gray, learningRate = 0.015)
                # fixed size frame history
                if len(self.history[i]) >= start_size:
                    self.history[i].pop(0)
                    self.ticks[i].pop(0)
                self.history[i].append(f)
                self.ticks[i].append(t)
                # if not enough history, wait
                if len(self.history[i]) < start_size:
                    continue
                real_fps = (1 + ((len(self.history[i]) - 1) * cv2.getTickFrequency()) // 
                        (self.ticks[i][-1] - self.ticks[i][0]))
                # cleanup movement mask
                fgmask = cv2.erode(fgmask, kern_erode)
                fgmask = cv2.dilate(fgmask, kern_dilate)
                if np.sum(fgmask == 255) > MIN_WHITE:
                #if self.curr_frame[i] > 100:
                    self.consec[i] += 1
                    if self.register[i] == 0:
                        if self.consec[i] >= 1 + real_fps // 2:
                            self.register[i] = stop_size
                            self.regi_cnt[i] = 0
                            # start saving video
                            self.reco.start(i, self.capws[i], self.caphs[i], real_fps)
                            # write all history frames
                            for frm in self.history[i]:
                                self.reco.frame(i, frm)
                    else:
                        self.register[i] = stop_size
                else:
                    self.consec[i] = 0
                if self.regi_cnt[i] >= MAX_RECO_MINS * 60 * real_fps:
                    print("reached", self.regi_cnt[i])
                    # max recording exceeded
                    self.regi_cnt[i] = 0
                    self.register[i] = 1
                if self.register[i] > 0:
                    self.register[i] -= 1
                    if self.register[i] == 0:
                        self.reco.stop(i)
                if self.register[i] > 0:
                    self.regi_cnt[i] += 1
                    self.reco.frame(i, f)
                    self.lastframe[i] = f
                    self.lastvalid[i] = True
    
    def start(self, idx, cap):
        self.caps[idx] = cap
        self.que.put((self.MOVEM_START, idx, cv2.getTickCount(), None))
    
    def frame(self, idx, frame):
        self.que.put((self.MOVEM_FRAME, idx, cv2.getTickCount(), frame))

    def last_frame(self, idx):
        """ get the last detection frame, used to find faces or bodies """
        if self.lastvalid[idx]:
            self.lastvalid[idx] = False
            return True, self.lastframe[idx]
        return False, None

    def exit(self):
        """ join the camera thread """
        self.go_on = False
        self.thread.join()
