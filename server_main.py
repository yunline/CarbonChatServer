import logging
import os
import sys
import threading
import queue
import time
from socket import AF_INET, SOCK_STREAM
from socket import socket as Socket

from basic_lib import console,flags
from server_lib import connection, sql
from server_lib.load_config import server_config


class Server:
    def __init__(self):
        self.console=console.Console()
        threading.Thread(target=self.console.thread_start).start()

        logging.basicConfig(
            stream=self.console,
            level = logging.INFO,
            format = '[%(levelname)s][%(asctime)s][%(name)s] %(message)s'
        )
        self.logger = logging.getLogger("Server Main")

        self.addr=server_config["ipv4_addr"]
        self.port=server_config["port"]
        self.loggedin_users={}

        self.command_queue=queue.Queue()

        self.user_db=sql.UserDB()
        threading.Thread(target=self.user_db.thread_start).start()

        self.chat_db=sql.ChatDB()
        threading.Thread(target=self.chat_db.thread_start).start()
    
    def stop(self):
        for i in self.client_list:
            if i!=0:
                self.logger.info("Stopping %d"%i)
                self.client_list[i].parser_queue.put({flags.FLAG_INTERRUPT,None})
        
        time.sleep(1)
        os._exit(0)

    def run(self):
        root=connection.RootConnection(self)
        self.client_list={0:root}
        threading.Thread(target=root.thread_start).start()
        threading.Thread(target=self.thread_start).start()
            

    def thread_start(self):
        self.main_socket=Socket(AF_INET,SOCK_STREAM)
        self.main_socket.bind((self.addr,self.port))
        self.main_socket.listen()
        
        self.logger.info("Server successfuly started on %s:%d (PID:%d)"%(self.addr,self.port,os.getpid()))

        while 1:
            client=connection.ClientConnection(self,*self.main_socket.accept())
            self.client_list[client.client_id]=client
            threading.Thread(target=client.thread_start).start()


s=Server()
s.run()
