
from mipy_lib import logging 
from collections import OrderedDict
import gc

DEFAULT_RETAIN = {logging.DEBUG:50,logging.INFO:50,logging.WARNING:20,logging.ERROR:15,logging.CRITICAL:15}


class LogRetainFilter():

    def __init__(self, name:str, level=logging.INFO, count=10):
        self.name:str = name
        self.level:int = level
        self.count:int = count
        self._index:list = list()


    def filter(self, logSeq:int, rec:logging.LogRecord):
        rm = None
        if rec.name == self.name and rec.levelno == self.level:
            if len(self._index) >= self.count:
                rm = self._index.pop(0)
            self._index.append(logSeq)
        return rm
    

class LogRetainSuppress(LogRetainFilter):
    """ Special filter to suppress log entries for specific (emitter;level) all together"""

    def filter(self, logSeq:int, rec:logging.LogRecord):
        """ In order to suppress new item, return it as the 'toRemove' item """
        if rec.name == self.name and rec.levelno == self.level:
            return logSeq
        


class LogRetainHandler(logging.Handler):
    
    def __init__(self, retain=DEFAULT_RETAIN, level=logging.INFO):
        super().__init__(level)
        self.retainSetup:dict = retain
        self.level = level
        self.logSeq:int = 0
        self._index:OrderedDict[int,str] = OrderedDict()    # index of all retained log entries, to get order right
        self._retain:dict[int,list] = {}                    # dict with retain list (seq no) for each log level
        for k in self.retainSetup.keys():
            self._retain[k] = list()
        self._filters:list[LogRetainFilter] = list()        # list of filters to process before adding new entry


    # record:
        # self.name = name
        # self.levelno = level
        # self.levelname = _level_dict[level]
        # self.message = message
        # self.ct = time.time()
        # self.msecs = int((self.ct - int(self.ct)) * 1000)
        # self.asctime = None

    def emit(self, record:logging.LogRecord):
        """ Called whenever something is logged.
            Checks with filters if entries are to be rolled
            and then checks with the retain setup if entries need to be rolled
        """
        if record.levelno >= self.level: # is log level in scope?
            self.logSeq += 1
            lvlRecs = self._retain.get(record.levelno)  # the retained log entries for given level
            for filter in self._filters: # process any filters
                toRemove = filter.filter(self.logSeq,record)
                if toRemove: # Filter wants to remove this logSeq# from retainer
                    if toRemove == self.logSeq: # Its current item, leave
                        return                    
                    try: # remove from history
                        lvlRecs.pop( lvlRecs.index(toRemove) )
                    finally:
                        pass
                    self._index.pop(toRemove)
            self._index[self.logSeq] = self.format(record)
            if len(lvlRecs) >= self.retainSetup.get(record.levelno): # check if historic entry must go to accept new
                rm = lvlRecs.pop(0)
                self._index.pop(rm)
            lvlRecs.append(self.logSeq)


    def addFilter(self, filter):
        self._filters.append(filter)


    async def getLogEntries(self):
        for idx,txt in self._index.items():
            yield idx,txt


    def get(self, data, logger):
        for idx in reversed(list(self._index.keys())):
            yield f"{idx}> {self._index[idx]}\n"
        gc.collect()
        yield f"{len(self._index)} log items retained. Memory: {gc.mem_alloc()} alloc, {gc.mem_free()} free."
