import pymurapi as mur
import time
import cv2 as cv
import numpy as np


auv = mur.mur_init() 

def detect_coord_blue_objects(image):
    img_hsv = cv.cvtColor(image, cv.COLOR_BGR2HSV)
    
    lower_red = np.array([60,35,140])
    upper_red = np.array([180,255,255])
    mask = cv.inRange(img_hsv, lower_red, upper_red)
    contours, hierarchy = cv.findContours(mask, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
    cv.drawContours(image, contours, -1, (128,0,0), 1)
    return contours
    
    #for cnt in contours:
    #    (x,y),radius = cv.minEnclosingCircle(cnt)
     #   print(y)
     #   if 110<(y)<130:
    #        return y
            
    

def detect_coord_white_objects(image):
    img_hsv = cv.cvtColor(image, cv.COLOR_BGR2HSV)
    lower_red = np.array([0,0,255])
    upper_red = np.array([255,255,255])
    mask = cv.inRange(img_hsv, lower_red, upper_red)
    
    contours, hierarchy = cv.findContours(mask, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)  
    cv.drawContours(image, contours, -1, (128,0,0), 1)
    return contours
    
 #   for cnt in contours:
#        (x,y),radius = cv.minEnclosingCircle(cnt)
  #      print(y)
   #     if 110<(y)<130:
    #        return y
            
     
    cv.waitKey(5)    
            
def turn_right():
    yaw = auv.get_yaw()
    while yaw <= 90: 
        auv.set_motor_power(0, 5)
        yaw = auv.get_yaw()
        print(yaw)
    auv.set_motor_power(1, 5)
    
for i in range(50):
    auv.set_motor_power(0, -1)
    auv.set_motor_power(1, -1)
    
flag= 0
while True:
    
    image = auv.get_image_bottom()
    cv.imshow("Image", image)
    contour_blue = detect_coord_blue_objects(image) 
    contour_white = detect_coord_blue_objects(image) 
    for cnt in contour_blue:
        (x,y),radius = cv.minEnclosingCircle(cnt)
        if 119<int(y)<131:
            turn_right()
            flag=1
            break
        
            
    depth = auv.get_depth()
    cv.waitKey(5)
    
    
    