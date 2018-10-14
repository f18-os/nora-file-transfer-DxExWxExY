#! /usr/bin/env python3
import sys, os, socket, params, time, re
from threading import Thread
from threading import Event
from framedSock import FramedStreamSock

def init_server():
    global sock, debug, lsock
    switchesVarDefaults = (
        (('-l', '--listenPort') ,'listenPort', 50001),
        (('-d', '--debug'), "debug", False), # boolean (set if present)
        (('-?', '--usage'), "usage", False), # boolean (set if present)
        )

    progname = "echoserver"
    paramMap = params.parseParams(switchesVarDefaults)

    debug, listenPort = paramMap['debug'], paramMap['listenPort']

    if paramMap['usage']:
        params.usage()

    lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # listener socket
    bindAddr = ("127.0.0.1", listenPort)
    lsock.bind(bindAddr)
    lsock.listen(5)
    print("listening on:", bindAddr)

class ServerThread(Thread):
    requestCount = 0            # one instance / class
    def __init__(self, sock, debug):
        Thread.__init__(self, daemon=True)
        self.fsock, self.debug = FramedStreamSock(sock, debug), debug
        self.start()
    def run(self):
        global event
        while True:
            if event.wait():
                event.clear()
                server_protocols(self.fsock)
                event.set()

def server_protocols(fsock):
    payload = fsock.receivemsg()
    if payload:
        print("Received: ", payload.decode())
        if re.match("put\s[\w\W]+", payload.decode()):
            trash, file = payload.decode().split(" ",1)
            if not os.path.exists("%s/__pycache__/%s" % (os.getcwd(), file)):
                writer = open("%s/__pycache__/%s" % (os.getcwd(), file), "wb+")
                fsock.sendmsg("start".encode())
                payload = fsock.receivemsg()
                writer.write(payload)
                writer.close()
                print("Transfer Done.")
            else:
               fsock.sendmsg("File Already Exists.".encode()) 
        elif re.match("get\s[\w\W]+", payload.decode()):
            trash, file = payload.decode().split(" ",1)
            if os.path.exists("%s/__pycache__/%s" % (os.getcwd(),file)):
                fsock.sendmsg("true".encode())
                fsock.sendmsg(open("%s/__pycache__/%s" % (os.getcwd(),file), "rb").read(), 1)
                print("Transfer Done.")
            else:
                fsock.sendmsg("File Doesn't Exist.".encode())
        else:
            fsock.sendmsg("Received".encode())
    else:
        event.set()
        return
            
if __name__ == '__main__':
    init_server()
    event = Event()
    event.set()
    while True:
        sock, addr = lsock.accept()
        ServerThread(sock, debug)