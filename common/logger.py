import logging
import sys

class ConsoleLogger(object):
	def __init__(self, log_level):
		self.log_level = getattr(logging, log_level.upper()) 
		self.logger = logging.getLogger("core_logger")
		self.logger.setLevel(level = self.log_level)
		
		ch = logging.StreamHandler(sys.stdout)
		ch.setLevel(level = self.log_level)
		
		formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
		ch.setFormatter(formatter)
		self.logger.addHandler(ch)

	def getLogger(self):
		return self.logger
