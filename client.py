import socket
from threading import Thread,Lock
import numpy as np
import cv2
import pickle
import errno
from time import sleep

testImg = 'median.jpg'

TCP_IP = '0.0.0.0'
TCP_PORT = 6000
BUFFER_SIZE = 4096
HEADER_SIZE = 10 

RECV_FLAG = 0
SEND_FLAG = 1

s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.connect((TCP_IP,TCP_PORT))

ret = True
frame = np.zeros((200,200))


def getVideoStream():
    global ret,frame
    print("Receiving Video Stream in new Thread")
    while ret:
        
        cv2.imshow("Client Frame",frame)
        if cv2.waitKey(1) == 27:
            break

    cv2.destroyAllWindows()

def sendVideoStream():
    global ret,frame
    print("Video Stream Started in new Thread")
    lock = Lock()
    try:
        # cap = cv2.VideoCapture(0)
        # ret,frame = cap.read()
        while ret:
            lock.acquire()
            # ret,frame = cap.read()
            frame = cv2.imread(testImg)
            lock.release()
    except:
        # cap.release()
        pass

def sendStream(streamThread: Thread):
    try:
        while ret:
            frameBytes = pickle.dumps(frame)
            print(len(frameBytes))
            header = bytes(f"{len(frameBytes):<{HEADER_SIZE}}",'utf-8')
            print("HEader value : ",header)
            s.send(header)
            s.sendall(frameBytes)
            sleep(0.01)
    except Exception as e:
        print(e)
        s.close()

def recvStream(streamThread):
    global ret,frame
    lock = Lock()


    frameData = b''
    print("Receiving Streams")

    while True:
        if not streamThread.is_alive(): break
        msgLength = s.recv(HEADER_SIZE)
        msgLength = int(msgLength.decode('utf-8'))

        while(msgLength>0):
            if(msgLength>=BUFFER_SIZE):
                data = s.recv(BUFFER_SIZE)
            else:
                data = s.recv(msgLength)
            frameData += data
            msgLength -= len(data)
        else:
            lock.acquire()
            frame = pickle.loads(frameData)
            lock.release()
            frameData = b''  

if __name__ == "__main__":

    flag = SEND_FLAG
    target = None
    if( not flag):
        # Receiving Stream
        target=getVideoStream
    else:
        #sending Stream
        target=sendVideoStream
        
    streamThread = Thread(target=target)
    streamThread.start()

    if not flag:
        recvStream(streamThread)
    else:
        sendStream(streamThread)



    
    

cv2.destroyAllWindows()

s.close()
        