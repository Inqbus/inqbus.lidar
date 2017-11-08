import io
import os
import sys
from logging import getLogger, Formatter, DEBUG, INFO, StreamHandler
from logging.handlers import TimedRotatingFileHandler
from sys import stdout

from inqbus.lidar.scc_gui.configs import main_config as mc

if not os.path.exists(mc.SYS_LOG_PATH):
    print("Log file directory does not exists %s, please create it " % mc.SYS_LOG_PATH)
    sys.exit(1)



logger = getLogger('inqbus.lidar')
formatter = Formatter('%(asctime)s %(levelname)-8s %(message)s',
                          "%Y-%m-%d %H:%M:%S")

__all__ = ["logger"]


class TqdmToLogger(io.StringIO):
    """
        Output stream for TQDM which will output to logger module instead of
        the StdOut.
    """
    logger = None
    level = None
    buf = ''
    def __init__(self,logger,level=None):
        super(TqdmToLogger, self).__init__()
        self.logger = logger
        self.level = level or INFO
    def write(self,buf):
        self.buf = buf.strip('\r\n\t ')
    def flush(self):
        self.logger.log(self.level, self.buf)


timedRotatingFileHandler = TimedRotatingFileHandler(mc.SYS_LOG_FILE, "D", 1, 15)
timedRotatingFileHandlerFormatter = formatter
timedRotatingFileHandler.setFormatter(timedRotatingFileHandlerFormatter)
timedRotatingFileHandler.setLevel(mc.SYS_LOG_LEVEL)

consoleHandler = StreamHandler(stdout)

consoleFormatter = formatter
consoleHandler.setFormatter(consoleFormatter)
consoleHandler.setLevel(mc.SYS_LOG_LEVEL)

logger.addHandler(timedRotatingFileHandler)
logger.addHandler(consoleHandler)

logger.propagate = False
logger.setLevel(DEBUG)
