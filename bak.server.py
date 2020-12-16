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
threads = []

camThreads = {}


class ClientThread(Thread):
    def __init__(self,ip: str,port: int,sock: socket.socket,flag,target,id):
        Thread.__init__(self)
        global framesDict, emptyFrame
        self.daemon = True
        self.ip = ip
        self.port =  port
        self.sock = sock
        self.flag = flag
        self.target = target
        self.id = id
        self.stop = False
        framesDict[self.id] = emptyFrame.copy()
        


        print(f"New thread started for {ip}:{port}. Thread ID: {self.id} ")


    def run(self):
        
        global streamThread

        if(self.flag==SEND_FLAG):
            sendStream(streamThread,self.sock,rootID)
        else:
       
            self.stop = recvStream(streamThread,self.sock,self.id,self)

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
    print("Receiving Streams",self.stop)
    try:
        while not self.stop:
            msgLength = s.recv(HEADER_SIZE)
            msg = msgLength.decode('utf-8')
            if not msg:
                raise Exception("THREAD OVER BOOHO")
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
        print("I'm exiting")
        framesDict[id] = emptyFrame.copy()
        del framesDict[id]
        return True
            
def startServer():
    global streamThread,threads

    tcpsock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    tcpsock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    tcpsock.bind((TCP_IP,TCP_PORT))

    flag = RECV_FLAG

    

    target = None

    if(flag==SEND_FLAG):
        target = sendVideoStream
        streamThread = Thread(target=target,args=(rootID))
        streamThread.start()
    else:
        # target = getVideoStream
        pass

    while True:
        tcpsock.listen(5)
        print("Waiting for incoming connections")
        (conn,(ip,port)) = tcpsock.accept()
        print(f"[CONNECTED] Welcome, {ip}:{port} !")
        id =f"{ip}:{port}"
    

        newThread = ClientThread(ip,port,conn,flag,target,id)
        newThread.start()
        threads.append(newThread)
    

    for t in threads:
        print("join ",t)
        t.join()
    
    tcpsock.close()
    


CAM_OPEN = True
def openCVThread():

    prev = {}
    while CAM_OPEN:

        print(framesDict.keys())
        curr = list(framesDict)
        orphans = set(prev)
        for id in curr:
            if id in orphans:
                orphans.remove(id)
            cv2.imshow(id,framesDict[id])
            if(cv2.waitKey(1)==27):
                cv2.destroyWindow(id)

        for orphan in orphans:
            cv2.destroyWindow(orphan)
        prev = curr
    cv2.destroyAllWindows()

if __name__ == "__main__":
    serverThread = Thread(target=startServer)     
    serverThread.start()
    # startServer()
    openCVThread()

    

    
