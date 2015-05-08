import logging
import sys
import redis
import time
from config import Config
import config

class Datastore(object):
    def __init__(self, db=0):
        self.config = Config()
        self.redis_conn = redis.StrictRedis(host=self.config.redis_host, port=self.config.redis_port, db=db)
        self.logger = logging.getLogger(__name__)

    def getConnection(self):
        self.logger.info("Getting redis database connection")
        return self.redis_conn

    def getApplications(self):
        apps = list()
        for key in self.redis_conn.keys("app#*"):
            name = key.split("#")[1]
            apps.append(name)
        return apps

    def getApplication(self, name):
        app_details = self.redis_conn.hgetall("app#{}".format(name))
        return app_details

    def getApplicationEnvironment(self, name):
        return self.redis_conn.hgetall("{}:environment".format(name))

    def createApplication(self, name, data):
        try:
            self.redis_conn.hmset("app#{}".format(name), data)
            return True
        except:
            return False

    def updateApplication(self, name, data):

        pipe = self.redis_conn.pipeline()

        if "memory_in_mb" in data:
            pipe.hset("app#{}".format(name), "memory_in_mb", data["memory_in_mb"])

        if "docker_image" in data:
            pipe.hset("app#{}".format(name), "docker_image", data["docker_image"])

        if "command" in data:
            pipe.hset("app#{}".format(name), "command", data["command"])

        if "urls" in data:
            pipe.hset("app#{}".format(name), "urls", data["urls"])

        if "type" in data:
            pipe.hset("app#{}".format(name), "type", data['type'])

        pipe.hdel("app#{}".format(name), "app_type")
        if "container_count" in data:
            pipe.hset("app#{}".format(name), "container_count", data['container_count'])

        if "environment" in data:
            self.updateApplicationEnvironment(name, data['environment'])
        if "state" in data:
            pipe.hset("app#{}".format(name), "state", data['state'])
        else:
            pipe.hset("app#{}".format(name), "state", "OUT OF DATE, AWAITING DEPLOY")


        pipe.execute()

    def updateApplicationEnvironment(self, name, data):

        pipe = self.redis_conn.pipeline()
        to_set = {k:v for k,v in data.items() if v}
        if to_set:
            pipe.hmset("{}:environment".format(name), to_set)
        to_remove = [k for k,v in data.items() if not v ]
        if to_remove:
            pipe.hdel("{}:environment".format(name), *to_remove)
        pipe.execute()
        return True


    def deleteApplication(self, name):
        try:
            self.redis_conn.delete("app#{}".format(name))
            self.deleteApplicationEnvironment(name)
            return True
        except:
            raise Exception("Application not found")

    def deleteApplicationEnvironment(self, name):
        self.redis_conn.delete("{}:environment".format(name))
        return True

    def getContainerHosts(self):
        return list(self.redis_conn.smembers("hosts"))

    def addContainerHost(self, host):
        self.redis_conn.sadd("hosts", host)

    def deleteContainerHost(self, host):
        self.redis_conn.srem("hosts", host)

    def allocatePort(self):
        if not self.redis_conn.exists("ports"):
            self.redis_conn.sadd("ports", *range(30000,60000))
        port = self.redis_conn.spop("ports")
        return port

    def releasePort(self, port):
        try:
            self.redis_conn.sadd("ports", port)
            return True
        except:
            return False

    def createApplicationLock(self, name):
        return self.redis_conn.execute_command("SET", "lock:{}".format(name), "locked", "NX", "EX", "60")

    def deleteApplicationLock(self, name):
        return self.redis_conn.delete("lock:{}".format(name))

    def writeEvent(self, name, message):
        epoch_timestamp = time.time()
        count = self.redis_conn.zcount("logs:{}".format(name), 0, 1000000000000000000000)
        pipe = self.redis_conn.pipeline()
        pipe.zadd("logs:{}".format(name), epoch_timestamp, message)
        if count >= 100:
            difference = count - 100
            pipe.zremrangebyrank("app#{}".format(name), 0, difference)
        pipe.expire("logs:{}".format(name), 7776000)
        pipe.execute()

    def getEvent(self, name):

        events_data = list()
        if ( name != "all"):
            try:
                events_data = list(self.redis_conn.zrange("app#{}".format(name), 0, 100, withscores=True))
            except:
                logging.error("Unable to get list")
        else:
            pipe = self.redis_conn.pipeline()
            keys = list(self.redis_conn.keys("app#*"))
            if ( len(keys) > 0 ):
                pipe.zunionstore('combined', keys)
                pipe.zrange('combined', 0, -1, withscores=True)
                events_data = list(pipe.execute()[1])
            else:
                logging.error("No apps logs available")

        return events_data



