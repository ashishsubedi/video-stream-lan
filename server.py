import socket
from threading import Thread, Lock, get_ident
from socketserver import ThreadingMixIn
from time import time,sleep

import numpy as np
import cv2
import pickle

TCP_IP = '0.0.0.0'
TCP_PORT = 6000
BUFFER_SIZE = 4096

RECV_FLAG = 0
SEND_FLAG = 1



ret = True
emptyFrame = np.zeros((200,200))
framesDict = {}
HEADER_SIZE = 10

streamThread = None
rootID = 'root'


class ClientThread(Thread):
    def __init__(self,ip: str,port: int,sock: socket.socket,flag,target):
        Thread.__init__(self)
        global framesDict, emptyFrame
        self.setDaemon(True)
        self.ip = ip
        self.port =  port
        self.sock = sock
        self.flag = flag
        self.target = target
        self.id = f"{ip}:{port}"
        self.frameName = f"Client {self.id}"
        self.stop = False
        framesDict[self.id] = emptyFrame.copy()
         #opencv stuff
        print(f"New thread started for {ip}:{port}. Thread ID: {self.id} ")
          

    def run(self):
        global streamThread

        if(self.flag==SEND_FLAG):
            sendStream(streamThread,self.sock,rootID)
        else:
              #Target = getVideoStream
            streamThread = Thread(target=self.target,args=(self.frameName,self.id,self))
            streamThread.setDaemon(True)
            streamThread.start()
            print(streamThread)
            self.stop = recvStream(streamThread,self.sock,self.id,self.stop)

def sendVideoStream(id):
    global ret,framesDict
    print("Sending Video stream in new Thread")
    lock = Lock()
    cap = cv2.VideoCapture(0)
    ret,newFrame = cap.read()
    while ret:
        lock.acquire()
        ret,newFrame = cap.read() 
        lock.release()
        framesDict[id]=newFrame
    cap.release()
        
def getVideoStream(frameName,id,self):
    print("Receiving Video Stream in new Thread")
    print(framesDict.keys())
    try:
        while ret:
            if(not self.is_alive()):raise Exception("THREAD OVER because DEAD")
            
            cv2.putText(framesDict[id],id, (10,20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, 255)

            cv2.imshow(frameName,framesDict[id])
            if cv2.waitKey(1) == 27:
                
                break
    except:
        print("Error in getting Video stream")
    finally:

        cv2.destroyWindow(frameName)

    

def sendStream(streamThread: Thread,sock: socket.socket,id):
    global framesDict
    try:
        while True:
            frameBytes = pickle.dumps(framesDict[id])
            print(len(frameBytes))
            header = bytes(f"{len(frameBytes):<{HEADER_SIZE}}",'utf-8')
            print("HEader value : ",header)
            sock.send(header)
            sock.sendall(frameBytes)
            sleep(0.01)
    except Exception as e:
        print(e)
        framesDict[id] = emptyFrame.copy()
        sock.close()

def recvStream(streamThread: Thread,s: socket.socket,id,self):
    global framesDict
    lock = Lock()


    frameData = b''
    print("Receiving Streams")
    try:
        while True:
            if not streamThread.is_alive(): raise Exception("THREAD OVER because DEAD")
            msgLength = s.recv(HEADER_SIZE)
            msg = msgLength.decode('utf-8')
            if not msg:
                raise Exception("THREAD OVER")
            msgLength = int(msg)
        
            while(msgLength>0):
                if(msgLength>=BUFFER_SIZE):
                    data = s.recv(BUFFER_SIZE)
                else:
                    data = s.recv(msgLength)
                frameData += data
                msgLength -= len(data)
            else:
                lock.acquire()
                framesDict[id] = pickle.loads(frameData)
                lock.release()
               
                frameData = b''  
    except Exception as e:
        print("ERROR:",e)
        s.close()
    finally:
        framesDict[id] = emptyFrame.copy()
        return True
            
def startServer():
    global streamThread

    tcpsock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    tcpsock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    tcpsock.bind((TCP_IP,TCP_PORT))

    threads = []
    flag = RECV_FLAG

    

    target = None

    if(flag==SEND_FLAG):
        target = sendVideoStream
        streamThread = Thread(target=target,args=(rootID))
        streamThread.start()
    else:
        target = getVideoStream

    while True:
        tcpsock.listen(5)
        print("Waiting for incoming connections")
        (conn,(ip,port)) = tcpsock.accept()
        print(f"[CONNECTED] Welcome, {ip}:{port} !")
        newThread = ClientThread(ip,port,conn,flag,target)
        newThread.start()
        threads.append(newThread)

    cv2.destroyAllWindows()
    for t in threads:
        print("join ",t)
        t.join()
    
    tcpsock.close()
    

if __name__ == "__main__":
    
    startServer()
    

    
