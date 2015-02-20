__author__ = 'oliver'

from os.path import dirname, realpath
import sys

sys.path.append(dirname(realpath(__file__)) + '../../' )

import redis

class GlobalConfig(object):

    def __init__(self, config):
        self.config = config
        self.redis_conn = redis.StrictRedis(self.config.redis_host)

    def get_hosts(self):
        hosts = list(self.redis_conn.smembers("hosts"))
        return hosts

    def add_host(self, host):
	self.redis_conn.sadd("hosts", host)
	return self.get_hosts()

    def remove_host(self, host):
	self.redis_conn.srem("hosts", host)
	return self.get_hosts()
