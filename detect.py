import cv2
import threading
import queue
import os
import numpy as np
from datetime import datetime

def resize_with_padding(image, wsize, hsize):
    h, w = image.shape[:2]
    scale = min(wsize / w, hsize / h)
    new_w = int(w * scale)
    new_h = int(h * scale)
    resized_image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    padded_image = np.zeros((hsize, wsize, 3), dtype=np.uint8)
    x_offset = (wsize - new_w) // 2
    y_offset = (hsize - new_h) // 2
    padded_image[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = resized_image
    return padded_image

def croppa(img, x, y, w, h, maxw, maxh):
    x1 = x - 10
    x2 = x + w + 10
    if x1 < 0:
        x1 = 0
    if x2 > maxw:
        x2 = maxw
    y1 = y - 10
    y2 = y + h + 10
    if y1 < 0:
        y1 = 0
    if y2 > maxh:
        y2 = maxh
    return True, img[y1 : y2, x1 : x2]

class Detect:

    TYPE_FACE = 1
    TYPE_BODY = 2

    DETECT_FRAME = 1
    DETECT_EXIT = 2

    que = queue.Queue()

    def __init__(self, outfolder, dtyp):

        if not os.path.exists(outfolder):
            os.makedirs(outfolder)

        self.outfolder = outfolder

        if dtyp == self.TYPE_FACE:
            self.face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
            self.imgh = 64
        else:
            self.face_cascade = cv2.CascadeClassifier('haarcascade_fullbody.xml')
            self.imgh = 128

        self.thread = threading.Thread(target=self.thread_function)
        self.thread.start()

    def thread_function(self):
        OUTFORMAT = "%Y_%m_%d_%H_%M_%S"
        count = 0
        while True:
            e, fr = self.que.get()
            if e == self.DETECT_FRAME:
                gray = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
                faces, _, weights = self.face_cascade.detectMultiScale3(gray, scaleFactor=1.3, 
                        minNeighbors=4, minSize=(20, 20), outputRejectLevels=True)
                #print("Found %d faces on frame" % (len(faces)))
                fa = 0
                for (x, y, w, h) in faces:
                    if weights[fa] < 1.5:
                        continue
                    fa+= 1
                    ret, cf = croppa(fr, x, y, w, h, fr.shape[1], fr.shape[0])
                    if ret:
                        count +=1
                        rp = resize_with_padding(cf, 64, self.imgh)
                        fname = self.outfolder + datetime.now().strftime(OUTFORMAT)
                        cv2.imwrite(fname + "_d%09df%02d.jpg" % (count,fa), rp)
            else:
                break

    def frame(self, frame):
        self.que.put((self.DETECT_FRAME, frame))

    def exit(self):
        self.que.put((self.DETECT_EXIT, None))
        self.thread.join()

