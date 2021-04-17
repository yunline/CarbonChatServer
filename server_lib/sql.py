import sqlite3
import time
import queue
import logging

class DB:
    def __init__(self):
        self.command_queue=queue.Queue()
    def _main(self):
        while 1:
            out_queue,command,args=self.command_queue.get()
            out_queue.put(command(*args))
    def thread_start(self):
        try:
            self.db_init()
            self._main()
        except Exception as err:
            self.logger.error(err)
        finally:
            self.db_cursor.close()
            self.db.close()
    def multi_thread_method(func):
        def out_func(*args):
            q=queue.Queue()
            args[0].command_queue.put((q,func,args))
            return q.get(timeout=2)
        return out_func

class UserDB(DB):

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("User database")
        
    @DB.multi_thread_method
    def register(self,username,password):
        self.db_cursor.execute("select * from users where username=?;",(username,))
        if len(self.db_cursor.fetchall())==0:
            self.db_cursor.execute(
                "insert into users values(?,?,?,?);",
                (None,username,password,time.time())
            )
            self.db.commit()
            return 1
        else:
            return 0

    @DB.multi_thread_method
    def login(self,username,password):
        self.db_cursor.execute("select * from users where username=?;",(username,))
        tmp=self.db_cursor.fetchall()
        if len(tmp)>0:
            if tmp[0][2]==password:
                return 1
            else:
                return 0
        else:
            return 0
        
    def db_init(self):
        self.db=sqlite3.connect("./users.db")
        self.db_cursor=self.db.cursor()
        self.db_cursor.execute("""
            create table if not exists users(
                id integer primary key,
                username nvarchar(20),
                password char(64),
                reg_time real);--如果不存在就新建表
            """)
        self.logger.info("User DB loaded.")


class ChatDB(DB):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("Chat history database")
    
    @DB.multi_thread_method
    def add(self,username,msg):
        self.db_cursor.execute(
                "insert into chat values(?,?,?,?);",
                (None,username,msg,time.time())
            )
        self.db.commit()

    def db_init(self):
        self.db=sqlite3.connect("./chat.db")
        self.db_cursor=self.db.cursor()
        self.db_cursor.execute("""
            create table if not exists chat(
                id integer primary key,
                username nvarchar(20),
                msg nvarchar(400),
                time real);--如果不存在就新建表
            """)
        self.logger.info("Chat history DB loaded.")

