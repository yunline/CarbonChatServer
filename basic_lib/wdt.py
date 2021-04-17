import time
class Wdt:
    class Timer:
        def __init__(self,delay):
            self.last_reset=time.time()
            self.delay=delay
        def is_timeout(self):
            if self.last_reset+self.delay<=time.time():
                return 1
            else:
                return 0
        def reset(self):
            self.last_reset=time.time()
    def __init__(self):
        self.timers={}
    def new_timer(self,name,delay):
        self.timers[name]=self.Timer(delay)
    def rm_timer(self,name):
        del self.timers[name]
    def check(self):
        out=[]
        for name in self.timers:
            if self.timers[name].is_timeout():
                out.append(name)
        return set(out)
    def feed(self,name):
        self.timers[name].reset()