import json
import logging
import queue
import random
import threading
import time

from basic_lib import flags, pack_processor, wdt,utils


class Connection:
    def __init__(self,server_obj):
        self.broadcast_queue=queue.Queue()
        self.server_obj=server_obj
    
    def broadcast_as_server(self,content):
        self.broadcast("Server",content)

    def broadcast(self,username,content):
        for i in self.server_obj.client_list:
            self.server_obj.client_list[i].broadcast_queue.put([username,content])

class ClientConnection(Connection):
    def __init__(self,server_obj,conn,address):
        super().__init__(server_obj)
        self.logged_in=0
        self.conn=conn

        self.addr=address
        self.client_id=random.randint(1,0xfffffff0)

        self.parser=pack_processor.Parser(conn,self.client_id)
        self.parser_queue=queue.Queue()
        self.send=pack_processor.Sender(conn)

        self.user_db=self.server_obj.user_db

        self.logger=logging.getLogger("Client %d"%self.client_id)

    def thread_start(self):
        try:
            self.logger.info("Client Connected. (Addr: %s, Port: %d)"%self.addr)
            threading.Thread(target=self.parser.thread_start,args=(self.parser_queue,)).start()
            self._main()
        except Exception as err:
            self.logger.error(err)
        finally:
            if self.logged_in:
                del self.server_obj.loggedin_users[self.username]
                self.broadcast_as_server("%s left the server."%self.username)
            del self.server_obj.client_list[self.client_id]
            self.conn.close()
            self.logger.info("Connection Closed.")

    def send_msg_as_server(self,content):
        self.send(flags.FLAG_MSG,{"from":"Server","content":content})

    def handle_pack(self):
        if not self.parser_queue.empty():
            flag,data=self.parser_queue.get()

            if flag==flags.FLAG_INTERRUPT:
                return 0
            elif flag==flags.FLAG_LOGIN:
                if data["username"] in self.server_obj.loggedin_users:
                    self.send_msg_as_server("You have already logged in.")
                elif self.user_db.login(data["username"],data["password"]):
                    self.timer.rm_timer("login_timeout")
                    self.server_obj.loggedin_users[data["username"]]=self.client_id
                    self.logger.info("Logged in successfully.")
                    self.logger.info("Client%d's username is %s."%(self.client_id,data["username"]))
                    self.broadcast_as_server("%s joined the server."%data["username"])
                    self.send_msg_as_server("Welcome")
                    self.username=data["username"]
                    self.logged_in=1
                else:
                    self.send_msg_as_server("Login failed.")
                    self.logger.warning("Login failed.")
                    time.sleep(1)
                    return 0
            elif flag==flags.FLAG_PING:
                #print("pang!",data)
                self.timer.feed("ping")
                self.send(flags.FLAG_PANG,data)
            elif flag==flags.FLAG_MSG:
                if self.logged_in:
                    self.broadcast(self.username,data['content'])
                else:
                    self.send_msg_as_server("You haven't logged in yet")
        return 1

    def handle_broadcast(self):
        if not self.broadcast_queue.empty():
            username,data=self.broadcast_queue.get()
            self.send(flags.FLAG_MSG,{"from":username,"content":data})

    def handle_timer(self):
        timeout_set=self.timer.check()
        if timeout_set:
            if "login_timeout" in timeout_set:
                self.send_msg_as_server("Login timeout.")
                self.logger.warning("Login timeout.")
                return 0
            if "ping" in timeout_set:
                self.send_msg_as_server("Ping timeout.")
                self.logger.warning("Ping timeout.")
                return 0
        return 1

    def _main(self):
        self.timer=wdt.Wdt()
        self.timer.new_timer("login_timeout",5)
        self.timer.new_timer("ping",30)
        while 1:
            if self.handle_pack()==0:break
            self.handle_broadcast()
            if self.handle_timer()==0:break
            time.sleep(0.01)

class RootConnection(Connection):
    def __init__(self,server_obj):
        super().__init__(server_obj)
        self.logger=logging.getLogger("RootConnection")
        self.client_id=0
        self.console=server_obj.console

    def handle_broadcast(self):
        if not self.broadcast_queue.empty():
            username,data=self.broadcast_queue.get()
            self.server_obj.chat_db.add(username,data)
            self.logger.info("chat: [%s] %s"%(username,data))

    def handle_console(self):
        if not self.console.output_queue.empty():
            cmd=self.console.output_queue.get()
            if not cmd:
                return
            if cmd[0]==":" or cmd[0]=="：":
                self.broadcast_as_server(cmd[1:])
            elif cmd[0]=="/":
                c=cmd[1:].split(" ")
                if c[0]=="stop":
                    self.broadcast_as_server("Stopping server.")
                    self.server_obj.stop()
                if c[0]=="reg":
                    self.server_obj.user_db.register(c[1],utils.convert_password(c[2]))
            else:
                self.logger.info('Unknown command "%s"'%cmd)

    def _main(self):
        while 1:
            self.handle_broadcast()
            self.handle_console()
            time.sleep(0.01)

    def thread_start(self):
        try:
            self.logger.info("Root connection started.")
            self._main()
        except Exception as err:
            self.logger.error(err)
        finally:
            pass
