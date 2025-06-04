#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__     = "Irakli Keshelashvili"
__copyright__  = "Copyright 2021, The CBM-STS Project"
__license__    = ""
__version__    = "2.29.24"
__email__      = "i.keshelashvili@gsi.de"
__status__     = "Production"

'''
This script is used as an separate process to scan the QR code 
'''

import pyzbar.pyzbar as pyzbar
import cv2

# get the webcam:  
cap = cv2.VideoCapture(0)

# 160.0 x 120.0 #176.0 x 144.0 #320.0 x 240.0 #352.0 x 288.0 
# 640.0 x 480.0 #1024.0 x 768.0 #1280.0 x 1024.0
# https://docs.opencv.org/3.4/d4/d15/group__videoio__flags__base.html#gaeb8dd9c89c10a5c63c139bf7c4f5704d
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640.0)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480.0)
cap.set(cv2.CAP_PROP_MONOCHROME, 1)

font = cv2.FONT_HERSHEY_SIMPLEX

nn = 0
data = ''

while(cap.isOpened()):
    nn = nn +1
    if nn > 2e2: 
        break
    
    # Capture frame-by-frame
    ret, frame = cap.read()
    
    key = cv2.waitKey(1) # delay 10ms
    if key == 27:  # ESC
        break

    # Display the resulting frame
    cv2.imshow('Module QR',frame)

    # Our operations on the frame come here
    im = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    #Find barcodes and QR codes
    decodedObjects = pyzbar.decode(im)

    if len(decodedObjects) == 1:
        if decodedObjects[0].type == 'QRCODE':
            data = decodedObjects[0].data.decode()
            cv2.imwrite('report/Capture.png', frame)                
            break

print( data )

#When everything done, release the capture
cap.release()
cv2.destroyAllWindows()
