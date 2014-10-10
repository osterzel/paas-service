__author__ = 'oliver'

from os.path import dirname, realpath
import sys

sys.path.append(dirname(realpath(__file__)) + '../../' )

from datetime import datetime
import redis

from common.paasevents import write_event, get_events

class Applications(object):

    def __init__(self, config):
        self.config = config
        self.redis_conn = redis.StrictRedis(self.config.redis_host)

    def get_all(self):
        applications = list(self.redis_conn.smembers("apps"))
        return { "data": applications }

    def get(self, name):
        app_details = self.redis_conn.hgetall("app#{}".format(name))
        if not app_details:
            raise Exception

        app_details["environment"] = self.redis_conn.hgetall("{}:environment".format(name))
        if ( self.redis_conn.hgetall("global:environment")):
            app_details["global_environment"] = self.redis_conn.hgetall("global:environment")

        if "memory_in_mb" in app_details:
            app_details["memory_in_mb"] = int(app_details["memory_in_mb"])
        if not app_details:
            raise Exception

        if not "urls" in app_details:
            print "No urls found"
            try:
                main_url = app_details['name'] + app_details['global_environment']['domain_name']
            except:
                main_url = app_details['name']
            urls = main_url

            app_details['urls'] = main_url

        app_details['hosts'] = list(self.redis_conn.smembers("hosts"))

        return app_details

    def create_application(self, data):

        if not self.redis_conn.exists("ports"):
            paas_init_lock = self.redis_conn.execute_command("SET", "initlock", "locked", "NX", "EX", "60")
            if not paas_init_lock:
                raise Exception
            self.redis_conn.sadd("ports", *range(49152, 65535))

        name = data['name']

        grabbed_name = self.redis_conn.hsetnx("app#{}".format(name), "created_at", datetime.now().isoformat())
        if not grabbed_name:
            raise Exception
        port = self.redis_conn.spop("ports")
        if not port:
            self.redis_conn.delete("app#{}".format(name))
            raise Exception

        pipe = self.redis_conn.pipeline()
        pipe.hmset("app#{}".format(name),
            {
                "name": name, "port": port, "ssl": "false", "ssl_certificate_name": "", "docker_image": "", "state": "virgin", "memory_in_mb": 512, "command": "", "urls": name })
        pipe.rpush("monitor", name)
        pipe.sadd("apps", name)
        pipe.execute()
        write_event("CREATE APP", "Create app - {}".format(name), name)
        return self.get(name)

    def update_application(self, name, data):

        if not self.redis_conn.exists("app#{}".format(name)):
            raise Exception
        if self.redis_conn.hget("app#{}".format(name), "state") == "deleting":
            raise Exception
        pipe = self.redis_conn.pipeline()

        if "restart" in data:
            environments = self.redis_conn.hgetall("{}:environment".format(name))
            try:
                new_counter = int(environments['RESTART']) + 1
            except KeyError:
                new_counter = 1

        if not "environment" in data:
            data['environment'] = {}
            data['environment']['RESTART'] = int(1)

        write_event("UPDATED APP", "App {}, restart called".format(name), name)

        if "ssl" in data:
            pipe.hset("app#{}".format(name), "ssl", data["ssl"])

        if "ssl_certificate_name" in data:
            pipe.hset("app#{}".format(name), "ssl_certificate_name", data["ssl_certificate_name"])

        if "memory_in_mb" in data:
            pipe.hset("app#{}".format(name), "memory_in_mb", data["memory_in_mb"])
        else:
            pipe.hsetnx("app#{}".format(name), "memory_in_mb", 0)

        if "docker_image" in data:
            pipe.hset("app#{}".format(name), "docker_image", data["docker_image"])

        if "command" in data:
            pipe.hset("app#{}".format(name), "command", data["command"])

        if "urls" in data:
            pipe.hset("app#{}".format(name), "urls", data["urls"])

        if "environment" in data:
            if "PORT" in data["environment"].keys():
                raise Exception
            to_set = {k:v for k,v in data["environment"].items() if v}
            if to_set:
                pipe.hmset("{}:environment".format(name), to_set)
            to_remove = [k for k,v in data["environment"].items() if not v ]
            if to_remove:
                pipe.hdel("{}:environment".format(name), *to_remove)
        pipe.hset("app#{}".format(name), "state", "OUT OF DATE, AWAITING DEPLOY")
        pipe.execute()
        write_event("UPDATED APP", "App {} was updated".format(name), name)

        return self.get(name)


    def delete_application(self, name):
        if not self.redis_conn.exists("app#{}".format(name)):
            raise Exception

        port = self.redis_conn.hget("app#{}".format(name), "port")

        pipe = self.redis_conn.pipeline()

        pipe.delete("app#{}".format(name))
        pipe.delete("{}:environment".format(name))
        pipe.lrem("monitor", 0, name)
        pipe.srem("apps", name)
        pipe.sadd("ports", port)
        pipe.execute()

        write_event("DELETE APP", "Deleted app - {}".format(name), name)
        return { "message": "Application deleted", "app_port": port}
