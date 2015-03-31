__author__ = 'oliver'

from os.path import dirname, realpath
import sys

sys.path.append(dirname(realpath(__file__)) + '../../' )

from common.datastore import Redis

class GlobalConfig(object):

    def __init__(self):
        self.redis_conn = Redis().getConnection() 

    def get_hosts(self):
        hosts = list(self.redis_conn.smembers("hosts"))
        return hosts

    def add_host(self, host):
	self.redis_conn.sadd("hosts", host)
	return self.get_hosts()

    def remove_host(self, host):
	self.redis_conn.srem("hosts", host)
	return self.get_hosts()
