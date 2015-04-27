__author__ = 'oliver'

from os.path import dirname, realpath
import sys

sys.path.append(dirname(realpath(__file__)) + '../../' )

from datetime import datetime
import re
import docker
import requests

from common.paasevents import write_event, get_events
import common.exceptions as exceptions
from common.datastore import Redis
import logging

class Applications(object):

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.redis_conn = Redis().getConnection()

    def get_all(self):
        applications = list(self.redis_conn.smembers("apps"))
        self.logger.debug("Getting application record")
        return { "data": applications }

    def get(self, name, containers=True):
        app_details = self.redis_conn.hgetall("app#{}".format(name))
        if not app_details:
            raise Exception("Application not found")

        app_details['environment'] = self.redis_conn.hgetall("global:environment")
        app_details["environment"].update(self.redis_conn.hgetall("{}:environment".format(name)))

        if "memory_in_mb" in app_details:
            app_details["memory_in_mb"] = str(app_details["memory_in_mb"])
        if not app_details:
            raise Exception

        #Fetch all containers that match this application
        if containers == True:
            containers = []
            for host in self.redis_conn.smembers("hosts"):
                try:
                    c = docker.Client(base_url="http://{}:4243".format(host), version="1.12")
                    find_containers = c.containers()
                    for container in find_containers:
                            if name in str(container['Names']) and any(match in str(container['Names']) for match in [ '_web_', '_weburlcheck_' ]):
                                port = container['Names'][0].split('_')[-1]
                                containers.append("{}:{}".format(host, port))
                except:
                    self.logger.info("Unable to communicate with docker node while requesting application containers")

            app_details['containers'] = containers

        if not "urls" in app_details:
            try:
                main_url = app_details['name'] + app_details['global_environment']['domain_name']
            except:
                print "Something is happening"
                print app_details
                main_url = app_details['name']
            urls = main_url

            app_details['urls'] = main_url

        return app_details

    def create_application(self, data):

        name = data['name']

        grabbed_name = self.redis_conn.hsetnx("app#{}".format(name), "created_at", datetime.now().isoformat())
        if not grabbed_name:
            raise exceptions.ApplicationExists("Application already exists")

        pipe = self.redis_conn.pipeline()
        pipe.hmset("app#{}".format(name),
            {
                "name": name, "type": "web", "docker_image": "", "state": "NEW", "memory_in_mb": "128", "command": "", "urls": name, "error_count": 0, "container_count": "2" })
        pipe.rpush("monitor", name)
        pipe.sadd("apps", name)
        output = pipe.execute()
        self.logger.debug("Application created, datastore output: {}".format(output))
        write_event("CREATE APP", "Create app - {}".format(name), name)
        return self.get(name)

    def update_application(self, name, data):

        if not self.redis_conn.exists("app#{}".format(name)):
            raise Exception("Application not found")
        if self.redis_conn.hget("app#{}".format(name), "state") == "deleting":
            raise Exception("Application scheduled for deletion")
        pipe = self.redis_conn.pipeline()

        current_record = self.redis_conn.hgetall("app#{}".format(name))
        current_environment = self.redis_conn.hgetall("{}:environment".format(name))

        if "restart" in data:
            environments = self.redis_conn.hgetall("{}:environment".format(name))
            try:
                new_counter = int(environments['RESTART']) + 1
            except KeyError:
                new_counter = 1

            if not "environment" in data:
                data['environment'] = {}
                data['environment']['RESTART'] = new_counter

            write_event("UPDATED APP", "App {}, restart called".format(name), name)

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
            #Check slug_url, if not valid return badly
            if "SLUG_URL" in data["environment"].keys():
                try:
                    response = requests.get(data["environment"]["SLUG_URL"], timeout=2, stream=True)
                    if response.status_code != 200:
                        raise Exception
                except Exception as e:
                    write_event("UPDATE APP", "Failed updating app, slug url {} invalid or inaccessible".format(data['environment']['SLUG_URL']), name)
                    raise Exception("Slug URL {} is either invalid or inaccessible".format(data["environment"]["SLUG_URL"]))

            if "PORT" in data["environment"].keys():
                raise Exception
            to_set = {k:v for k,v in data["environment"].items() if v}
            if to_set:
                pipe.hmset("{}:environment".format(name), to_set)
            to_remove = [k for k,v in data["environment"].items() if not v ]
            if to_remove:
                pipe.hdel("{}:environment".format(name), *to_remove)
        pipe.hdel("app#{}".format(name), "error_count")
        pipe.hset("app#{}".format(name), "state", "OUT OF DATE, AWAITING DEPLOY")
        pipe.execute()
        new_record = self.redis_conn.hgetall("app#{}".format(name))
        new_environment = self.redis_conn.hgetall("{}:environment".format(name))

        env_diff = set(set(current_environment.items()) ^ set(new_environment.items()))
        diff = set(set(current_record.items()) ^ set(new_record.items()))

        write_event("UPDATED APP", "App {} was updated".format(name), name)

        self.publish_updates(name)

        return self.get(name)

    def delete_application(self, name):
        if not self.redis_conn.exists("app#{}".format(name)):
            raise Exception("Application not found")

        port = self.redis_conn.hget("app#{}".format(name), "port")

        pipe = self.redis_conn.pipeline()

        pipe.delete("app#{}".format(name))
        pipe.delete("{}:environment".format(name))
        pipe.lrem("monitor", 0, name)
        pipe.srem("apps", name)
        pipe.execute()

        write_event("DELETE APP", "Deleted app - {}".format(name), name)
        return { "message": "Application {} deleted".format(name), "app_port": port}

    def publish_updates(self, app):
        self.redis_conn.publish('app_changes', app)
        return True

    def set_application_state(self, name, message):
        self.redis_conn.hset("app#{}".format(name), "state", message)

    def get_application_state(self, name):
        return self.redis_conn.hget("app#{}".format(name), "state")

    def write_container_logs(self, name, log_array):
        for entry in log_array:
            self.redis_conn.lpush("logs:{}".format(name), entry)
            self.redis_conn.ltrim("logs:{}".format(name), 0, 150)

    def get_container_logs(self, name):
        return self.redis_conn.lrange("logs:{}".format(name), 0, -1)

    def set_application_logs(self, name, node, container_logs):
        self.redis_conn.hset("app#{}:logs".format(name), node, container_logs)

    def get_application_logs(self, name):
        raw_logs = self.redis_conn.hgetall("app#{}:logs".format(name))
        return raw_logs

    def set_application_error_count(self, name):
        error_count = self.get_application_error_count(name)
        try:
            count = error_count + 1
        except:
            count = 1

        self.redis_conn.hset("app#{}".format(name), "error_count", count)
        return count

    def get_application_error_count(self, name):
        error_count = self.redis_conn.hget("app#{}".format(name), "error_count")

        return error_count

    def set_application_lock(self,name):
        return self.redis_conn.execute_command("SET", "app#{}:locked".format(name), "locked", "NX", "EX", "60")

    def remove_application_lock(self, name):
        return self.redis_conn.delete("app#{}:locked".format(name))

    def get_all_urls(self):
        ab = re.compile("^.*:.*$")
        application_details = {}
        application_details['containers'] = {}
        application_details['endpoints'] = {}

        apps = self.redis_conn.smembers("apps")
        for app in apps:
            try:
                app_details = self.get(app)
                for url in app_details['urls'].split('\n'):
                    if ab.match(url):
                        (domain, location) = url.split(":")
                        if not domain in application_details['endpoints']:
                            application_details['endpoints'][domain] = {}
                        application_details['endpoints'][domain][location] = app_details['name']
                    else:
                        if not "url" in application_details['endpoints']:
                            application_details['endpoints'][url] = {}
                        application_details['endpoints'][url]['/'] = app_details['name']

                application_details['containers'][app] = app_details['containers']
            except Exception as e:
                print "Error fetching application details for urls: {}".format(e.message)

        return application_details

    def allocate_port(self):
        if not self.redis_conn.exists("ports"):
            self.redis_conn.sadd("ports", *range(30000,60000))
        port = self.redis_conn.spop("ports")
        return port

    def return_port(self, port):
        try:
            self.redis_conn.sadd("ports", port)
            return True
        except:
            return False
