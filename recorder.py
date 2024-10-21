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

    def __init__(self, outfolder):
        """
        Class initialization, pass camera index (for filename), the
        output fodler and the capture information (witdh, height, fps)
        """
        self.outfolder = outfolder

        self.que = queue.Queue()
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

        fourcc = cv2.VideoWriter_fourcc('a','v','c','1')
        fname = ["", "", "", "", "", "", "", "", "", "" ]
        output = [ None, None, None, None, None, None, None, None, None, None ]
        opened = [ False, False, False, False, False, False, False, False, False, False ]

        print("Video output thread starting")

        while True:
            if self.que.empty():
                time.sleep(0.1)
                continue
            e, i, f = self.que.get()
            if e == self.VIDEO_START:
                fname[i] = self.outfolder + datetime.now().strftime(OUTFORMAT)
                fname[i] += "_cam" + str(i) + OUTEXTENSION
                output[i] = cv2.VideoWriter(fname[i], fourcc, f[2], (f[0], f[1]), OUTFLAGS)
                opened[i] = True
                print(fname[i] + " start recording " + str(f))
            elif e == self.VIDEO_FRAME:
                if opened[i]:
                    output[i].write(f)
                else:
                    print("Writing but not opened")
            elif e == self.VIDEO_STOP:
                output[i].release()
                opened[i] = False
                print(fname[i] + " stop recording")
            else:
                for j in range(0, len(opened)):
                   if opened[j]:
                        print(fname[j] + " stop recording")
                        output[j].release
                print(fname[i] + " exit recording")
                break
        print("Video output thread finishing")

    def start(self, idx, w, h, fps):
        """ start a recording """
        self.que.put((self.VIDEO_START, idx, (w, h, fps)))

    def frame(self, idx, frame):
        """ store a frame in the recording file """
        self.que.put((self.VIDEO_FRAME, idx, frame))

    def stop(self, idx):
        """ stop recording """
        self.que.put((self.VIDEO_STOP, idx, None))

    def exit(self):
        """ exit from the thread function and join the thread """
        self.que.put((self.VIDEO_EXIT, 0, None))
        self.thread.join()
