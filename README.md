# surveillance
surveillance camera with python - opencv - numpy

## how to run
```
python surveillance.py
```

## camera.py -> Camera class
It's the class that detect the movement using the background subtractor method from opencv,
when a movent is detected, it starts recording to file

## recorder.py -> Recorder class
It's the class that opens the files on disc, writes the frames, closes the file, etc.. using
a separate thread, so the Camera thread does not freeze.
It uses hardware acceleration (intel N100 quicksync video h264).

## exposure.py -> Exposure class
It's the class that regulate the exposure time of the camera, because the "HW" one is too
fast and false detections are triggered. Separate thread too.

## detect.py -> Detect class
It's the class that search for faces or bodies in the detection frames and store then
to file. Separate thread.
