__author__ = 'oliver'

from os.path import dirname, realpath
import sys

sys.path.append(dirname(realpath(__file__)) + '../../' )

from datetime import datetime

import common.paasevents
import json

import redis

class GlobalConfig(object):

    def __init__(self, config):
        self.config = config
        self.redis_conn = redis.StrictRedis(self.config.redis_host)

    def get(self, type):

        hosts = list(self.redis_conn.smembers("hosts"))
        environment = self.redis_conn.hgetall("global:environment")

        if type == 'all':
            return { "hosts": hosts, "environment": environment }
        elif type == 'environment':
            return hosts
        elif type == 'hosts':
            return hosts
        else:
            raise Exception

    def update_environment(self, data):

        args = json.dumps(data)

        if "environment" in args:
            to_set = {k:v for k,v in args["environment"].items() if v}
            if to_set:
                self.redis_conn.hmset("global:environment", to_set)
            to_remove = [k for k,v in args["environment"].items() if not v ]
            if to_remove:
                self.redis_conn.hdel("global:environment", *to_remove)

        if "hosts" in args:
            self.redis_conn.delete("hosts")
            for host in args['hosts']:
                self.redis_conn.sadd("hosts", host)
