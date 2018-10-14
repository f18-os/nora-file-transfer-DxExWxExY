#! /usr/bin/env python3

# Echo client program
import socket, sys, re, os
import params
from framedSock import FramedStreamSock
from threading import Thread
from threading import Lock
import time

def init_client():
    global serverHost, serverPort, debug
    switchesVarDefaults = (
    (('-s', '--server'), 'server', "localhost:50001"),
    (('-d', '--debug'), "debug", False), # boolean (set if present)
    (('-?', '--usage'), "usage", False), # boolean (set if present)
    )
    progname = "Client"
    paramMap = params.parseParams(switchesVarDefaults)
    
    server, usage, debug  = paramMap["server"], paramMap["usage"], paramMap["debug"]
    
    if usage:
        params.usage()
    try:
        serverHost, serverPort = re.split(":", server)
        serverPort = int(serverPort)
    except:
        print("Can't parse server:port from '%s'" % server)
        sys.exit(1)

class ClientThread(Thread):
    def __init__(self, serverHost, serverPort, debug):
        Thread.__init__(self, daemon=False)
        self.serverHost, self.serverPort, self.debug = serverHost, serverPort, debug
        self.start()
    def run(self):
        s = None
        for res in socket.getaddrinfo(serverHost, serverPort, socket.AF_UNSPEC, socket.SOCK_STREAM):
            af, socktype, proto, canonname, sa = res
            try:
                print("creating sock: af=%d, type=%d, proto=%d" % (af, socktype, proto))
                s = socket.socket(af, socktype, proto)
            except socket.error as msg:
                print(" error: %s" % msg)
                s = None
                continue
            try:
                print(" attempting to connect to %s" % repr(sa))
                s.connect(sa)
            except socket.error as msg:
                print(" error: %s" % msg)
                s.close()
                s = None
                continue
            break   
        if s is None:
            print('could not open socket')
            sys.exit(1)
        
        fs = FramedStreamSock(s, debug=debug)
        send_message(fs, "put t.txt")
        
def send_message(fs, *args):
    user_input = args[0]
    if re.match("put\s[\w\W]+", user_input):
        trash, file = user_input.split(" ",1)
        if os.path.exists("%s/%s" % (os.getcwd(), file)):
            msg = "put " + file.rsplit('/', 1)[-1]
            fs.sendmsg(msg.encode())
            fs.sendmsg(open(file, "rb").read())
        else:
            print("\nFile Doesn't Exist.")
    elif re.match("get\s[\w\W]+", user_input):
        fs.sendmsg(user_input.encode())
        payload = fs.receivemsg()
        if payload.decode() == "true":
            trash, file = user_input.split(" ",1)
            writer = open("%s/%s" % (os.getcwd(), file), "wb+")
            payload = fs.receivemsg()
            writer.write(payload)
            writer.close()
            print("\nTransfer Done.")
        else:
            print("File not Found.")
    elif user_input == "quit":
        print("Killing Client...")
        sys.exit(0)
    else:
        fs.sendmsg(args[0].encode())
        print(fs.receivemsg())
        fs.sendmsg(args[0].encode())
        print(fs.receivemsg())

if __name__ == '__main__':
    init_client()
    for i in range(1):
        ClientThread(serverHost, serverPort, debug)