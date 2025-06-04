#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__     = "Irakli Keshelashvili"
__copyright__  = "Copyright 2021, The CBM-STS Project"
__license__    = ""
__version__    = "2.0.1"
__maintainer__ = "Irakli Keshelashvili"
__email__      = "i.keshelashvili@gsi.de"
__status__     = "Production"

'''
This script is used as an separate process to scan the QR code 
'''


import cv2
import tesserocr
from PIL import Image

##
##
def read_number(img):

    _, thresh = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    # Convert back to PIL for tesserocr
    pil_img = Image.fromarray(thresh)
    pil_img = pil_img.convert("L")  # Convert to grayscale if not already

    # OCR
    with tesserocr.PyTessBaseAPI(psm=tesserocr.PSM.SINGLE_LINE) as api:
        api.SetVariable("tessedit_char_whitelist", "0123456789")
        api.SetImage(pil_img)
        text = api.GetUTF8Text().strip()
        confidence = api.MeanTextConf()
    
    if len(text) != 4:
        # print("Error: Not a FEB number.")
        return 0, 0
    
    return text, confidence

##
# Define the region of interest (ROI) for capturing the middle 400x200 pixels
def get_middle_frame(frame, width=600, height=200):

    frame_height, frame_width = frame.shape[:2]
    start_x = frame_width  // 2 - width // 2
    start_y = frame_height // 2 - height // 2

    end_x = start_x + width
    end_y = start_y + height
    return frame[start_y:end_y, start_x:end_x]


##
##
##
if __name__ == "__main__":

    # get the webcam:  
    cap = cv2.VideoCapture(0)

    # 160.0 x 120.0 #176.0 x 144.0 #320.0 x 240.0 #352.0 x 288.0 
    # 640.0 x 480.0 #1024.0 x 768.0 #1280.0 x 1024.0
    # https://docs.opencv.org/3.4/d4/d15/group__videoio__flags__base.html#gaeb8dd9c89c10a5c63c139bf7c4f5704d
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640.0)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480.0)
    # cap.set(cv2.CAP_PROP_MONOCHROME, 1)

    font = cv2.FONT_HERSHEY_SIMPLEX

    nn = 0
    data = ''

    while(cap.isOpened()):
        nn = nn +1
        if nn > 220:
            break
        
        # Capture frame-by-frame
        ret, frame = cap.read()
        
        key = cv2.waitKey(10) # delay 10ms
        if key == 27:  # ESC
            break

        frame = get_middle_frame(frame, 300, 100)

        # Display the resulting frame
        cv2.imshow('FEB SN',frame)

        # Our operations on the frame come here
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        try:
            text, confidence = read_number( img )
            # print(f"confidence: {confidence}")
            if confidence > 80:
                print(f"{text}")
                cv2.imwrite('report/Capture.png', frame)
                break

        except Exception as e:
            print(f"Error: {e}")
            pass


    #When everything done, release the capture
    cap.release()
    cv2.destroyAllWindows()
