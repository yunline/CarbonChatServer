import re
from basic_lib import flags
import json
import logging

class Parser:
    def __init__(self,conn,_id,timeout=0):
        self._id=_id
        self.logger=self.logger = logging.getLogger("Parser %d"%self._id)
        self.conn=conn
        if timeout:self.conn.settimeout(timeout)

    def recv(self,length):
        tmp=self.conn.recv(length)
        if tmp:
            return tmp
        else:
            raise Exception("Disconnected.")

    def listen(self):
        buff=b''
        while 1:
            if len(buff)<8:
                buff+=self.recv(1024)

            re_tmp=re.search(flags.PACK_START,buff)

            if re_tmp:
                pack_start_point=re_tmp.span()[1]
                tmp=buff[pack_start_point:pack_start_point+8]
                pack_len=int.from_bytes(tmp,"big")
                buff=buff[pack_start_point+8:]

                if len(buff)<pack_len:
                    buff+=self.recv(pack_len-len(buff))
                    if len(buff)<pack_len:
                        continue

                pack=buff[:pack_len]
                buff=buff[pack_len:]
                yield json.loads(pack.decode())
            
            else:#如果没有找到包头，就清空缓冲区
                buff=b''

    def thread_start(self,event_queue):
        try:
            for pack in self.listen():
                event_queue.put(pack)
        except Exception as err:
            self.logger.error(err)
            event_queue.put([flags.FLAG_INTERRUPT,None])

class Sender:
    def __init__(self,conn):
        self.conn=conn
    def __call__(self,flag,data):
        content=json.dumps([flag,data],ensure_ascii=True).encode()
        head=flags.PACK_START+int(len(content)).to_bytes(8,"big")
        self.conn.send(head+content)