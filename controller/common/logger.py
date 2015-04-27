import logging
import sys
from config import Config

class ConsoleLogger(object):
    def __init__(self, name=''):
        config = Config()
        self.log_level = getattr(logging, config.log_level.upper())
        if not name:
            self.logger = logging.getLogger()
        else:
            self.logger = logging.getLogger(name)

        self.logger.setLevel(level = self.log_level)
		
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(level = config.log_level)
		
        formatter = logging.Formatter("%(asctime)s:%(name)s:%(levelname)s:%(message)s")
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

    def getLogger(self):
        return self.logger
