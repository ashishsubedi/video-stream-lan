import socket
from threading import Thread,Lock
import numpy as np
import cv2
import pickle
import errno
from time import sleep

testImg = 'median.jpg'


BUFFER_SIZE = 1024
HEADER_SIZE = 10 

RECV_FLAG = 0
SEND_FLAG = 1

PORT = np.random.randint(3000,8000)

ret = True
frame = np.zeros((200,200))
print(f"Hello, I am 0.0.0.0:{PORT}")


# TCP_IP = input("Enter Other Client IP:")



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
        cap = cv2.VideoCapture(0)
        ret,frame = cap.read()
        while ret:
            lock.acquire()
            ret,frame = cap.read()
            # frame = cv2.imread(testImg)
            lock.release()
    except:
        cap.release()
        pass

def sendStreamUDP(streamThread: Thread,s):
    try:
        while ret:
            frameBytes = pickle.dumps(frame)
            msgLen = len(frameBytes)
            
            header = bytes(f"{msgLen:<{HEADER_SIZE}}",'utf-8')
            print("HEader value : ",header)
            s.sendto(header,(TCP_IP,TCP_PORT))
            print("Header sent")
         
            offset = 0
            while msgLen>0:
                dataSize = BUFFER_SIZE if (BUFFER_SIZE<msgLen) else msgLen
                print(dataSize)
                data = frameBytes[offset:min(offset+dataSize,len(frameBytes))-1]
               
                s.sendto(data,(TCP_IP,TCP_PORT))
                msgLen -= dataSize

            sleep(0.01)
    except Exception as e:
        print("SEnding Error:",e)
        s.close()

def sendStreamTCP(streamThread: Thread,s):
    try:
        while ret:
            frameBytes = pickle.dumps(frame)
            msgLen = len(frameBytes)
            
            header = bytes(f"{msgLen:<{HEADER_SIZE}}",'utf-8')
            print("HEader value : ",header)
            s.send(header)
         
            
            s.sendall(frameBytes)
            

            sleep(0.01)

    except Exception as e:
        print("SEnding Error:",e)
        s.close()

def recvStream(streamThread,s):
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
    # flag = SEND_FLAG
 

    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.bind(('0.0.0.0',PORT))

    flag = int(input("Enter Flag (0 to receive, 1 to send): "))
    target = None
    if( not flag):
        # Receiving Stream
        s.listen(1)
        conn,addr = s.accept()
        print(f'{addr} Joined Connection')
        sleep(0.1)

        target=getVideoStream
    else:
        #sending Stream
        TCP_IP = '0.0.0.0'
        TCP_PORT = int(input("Enter Other Client PORT:"))
        s.connect((TCP_IP,TCP_PORT))
        print(f'Connected to {TCP_IP}:{TCP_PORT}')
        sleep(0.1)

        target=sendVideoStream
        
    # streamThread = Thread(target=target)
    # streamThread.start()

    recvStreamThread = Thread(target=getVideoStream)
    sendStreamThread = Thread(target=sendVideoStream)
    sendStreamThread.start()
    recvStreamThread.start()
    if not flag:
        recvStream(recvStreamThread,conn)
        sendStreamTCP(sendStreamThread,conn)
    else:
        recvStream(sendStreamThread,s)
        sendStreamTCP(recvStreamThread,s)



    
    

cv2.destroyAllWindows()

s.close()
        