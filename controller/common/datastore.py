import logging
import sys
import redis
from config import Config
import config

class Redis(object):
	def __init__(self, db=0):
		self.config = Config()
		self.redis_conn = redis.StrictRedis(host=self.config.redis_host, port=self.config.redis_port, db=db)

	def getConnection(self):
		return self.redis_conn
