import socket
from threading import Thread, Lock
from socketserver import ThreadingMixIn
from time import time,sleep

import numpy as np
import cv2
import pickle

TCP_IP = '0.0.0.0'
TCP_PORT = 6001
BUFFER_SIZE = 4096

ret = True
frame = None
HEADER_SIZE = 10

class ClientThread(Thread):
    def __init__(self,ip: str,port: int,sock: socket.socket):
        Thread.__init__(self)
        self.ip = ip
        self.port =  port
        self.sock = sock
        print(f"New thread started for {ip}:{port} ")

    def run(self):
        try:
            while True:
                frameBytes = pickle.dumps(frame)
                print(len(frameBytes))
                header = bytes(f"{len(frameBytes):<{HEADER_SIZE}}",'utf-8')
                print("HEader value : ",header)
                self.sock.send(header)
                self.sock.sendall(frameBytes)
                sleep(0.01)
        except Exception as e:
            print(e)
            self.sock.close()

def videoStream():
    global ret,frame
    print("Video Stream Started in new Thread")
    lock = Lock()
    cap = cv2.VideoCapture(0)
    # cap.set(cv2.CAP_PROP_FRAME_WIDTH, 200)
    # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 200)
    ret,frame = cap.read()
    while ret:
        lock.acquire()
        ret,frame = cap.read() 
        lock.release()
    #     cv2.imshow("Server Frame",frame)
    #     if cv2.waitKey(1) == 27:
    #         break
    # cv2.destroyAllWindows()
    cap.release()
        

def startServer():
    tcpsock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    tcpsock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    tcpsock.bind((TCP_IP,TCP_PORT))

    threads = []
    
    #opencv stuff
    streamThread = Thread(target=videoStream)
    streamThread.start()
    

    while True:
        tcpsock.listen(5)
        print("Waiting for incoming connections")
        (conn,(ip,port)) = tcpsock.accept()
        print(f"[CONNECTED] Welcome, {ip}:{port} !")
        newThread = ClientThread(ip,port,conn)
        newThread.start()
        threads.append(newThread)

    
    for t in threads:
        t.join()
    
    tcpsock.close()
    

if __name__ == "__main__":
    
    startServer()
    cap.release()

    
