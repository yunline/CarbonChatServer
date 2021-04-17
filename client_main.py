import json
import queue
import random
import socket
import threading
import time
import os
from socket import AF_INET, SOCK_STREAM
from socket import socket as Socket
import traceback

from basic_lib import console, flags, pack_processor, wdt,utils

default_settings={"addr":"127.0.0.1","port":14514,"username":"user","password":"sbbbbbbbbbbb","debug":0}
try:
    f=open("./client_config.json","r")
    default_settings.update(json.loads(f.read()))
except:
    f=open("./client_config.json","w")
    f.write(json.dumps(default_settings,indent=1))
finally:
    try:f.close()
    except:pass
USERNAME=default_settings["username"]
PASSWORD=default_settings["password"]
ADDR=default_settings["addr"]
PORT=default_settings["port"]
DEBUG=default_settings["debug"]

class Client:
    def __init__(self):
        global print
        self.timeout_cnt=0
        self.conn=Socket(AF_INET,SOCK_STREAM)
        self.parser=pack_processor.Parser(self.conn,int(),timeout=0.025)
        self.send=pack_processor.Sender(self.conn)
        self.timer=wdt.Wdt()
        self.pack_queue=queue.Queue()
        self.console=console.Console()
        threading.Thread(target=self.console.thread_start).start()
        print=self.console.print

    def login(self,username,password):
        h=utils.convert_password(password)
        self.send(flags.FLAG_LOGIN,{"username":username,"password":h})
    
    def ping(self):
        self.send(flags.FLAG_PING,random.randint(0x0001,0xffff))
        self.timer.feed("ping")

    def handle_packs(self):
        while not self.pack_queue.empty():
            flag,data=self.pack_queue.get()
            if flag==flags.FLAG_PANG:
                pass
            elif flag==flags.FLAG_MSG:
                print("[%(from)s] %(content)s"%data)

    def handle_console(self):
        if not self.console.output_queue.empty():
            msg=self.console.output_queue.get()
            if msg:self.send(flags.FLAG_MSG,{"from":None,"content":msg})
    
    def handle_parser(self):
        try:
            for pack in self.parser.listen():
                self.pack_queue.put(pack)
                self.timeout_cnt=0
        except socket.timeout:
            self.timeout_cnt+=1
            if self.timeout_cnt==200:
                self.ping()
            elif self.timeout_cnt>399:
                return 0
        return 1

    def _main(self):
        print("Connecting")
        self.conn.connect((ADDR,PORT))
        print("Successfully connected to server (%s,%d)"%(ADDR,PORT))
        self.login(USERNAME,PASSWORD)
        self.timer.new_timer("ping",20)
        while 1:
            if "ping" in self.timer.check():
                ping()
            
            self.handle_packs()
            self.handle_console()
            if self.handle_parser()==0:
                break
    
    def main(self):
        try:
            self._main()
        except:
            if DEBUG:
                traceback.print_exc()
            input("Press any key to exit.")
            self.conn.close()
            os._exit(0)
                


c=Client()
c.main()
