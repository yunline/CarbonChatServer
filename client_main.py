import json
import queue
import random
import socket
import threading
import time
import os
from socket import AF_INET, SOCK_STREAM
from socket import socket as Socket

from basic_lib import console, flags, pack_processor, wdt,utils


#USERNAME,PASSWORD=input("Username >> "),input("Password >> ")
USERNAME,PASSWORD="YL12c","ccccc"

class Client:
    def __init__(self):
        global print
        self.timeout_cnt=0
        self.conn=Socket(AF_INET,SOCK_STREAM)
        #self.conn.connect(("mc.icyiso.xyz",14514))
        self.conn.connect(("127.0.0.1",14514))
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
            self.conn.close()
            os._exit(0)
                


c=Client()
c.main()
