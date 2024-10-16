from datetime import datetime
import threading
import queue
import cv2
import time

class Recorder:

    VIDEO_START = 1
    VIDEO_FRAME = 2
    VIDEO_STOP = 3
    VIDEO_EXIT = 4

    que = queue.Queue()

    def __init__(self, idx, outfolder, capinfo):
        """
        Class initialization, pass camera index (for filename), the
        output fodler and the capture information (witdh, height, fps)
        """
        self.idx = idx
        self.outfolder = outfolder
        self.capinfo = capinfo

        self.thread = threading.Thread(target=self.thread_function)
        self.thread.start()

    def thread_function(self):
        """
        Wait for a recording event:
        - START = open the file
        - FRAME = store the frame
        - STOP = close the file
        - EXIT = exit from thread
        """
        OUTFORMAT = "%Y_%m_%d_%H_%M_%S"
        OUTEXTENSION = ".mp4"
        OUTFLAGS = (cv2.VIDEOWRITER_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY)

        capw, caph, capf = self.capinfo
        fourcc = cv2.VideoWriter_fourcc('a','v','c','1')
        opened = False

        print("Video output thread starting")

        while True:
            if self.que.empty():
                time.sleep(0.1)
                continue
            e, f = self.que.get()
            if e == self.VIDEO_START:
                fname = self.outfolder + datetime.now().strftime(OUTFORMAT)
                fname += "_cam" + str(self.idx) + OUTEXTENSION
                output = cv2.VideoWriter(fname, fourcc, capf, (capw, caph), OUTFLAGS)
                opened = True
                print(fname + " start recording")
            elif e == self.VIDEO_FRAME:
                output.write(f)
            elif e == self.VIDEO_STOP:
                output.release()
                opened = False
                print(fname + " stop recording")
            else:
                if opened:
                    print(fname + " stop recording")
                    output.release
                print(fname + " exit recording")
                break
        print("Video output thread finishing")

    def start(self):
        """ start a recording """
        self.que.put((self.VIDEO_START, None))

    def frame(self, frame):
        """ store a frame in the recording file """
        self.que.put((self.VIDEO_FRAME, frame))

    def stop(self):
        """ stop recording """
        self.que.put((self.VIDEO_STOP, None))

    def exit(self):
        """ exit from the thread function and join the thread """
        self.que.put((self.VIDEO_EXIT, None))
        self.thread.join()
