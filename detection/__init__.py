from camera import Camera
import numpy as np 
import cv2 as cv 

camera = Camera()
camera.start()
while True : 
    frame = camera.get_processed_frame()
    cv.imshow("FaceLandmarker",frame)
    if cv.waitKey(1) & 0xFF == 27:
        break
    
camera.release()

