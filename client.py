import socket
# from time import time
from threading import Thread,Lock
import numpy as np
import cv2
import pickle
import errno
from time import sleep

TCP_IP = '0.0.0.0'
TCP_PORT = 6001
BUFFER_SIZE = 4096
HEADER_SIZE = 10 

s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.connect((TCP_IP,TCP_PORT))

frameData = b''
ret = True
frame = np.zeros((200,200))


def videoStream():
    global ret,frame
    print("Video Stream Started in new Thread")
    while ret:
        
        cv2.imshow("Client Frame",frame)
        if cv2.waitKey(1) == 27:
            break

    cv2.destroyAllWindows()

streamThread = Thread(target=videoStream)
streamThread.start()
lock = Lock()

while True:
    if not streamThread.isAlive(): break

    msgLength = s.recv(HEADER_SIZE)
    print(msgLength.decode('utf-8'))
    msgLength = int(msgLength.decode('utf-8'))
    while(msgLength>0):
        print("data exists")
        if(msgLength>=BUFFER_SIZE):
            data = s.recv(BUFFER_SIZE)
        else:
            data = s.recv(msgLength)
        frameData += data
        msgLength -= len(data)
    else:
        print("data poof")
        lock.acquire()
        frame = pickle.loads(frameData)
        lock.release()
        frameData = b''  

    
    

cv2.destroyAllWindows()

s.close()
        