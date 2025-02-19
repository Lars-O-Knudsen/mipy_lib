
import logging

class TailLogHandler(logging.Handler):
    
    def __init__(self, tailLen=50, level=logging.NOTSET):
        super().__init__(level)
        self.tailLen = tailLen
        self.tail = list()
        self.logCount = 0


    # record:
        # self.name = name
        # self.levelno = level
        # self.levelname = _level_dict[level]
        # self.message = message
        # self.ct = time.time()
        # self.msecs = int((self.ct - int(self.ct)) * 1000)
        # self.asctime = None

    def emit(self, record):
        self.logCount += 1
        if record.levelno >= self.level:
            if len(self.tail) >= self.tailLen:
                self.tail.pop(0)
            self.tail.append(self.format(record))


    async def getLogEntries(self):
        for s in self.tail:
            yield s


    def get(self, data, logger):
        logger.info(f"Tail logger contains last {len(self.tail)} of {self.logCount} logged items.")
        for idx, line in enumerate(reversed(self.tail)):
            yield f"{self.logCount-idx}> {line}\n"
