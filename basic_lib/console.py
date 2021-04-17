import msvcrt
import os
import sys
import time
import queue
import colorama
import io
colorama.init()

class Console(io.IOBase):
    '''win only'''
    def __init__(self):
        self.input_buff=''
        self.output_queue=queue.Queue()
        self.stdout=sys.stdout
    def read_input(self):
        ch=b''
        while msvcrt.kbhit():
            ch+=msvcrt.getch()
        try:
            return ch.decode("gb2312")
        except:
            return ''

    def get_buffer_length(self):
        return len(self.input_buff.encode("gb2312"))

    def print(self,*args,sep=''):#暂不支持end参数
        if len(self.input_buff)!=0:
            self.stdout.write("\r%s\r"%(' '*self.get_buffer_length()))
        self.stdout.write(sep.join([str(i) for i in args])+'\n')
        self.stdout.write(self.input_buff)
        self.stdout.flush()

    def write(self,s):
        if len(self.input_buff)!=0:
            self.stdout.write("\r%s\r"%(' '*self.get_buffer_length()))
        self.stdout.write(s)
        self.stdout.write(self.input_buff)
    
    def writable(self):
        return True

    def scan(self):
        #把键盘输入放入队列
        #如果只输入ascii字符则不会阻塞，如果输入汉字则会导致阻塞
        #原因未知
        i=self.read_input()
        if i=='\r':
            self.output_queue.put(self.input_buff)
            self.stdout.write("\r%s\r"%(' '*self.get_buffer_length()))
            self.input_buff=""
        elif i=='\b':
            if len(self.input_buff):
                if len(self.input_buff[-1].encode("gb2312"))==2:
                    self.stdout.write('\b\b  \b\b')
                else:
                    self.stdout.write("\b \b")
                self.input_buff=self.input_buff[:-1]
                
        elif i:
            self.input_buff+=i
            self.stdout.write(i)
    
    def thread_start(self,sleep_time=0.001):
        while 1:
            self.scan()
            time.sleep(sleep_time)