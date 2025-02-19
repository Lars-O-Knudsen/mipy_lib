

# This is a micropython module that is used to keep/retain a defined number of the most recent log 
# entries in the memory of the device running a mipy application.
# 
# Messages are kept by logging level. So you define how many INFO,WARNING,ERROR & CRITICAL 
# most recent messages are to be kept separately. This way INFO messages will not move any
# ERROR messages out of view.
#
# Messages are kept in chonological order depite being kept by log level. Each log message 
# is assigned a sequental id that helps keep messages in order.
#
# It works by adding an instance of LogRetainHandler as a handler to logging.
# The LogRetainHandler contructor takes two parameters:
#   - retain: a dict[log_level,number_to_retain]
#           Example: {logging.INFO:50,logging.WARNING:20,logging.ERROR:15,logging.CRITICAL:15}
#           The DEFAULT_RETAIN var contains the default config.
#  - level: the minimum level to be kept at all
#
# Filters can be applied using the LogRetainFilter class. This will enable you to keep
# a defined number of entries for a [name,level] combination. 
# Example: if you have a recurring task FREQ_LOG_TASK that logs often, it will squeeze out more infrequent
#          logging tasks. By setting up the FREQ_LOG_TASK to log under the name "FREQ_LOG_TASK" (using ContextLogger) you can then
#          create a filter LogRetainFilter("FREQ_LOG_TASK", logging.INFO, 10) and add it to the LogRetainHandler.
#          Now only the 10 most recent INFO logs from FREQ_LOG_TASK will be retained and there will be room
#          for more infrequent logged INFO messages as well.
# You can also use the predefined LogRetainSuppress class to suppress messages from a certain logger all together.

import logging 
from collections import OrderedDict
import gc

DEFAULT_RETAIN = {logging.DEBUG:50,logging.INFO:50,logging.WARNING:20,logging.ERROR:15,logging.CRITICAL:15}


class LogRetainFilter():
    """Perform filtering in the retained messages"""

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
    """Retain latest log messages by log level"""
    
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
        """Generator that returns currently retained messages and their log seq #"""
        for idx,txt in self._index.items():
            yield idx,txt


    def get(self, data, logger):
        """ Convienience method that makes it possible to add this class as
            a resource to the webserver (server.py) directly:
                    logRetainers = [h for h in logger.handlers if isinstance( h, LogRetainHandler)]
                    if len(logRetainers) > 0:
                        app.add_resource( logRetainers[0], "/api/log", logger=logger)
            A list of the retained messages and their log seq # will be returned
            with newest entry first
        """
        for idx in reversed(list(self._index.keys())):
            yield f"{idx}> {self._index[idx]}\n"
        gc.collect()
        yield f"{len(self._index)} log items retained. Memory: {gc.mem_alloc()} alloc, {gc.mem_free()} free."
