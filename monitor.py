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
import Queue
import threading

logger = logging.getLogger("monitor_logger")
logger.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")

ch.setFormatter(formatter)

logger.addHandler(ch)

from common.config import Config

config = Config()
number_of_threads = 5
q = Queue.Queue()

redis_conn = redis.StrictRedis(config.redis_host, db=0)

import random

def check_app():
    print "Starting app check thread"
    while True:
        app_id = q.get()
        logger.debug("Check app: {}.{}".format(app_id,random.random()))
        locked = redis_conn.execute_command("SET", "app#{}:locked".format(app_id), "locked", "NX", "EX", "60")
        if not locked:
            q.task_done()
            continue

        logger.debug("checking {}".format(app_id))

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
            #logger.info("{} - image not set, skipping".format(app_id))
            redis_conn.delete("app#{}:locked".format(app_id))
            #redis_conn.expire("app#{}:locked".format(app_id), 1)
            q.task_done()
            continue


        for node in redis_conn.smembers("hosts"):
            c = docker.Client(base_url='http://{}:4243'.format(node), version="1.12")
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
                    docker_id = None
                    status = redis_conn.delete("docker_id#{}".format(docker_id), "{}:{}".format(node, app_id))
                    redis_conn.delete("app#{}:locked".format(app_id))
                else:
                    current_image = container_details["Config"]["Image"]
                    current_environment = { entry.split("=")[0]: entry.split("=")[1] for entry in container_details["Config"]["Env"] }
                    current_memory = container_details["Config"]["Memory"]
                    current_command = container_details["Config"]["Cmd"]
                    if "HOME" in current_environment:
                        del(current_environment["HOME"])
                    del(current_environment["PATH"])
                    del(current_environment["PORT"])
                    if current_environment != environment or current_image != docker_image or current_memory != memory or current_command != command:

                        #First fetch new image if its an image changed
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
                                redis_conn.delete("app#{}:locked".format(app_id))
                                q.task_done()
                                continue

                        c.stop(docker_id)
                        c.remove_container(docker_id)
                        write_event("CONTAINER_MONITOR", "Docker container {} destroyed on node {} for app_id {}".format(docker_id, node, app_id))
                        docker_id = redis_conn.hdel("{}:{}".format(node, app_id), "docker_id")
                        status = redis_conn.delete("docker_id#{}".format(docker_id), "{}:{}".format(node, app_id))
                        redis_conn.delete("app#{}:locked".format(app_id))

            if not docker_id:
                redis_conn.hset("app#{}".format(app_id), "state", "DEPLOYING to {}".format(node))
                logger.info("{} - starting runner on {}".format(app_id, node))
                repository, _, tag = docker_image.rpartition(":")
                if repository == "":
                   repository = docker_image
                c.pull(repository, tag)
                r = c.create_container(docker_image, command, ports={"{}/tcp".format(port): {}}, environment=dict( environment.items() + {"PORT": port}.items() ), mem_limit=memory)
                docker_id = r["Id"]
                try:
                    c.start(docker_id, port_bindings={"{}/tcp".format(port): port})
                except:
                    print "Error talking to docker"


                write_event("CONTAINER_MONITOR", "Starting docker container {} on node {} for app_id {}".format(docker_id, node, app_id))

                redis_conn.hset("{}:{}".format(node, app_id), "docker_id", docker_id)
                redis_conn.set("docker_id#{}".format(docker_id), app_id)
                redis_conn.delete("app#{}:locked".format(app_id))
                #redis_conn.expire("app#{}:locked".format(app_id), 2)

        redis_conn.hset("app#{}".format(app_id), "state", "RUNNING")

        # allow next check in 10s
        redis_conn.delete("app#{}:locked".format(app_id))
        #redis_conn.expire("app#{}:locked".format(app_id), 1)
        q.task_done()


def check_nodes():
    print "Starting node check thread"
    while True:
        for node in redis_conn.smembers("hosts"):
            c = docker.Client(base_url='http://{}:4243'.format(node), version="1.12")
            for container in c.containers(all=True):
                docker_id = container["Id"]
                container_details = c.inspect_container(docker_id)
                app_id = redis_conn.get("docker_id#{}".format(docker_id))
                if (docker_id != redis_conn.hget("{}:{}".format(node, app_id), "docker_id") or not redis_conn.exists("app#{}".format(app_id))):
                    print "stopping orphaned container {}".format(docker_id)
                    write_event("CONTAINER_MONITOR", "Destroying orphaned docker container {} on node {}".format(docker_id, node))
                    c.stop(docker_id)
                    c.remove_container(docker_id)
                    redis_conn.delete("docker_id#{}".format(docker_id))
                    redis_conn.delete("{}:{}".format(node, app_id))
        time.sleep(10)


def monitor_loop():
    while True:
        app_id = redis_conn.rpoplpush("monitor", "monitor")
        if app_id:
            try:
                #check_app(app_id)
                q.put(app_id)
            except Exception as e:
                redis_conn.hset("app#{}".format(app_id), "state", "FAILED - {}".format(e))
                logging.error("{} - {}".format(app_id, e))

        time.sleep(0.10)


if __name__ == '__main__':

    q.join()

    for i in range(number_of_threads):
        t = threading.Thread(target=check_app)
        t.daemon = True
        t.start()


#    node_thread = threading.Thread(target=check_nodes)
#    node_thread.daemon = True
#    node_thread.start()

    monitor_loop()





