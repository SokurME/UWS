#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'yan9yu'

import cv2
import numpy as np

#######   training part    ###############
samples = np.loadtxt('../data/generalsamples.data', np.float32)
responses = np.loadtxt('../data/generalresponses.data', np.float32)
responses = responses.reshape((responses.size, 1))

model = cv2.ml.KNearest_create()
model.train(samples, cv2.ml.ROW_SAMPLE, responses)

############################# testing part  #########################


im = cv2.imread('../data/test.png')
# im = cv2.imread('../data/photo.jpg')

out = np.zeros(im.shape, np.uint8)

# img_hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
# img_mask = cv2.inRange(img_hsv, (0, 0, 0), (0, 255, 255))
# contours, hierarchy = cv2.findContours(img_mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
# cv2.imshow('t', img_mask)
#
gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
thresh = cv2.adaptiveThreshold(gray, 255, 1, 1, 45, 10)
contours, hierarchy = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

cv2.imshow('t', thresh)


for cnt in contours:
    area = cv2.contourArea(cnt)
    if 600 > area > 30:
        [x, y, w, h] = cv2.boundingRect(cnt)
        if 25 < h < 50:
            cv2.rectangle(im, (x, y), (x + w, y + h), (0, 255, 0), 2)
            roi = thresh[y:y + h, x:x + w]
            roismall = cv2.resize(roi, (10, 10))
            roismall = roismall.reshape((1, 100))
            roismall = np.float32(roismall)
            retval, results, neigh_resp, dists = model.findNearest(roismall, k=1)
            string = str(int((results[0][0])))
            print(string)
            cv2.putText(out, string, (x, y + h), 0, 1, (0, 255, 0))

cv2.imshow('im', im)
cv2.imshow('out', out)

while 1:
    cv2.waitKey(10)
