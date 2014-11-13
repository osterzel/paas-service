#!/usr/bin/env python

import docker

from os.path import dirname, realpath
import sys

sys.path.append(dirname(realpath(__file__)) + '../' )

from common.paasevents import write_event, get_events

#stupid docker-py, monkeypatch
def pull_fix(self, repository, tag=None, registry=None):
    params = {
        'tag': tag,
        'fromImage': repository,
        'registry': registry
    }
    u = self._url("/images/create")
    return self._result(self.post(u, None, params=params))

from requests import HTTPError

docker.Client.pull = pull_fix

import redis
import time
import threading

import logging
logging.basicConfig(level=logging.DEBUG)

requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.WARNING)
requests_log.propogate = True

from common.config import Config

config = Config()

redis_conn = redis.StrictRedis(config.redis_host, db=0)

def check_app(app_id):
    locked = redis_conn.execute_command("SET", "app#{}:locked".format(app_id), "locked", "NX", "EX", "120")
    if not locked:
        return
    logging.debug("checking {}".format(app_id))

    app_details = redis_conn.hgetall("app#{}".format(app_id))

    name = app_details["name"]
    port = app_details["port"]
    docker_image = app_details["docker_image"]
    state = app_details["state"]
    environment = {}
    environment.update(redis_conn.hgetall("{}:environment".format(app_id)))

    memory = int(app_details["memory_in_mb"]) * 1024**2
    try:
        command = app_details["command"].split()
    except:
        command = None

    if not docker_image:
        logging.info("{} - image not set, skipping".format(app_id))
        redis_conn.expire("app#{}:locked".format(app_id), 10)
        return

    for node in redis_conn.smembers("hosts"):

        c = docker.Client(base_url='http://{}:4243'.format(node), version="1.4")
        docker_id = redis_conn.hget("{}:{}".format(node, app_id), "docker_id")
        if docker_id:
            try:
                container_details = c.inspect_container(docker_id)
                container_logs = c.logs(docker_id)
                # redis.setex("docker_id#{}:logs".format(docker_id), container_logs)
                redis_conn.hset("app#{}:logs".format(app_id), node, container_logs)
            except HTTPError:
                container_details = { "State": { "Running": False } }
            if not container_details["State"]["Running"]:
                c.remove_container(docker_id)
                docker_id = None
                redis_conn.delete("docker_id#{}".format(docker_id), "{}:{}".format(node, app_id))
            else:
                current_image = container_details["Config"]["Image"]
                current_environment = { entry.split("=")[0]: entry.split("=")[1] for entry in container_details["Config"]["Env"] }
                current_memory = container_details["Config"]["Memory"]
                current_command = container_details["Config"]["Cmd"]
                del(current_environment["HOME"])
                del(current_environment["PATH"])
                del(current_environment["PORT"])
                if current_environment != environment or current_image != docker_image or current_memory != memory or current_command != command:

                    #First fetch new image if its an image change
                    if current_image != docker_image:
                        try:
                            redis_conn.hset("app#{}".format(app_id), "state", "Fetching image {} on host {}".format(docker_image, node))
                            repository, _, tag = docker_image.rpartition(":")
                            if repository == "":
                                repository = docker_image
                            c.pull(repository, tag)
                        except Exception as e:
                            write_event("Problem fetching docker image: {}".format(e))
                            redis_conn.hset("app#{}".format(app_id), "state", "Unable to fetch image {} on {}".format(docker_image, node))
                            return

                    c.stop(docker_id)
                    c.remove_container(docker_id)
                    write_event("CONTAINER_MONITOR", "Docker container {} destroyed on node {} for app_id {}".format(docker_id, node, app_id))
                    docker_id = redis_conn.hdel("{}:{}".format(node, app_id), "docker_id")
                    redis_conn.delete("docker_id#{}".format(docker_id), "{}:{}".format(node, app_id))
                    redis_conn.delete("app#{}:locked".format(app_id))
                    return

        if not docker_id:
            redis_conn.hset("app#{}".format(app_id), "state", "DEPLOYING to {}".format(node))
            logging.info("{} - starting runner on {}".format(app_id, node))
            repository, _, tag = docker_image.rpartition(":")
            if repository == "":
               repository = docker_image
            c.pull(repository, tag)
            r = c.create_container(docker_image, command, ports={"{}/tcp".format(port): {}}, environment=dict( environment.items() + {"PORT": port}.items() ), mem_limit=memory)
            docker_id = r["Id"]
            c.start(docker_id, port_bindings={"{}/tcp".format(port): port})

            write_event("CONTAINER_MONITOR", "Starting docker container {} on node {} for app_id {}".format(docker_id, node, app_id))

            redis_conn.hset("{}:{}".format(node, app_id), "docker_id", docker_id)
            redis_conn.set("docker_id#{}".format(docker_id), app_id)
            redis_conn.expire("app#{}:locked".format(app_id), 10)
            return

    redis_conn.hset("app#{}".format(app_id), "state", "RUNNING")

    # allow next check in 10s
    redis_conn.expire("app#{}:locked".format(app_id), 5)

def check_nodes():
    for node in redis_conn.smembers("hosts"):
        print node
        c = docker.Client(base_url='http://{}:4243'.format(node), version="1.4")
        for container in c.containers(all=True):
            docker_id = container["Id"][:12]
            container_details = c.inspect_container(docker_id)
            app_id = redis_conn.get("docker_id#{}".format(docker_id))
            if not container_details["State"]["Running"] or (docker_id != redis_conn.hget("{}:{}".format(node, app_id), "docker_id") or not redis_conn.exists("app#{}".format(app_id))):
                print "stopping orphaned container {}".format(docker_id)
                write_event("CONTAINER_MONITOR", "Destroying orphaned docker container {} on node {}".format(docker_id, node))
                c.stop(docker_id)
                c.remove_container(docker_id)
                redis_conn.delete("docker_id#{}".format(docker_id))
                redis_conn.delete("{}:{}".format(node, app_id))


def monitor_loop():
    while True:
        app_id = redis_conn.rpoplpush("monitor", "monitor")
        if app_id:
            try:
                check_app(app_id)
            except Exception as e:
                redis_conn.hset("app#{}".format(app_id), "state", "FAILED - {}".format(e))
                logging.error("{} - {}".format(app_id, e))
        try:
            check_nodes()
        except Exception as e:
            logging.error("{}".format(e))
        time.sleep(0.05)

if __name__ == '__main__':

    monitor_loop()




