#!/usr/bin/env python

import docker

from os.path import dirname, realpath
import sys

sys.path.append(dirname(realpath(__file__)) + '../' )

from common.paasevents import write_event, get_events
from api.resources.applications import Applications
from api.resources.globalconfig import GlobalConfig

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
import re
import time
import threading

import logging
import Queue
import threading
from common.config import Config
import logging
import pprint

config = Config()

print config.log_level

log_level = getattr(logging, config.log_level.upper())
print log_level

logger = logging.getLogger("monitor_logger")
logger.setLevel(level = log_level)

ch = logging.StreamHandler()
ch.setLevel(level = log_level)

formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")

ch.setFormatter(formatter)

logger.addHandler(ch)

number_of_threads = 2
q = Queue.Queue()
change_queue = Queue.Queue()

application = Applications(config)
global_config = GlobalConfig(config)

redis_conn = redis.StrictRedis(config.redis_host, db=0)

cluster_state = {}

import random
import pika
import json
import os
import socket

class Notifications(object):
    def __init__(self):
        parameters = pika.URLParameters(os.environ.get("RABBITMQ_URI", "amqp://dev:dev@localhost:5672/paas"))
	print "RabbitMQ Url: {}".format(parameters)
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange='paas',
                         type='topic')

    def callback(self, ch, method, properties, body):
        try:
            data = json.loads(body)
        except:
            print "Message is not in json format"

    def send_message(self, routing, body):
        print "Sending message"
        self.channel.basic_publish(exchange='paas', routing_key=routing, body=body)

notification_handler = Notifications()

def test_web_container(node, port):
	logger.info("Testing web container on %s:%s responds" % (node, port))
	s = socket.socket()
	success = 0
	for count in range(60):
		try:
			s = socket.socket()
			socket.setdefaulttimeout(3)
			s.connect((node, int(port)))
			success = 1
			print "Successfully connected"
			s.close()
			break
		except socket.error, e:
			print e.message
			time.sleep(2)

	if success == 0:
		logger.info("Container did not respond after 60 seconds")
		return False
	else:
		logger.info("Container responded")
		return True

def get_cluster_state():
    cluster_state = {}
    cluster_state['containers'] = []
    cluster_state['nodes'] = {}
    for node in redis_conn.smembers("hosts"):
        cluster_state['nodes'][node] = {}
        try:
            c = docker.Client(base_url='http://{}:4243'.format(node), version="1.12")
            for container in c.containers(all=True):
                docker_id = container["Id"]
                cluster_state['containers'].append(docker_id)
                try:
                    container_details = c.inspect_container(docker_id)
                    cluster_state['nodes'][node][docker_id] = container_details
		except Exception as e:
                    logger.info("Error getting container details: {}".format(e.message))
        except:
            logger.error("Unable to connect to node {} to fetch cluster state".format(node))

    return cluster_state

def get_app_state():
    docker_keys = redis_conn.keys("docker_id#*")
    app_state = {}
    app_state['containers'] = []
    for docker_key in docker_keys:
        app_state['containers'].append(docker_key.split('#')[1])

    return app_state

def process_change():
    logger.info("Starting app change thread")
    while True:
        app = change_queue.get()
        locked = application.set_application_lock(app)
        if not locked:
	    change_queue.put(app)
            continue

        logger.info("Processing update on app {}".format(app))

        app_details = application.get(app)

        docker_image = app_details['docker_image']
        memory = int(app_details['memory_in_mb'] * 1024**2)
        environment = app_details['environment']

        try:
            command = app_details['command'].split()
        except:
            command = None

        logger.info("Ready to go through nodes and create new instances")

        for node in redis_conn.smembers("hosts"):
            c = docker.Client(base_url='http://{}:4243'.format(node), version="1.12")
            current_containers = redis_conn.keys("containers:{}:{}:*".format(node, app))

            #Get a free port for the node and allocate it to this container
            if not redis_conn.exists("ports:{}".format(node)):
                redis_conn.sadd("ports:{}".format(node), *range(49152, 65535))

            port = redis_conn.spop("ports:{}".format(node))

            try:
                r = c.create_container(docker_image, command, ports={"{}/tcp".format(port): {}}, environment=dict( environment.items() + {"PORT": port}.items() ), mem_limit=memory, name="{}_{}".format(app, port))
            except Exception as e:
                application.set_application_state(app, "Exception: {}".format(e.message))

                logger.error("Error creating docker image")
                continue

            application.set_application_state(app, "DEPLOYING to {}".format(node))
            docker_id = r['Id']
            c.start(docker_id, port_bindings={"{}/tcp".format(port): port})
            redis_conn.publish("containers", "New container created")
            redis_conn.set("docker_id#{}".format(docker_id), app)
            redis_conn.execute_command("SET", "docker_id:locked#{}".format(docker_id), "locked", "NX", "EX", 20)
            logger.info("Started new container {}".format(docker_id))

            #Now wait until the inspect returns and says its running then we say its successful
            time.sleep(12)
            output = c.inspect_container(docker_id)

            successful = 0
            if output['State']['Running'] == False:
                logs = c.logs(docker_id)
                application.set_application_logs(app, node, logs)
                redis_conn.hset("app#{}".format(app), "state", "Error updating application, {}".format(logs))
                logger.info("Problem starting up new container\n Log info: {}".format(logs))
            else:
                #First wait until the port responds on the container before continuing and putting into service


                if not "app_type" in app_details:
                    if not test_web_container(node, port):
                        print "Container did not start successfully"
                        application.set_application_state(app, "Failed deploying new container to %s" % (node))
                        continue
                else:
                    if not "app" in app_details['app_type']:
                        if not test_web_container(node, port):
                            print "Container did not start successfully"
                            application.set_application_state(app, "Failed deploying new container to %s" % (node))
                            continue

                redis_conn.hset("containers:{}:{}:{}".format(node, app, port), "docker_id", docker_id)
                redis_conn.hset("containers:{}:{}:{}".format(node, app, port), "port", port)

                try:
                    notification_handler.send_message('docker_container_updates', json.dumps(application.get_all_urls()))
                except Exception as e:
                    logger.info("Unable to send docker_container_update to exchange")


                logs = c.logs(docker_id)
                application.set_application_logs(app, node, logs)
                for key in current_containers:

                    data = redis_conn.hgetall(key)
                    delete_docker_id = data['docker_id']
                    if "port" in data:
                        delete_port = data['port']
                        redis_conn.sadd("ports:{}".format(node), delete_port)

                    try:
                        c.kill(delete_docker_id)
                        c.remove_container(delete_docker_id)
                    except Exception as e:
                        application.set_application_state(app, "Exception: {}".format(e.message))

                    redis_conn.delete(key)
                    redis_conn.delete("docker_id#{}".format(delete_docker_id))
                    logger.info("Deleted old container {}".format(delete_docker_id))

                try:
                    notification_handler.send_message('docker_container_updates', json.dumps(application.get_all_urls()))
                except Exception as e:
                    logger.info("Unable to send docker_container_update to exchange")

        logger.info("Finished updating node {}".format(node))
        redis_conn.hset("app#{}".format(app), "state", "RUNNING")

        redis_conn.delete("docker_id:locked#{}".format(docker_id))

        change_queue.task_done()
        application.remove_application_lock(app)

def check_app():
    logger.info("Starting app check thread")
    while True:
        data = q.get()
        app_id = data['app']
        print app_id
        cluster_state = data['cluster']
        unique_app_id = "{}.{}".format(app_id, random.random())
        logger.debug("{}:Check app".format(unique_app_id))
        locked = application.set_application_lock(app_id)
        if not locked:
    	    logger.info("Unable to lock app")
    	    q.task_done()
            continue

        logger.debug("{}:App locked and check started".format(unique_app_id))

        app_details = application.get(app_id)

        if "error_count" in app_details:
            if int(app_details['error_count']) >= 3:
                logger.debug("{}:Fatal error count found, {}".format(unique_app_id, app_details['error_count']))
                redis_conn.delete("app#{}:locked".format(app_id))
                q.task_done()
                if (app_details['state'] != "ERROR starting application"):
                    redis_conn.hset("app#{}".format(app_id), "state", "ERROR starting application")
                continue

        logger.debug("{}:No fatal error count found".format(unique_app_id))

        name = app_details["name"]
        docker_image = app_details["docker_image"]
        state = app_details["state"]
        environment = app_details['environment']

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
            containers = redis_conn.keys("containers:{}:{}:*")
            print containers
            for key in containers:
                docker_id = redis_conn.hget("{}:{}".format(node, app_id), "docker_id")
                #logger.debug("{}:Checking if app should be on node {}".format(unique_app_id,node))

                if docker_id:
                    try:
                        #container_details = cluster_state[node][docker_id]
                        container_details = c.inspect_container(docker_id)
                        try:
                            container_logs = c.logs(docker_id)
                        except:
                            logger.error("Unable to fetch logs for {}".format(docker_id))

                        # redis.setex("docker_id#{}:logs".format(docker_id), container_logs)
                        try:
                            application.set_application_logs(app_id, node, container_logs)
                        except:
                            logger.error("Problem setting application logs")
                    except (HTTPError, KeyError):
                        logger.info("Error fetching container details")
                        container_details = { "State": { "Running": False } }

                    if not container_details["State"]["Running"]:
                        docker_id = None
                        status = redis_conn.delete("docker_id#{}".format(docker_id))
                        redis_conn.delete("app#{}:locked".format(app_id))
                        count = 0
                        count = application.set_application_error_count(app_id)
                        logger.info("Application Error Count: {}".format(count))
                        redis_conn.hset("app#{}".format(app_id), "error_count", count)

                if not docker_id:
                    #Get a free port for the node and allocate it to this container
                    if not redis_conn.exists("ports:{}".format(node)):
                        paas_init_lock = redis_conn.execute_command("SET", "initlock", "locked", "NX", "EX", "60")
                        if not paas_init_lock:
                            raise Exception
                        redis_conn.sadd("ports:{}".format(node), *range(49152, 65535))
                    port = redis_conn.spop("ports:{}".format(node))

                    redis_conn.hset("app#{}".format(app_id), "state", "DEPLOYING to {}".format(node))
                    logger.info("{} - starting runner on {}".format(app_id, node))
                    repository, _, tag = docker_image.rpartition(":")
                    if repository == "":
                       repository = docker_image
                    c.pull(repository, tag)

                    try:
                        r = c.create_container(docker_image, command, ports={"{}/tcp".format(port): {}}, environment=dict( environment.items() + {"PORT": port}.items() ), mem_limit=memory, name="{}_{}".format(app_id, port))
                    except Exception as e:
                        application.set_application_state(app_id, "Exception: {}".format(e.message))
                        logger.error("Error creating docker image")
                        continue

                    docker_id = r["Id"]
                    try:
                        redis_conn.set("docker_id#{}".format(docker_id), app_id)
                        redis_conn.execute_command("SET", "docker_id:locked#{}".format(docker_id), "locked", "NX", "EX", 60)
                        c.start(docker_id, port_bindings={"{}/tcp".format(port): port})
                        write_event("CONTAINER_MONITOR", "Starting docker container {} on node {} for app_id {}".format(docker_id, node, app_id))

                        #Now wait until the inspect returns and says its running then we say its successful
                        time.sleep(10)
                        output = c.inspect_container(docker_id)
                        if output['State']['Running'] == False:
                            logs = c.logs(docker_id)
                            redis_conn.hset("app#{}".format(app_id), "state", "Error updating application, {}".format(logs))
                            logger.info("Problem starting up new container\n Log info: {}".format(logs))
                        else:
                            #First wait until the port responds on the container before continuing and putting into service
                            if not "app_type" in app_details:
                                if not test_web_container(node, port):
                                    print "Container did not start successfully"
                                    application.set_application_state("Failed deploying new container to %s" % (node))
                                    continue
                            else:
                                if not "app" in app_details['app_type']:
                                    if not test_web_container(node, port):
                                        print "Container did not start successfully"
                                        application.set_application_state("Failed deploying new container to %s" % (node))
                                        continue
                                        
                            redis_conn.hset("containers:{}:{}:{}".format(node, app_id, port), "docker_id", docker_id)
                            redis_conn.hset("containers:{}:{}:{}".format(node, app_id, port), "port", port)
                            redis_conn.hset("app#{}".format(app_id), "state", "RUNNING")
                            data = application.get_all_urls()
                            try:
                                notification_handler.send_message('docker_container_updates', json.dumps(data))
                            except:
                                logger.info("Unable to send docker_container_update to exchange")

                    except:
                        logger.error("Error talking to docker node {}".format(node))
                        write_event("CONTAINER_MONITOR", "Failed talking to node {} to start {}".format(node, app_id))
                        redis_conn.hset("app#{}".format(app_id), "state", "Problem talking to node {}".format(node))

            if not containers:
                #Get a free port for the node and allocate it to this container
                if not redis_conn.exists("ports:{}".format(node)):
                    paas_init_lock = redis_conn.execute_command("SET", "initlock", "locked", "NX", "EX", "60")
                    if not paas_init_lock:
                        raise Exception
                    redis_conn.sadd("ports:{}".format(node), *range(49152, 65535))
                port = redis_conn.spop("ports:{}".format(node))

                redis_conn.hset("app#{}".format(app_id), "state", "DEPLOYING to {}".format(node))
                logger.info("{} - starting runner on {}".format(app_id, node))
                repository, _, tag = docker_image.rpartition(":")
                if repository == "":
                   repository = docker_image
                c.pull(repository, tag)

                try:
                    r = c.create_container(docker_image, command, ports={"{}/tcp".format(port): {}}, environment=dict( environment.items() + {"PORT": port}.items() ), mem_limit=memory, name="{}_{}".format(app_id, port))
                except Exception as e:
                    application.set_application_state(app_id, "Exception: {}".format(e.message))
                    logger.error("Error creating docker image")
                    continue

                docker_id = r["Id"]
                try:
                    redis_conn.set("docker_id#{}".format(docker_id), app_id)
                    redis_conn.execute_command("SET", "docker_id:locked#{}".format(docker_id), "locked", "NX", "EX", 60)
                    c.start(docker_id, port_bindings={"{}/tcp".format(port): port})
                    write_event("CONTAINER_MONITOR", "Starting docker container {} on node {} for app_id {}".format(docker_id, node, app_id))

                    #Now wait until the inspect returns and says its running then we say its successful
                    time.sleep(10)
                    output = c.inspect_container(docker_id)
                    if output['State']['Running'] == False:
                        logs = c.logs(docker_id)
                        redis_conn.hset("app#{}".format(app_id), "state", "Error updating application, {}".format(logs))
                        logger.info("Problem starting up new container\n Log info: {}".format(logs))
                    else:
                        #First wait until the port responds on the container before continuing and putting into service
                        if not "app_type" in app_details:
                            if not test_web_container(node, port):
                                print "Container did not start successfully"
                                application.set_application_state("Failed deploying new container to %s" % (node))
                                continue
                        else:
                            if not "app" in app_details['app_type']:
                                if not test_web_container(node, port):
                                    print "Container did not start successfully"
                                    application.set_application_state("Failed deploying new container to %s" % (node))
                                    continue

                        redis_conn.hset("containers:{}:{}:{}".format(node, app_id, port), "docker_id", docker_id)
                        redis_conn.hset("containers:{}:{}:{}".format(node, app_id, port), "port", port)
                        redis_conn.hset("app#{}".format(app_id), "state", "RUNNING")
                        data = application.get_all_urls()
                        try:
                            notification_handler.send_message('docker_container_updates', json.dumps(data))
                        except:
                            logger.info("Unable to send docker_container_update to exchange")

                except Exception as e:
                    print e.message
                    logger.error("Error talking to docker node {}".format(node))
                    write_event("CONTAINER_MONITOR", "Failed talking to node {} to start {}".format(node, app_id))
                    redis_conn.hset("app#{}".format(app_id), "state", "Problem talking to node {}".format(node))



        # allow next check in 10s
        redis_conn.delete("app#{}:locked".format(app_id))
        logger.debug("{}:Check complete".format(unique_app_id))
        q.task_done()

def check_nodes():
    logger.info("Starting node check thread")
    while True:
        for node in redis_conn.smembers("hosts"):
            c = docker.Client(base_url='http://{}:4243'.format(node), version="1.12")
            for container in c.containers(all=True):
                docker_id = container["Id"]
                try:
                    container_details = c.inspect_container(docker_id)
                except Exception as e:
                    logger.info("Error getting container details")
                    continue
                app_id = redis_conn.get("docker_id#{}".format(docker_id))
                data = redis_conn.keys("docker_id:locked#{}".format(docker_id))
                if data:
                    continue
                redis_conn.delete("docker_id:locked#{}".format(docker_id))
                if (docker_id != redis_conn.hget("{}:{}".format(node, app_id), "docker_id") or not redis_conn.exists("app#{}".format(app_id))):
                    print redis_conn.hget("{}:{}".format(node, app_id), "docker_id")
                    print redis_conn.exists("app#{}".format(app_id))
                    logger.info("stopping orphaned container {}".format(docker_id))
                    write_event("CONTAINER_MONITOR", "Destroying orphaned docker container {} on node {}".format(docker_id, node))
                    try:
                        c.kill(docker_id)
                        c.remove_container(docker_id)
                    except Exception as e:
                        logger.error("Unable to remove container, error: {}".format(e.message))

                    redis_conn.delete("docker_id#{}".format(docker_id))
                    redis_conn.delete("{}:{}".format(node, app_id))
        time.sleep(10)


def delete_node(docker_ids, cluster_state):
    for node in cluster_state['nodes']:
        c = docker.Client(base_url="http://{}:4243".format(node), version="1.12")
        for docker_id in docker_ids:
            if docker_id in cluster_state['nodes'][node]:
		try:
			c.kill(docker_id)
                	c.remove_container(docker_id)
		except:
			print "Error removing docker container as it doesnt exist"


def monitor_loop():
    list_size = 0
    apps = redis_conn.lrange("monitor", 0 , -1 )
    print apps
    cluster_state = get_cluster_state()
    for app in apps:
    	q.put({ "app": app, "cluster": cluster_state })
    while True:
        time.sleep(60)



def monitor_changes():
    #Setting up a pubsub for event handling
    pubsub = redis_conn.pubsub()
    pubsub.subscribe('app_changes')

    for item in pubsub.listen():
        logger.info("Processing published updates to {}".format(item))
        app_details = redis_conn.hgetall("app#{}".format(item['data']))
        if "name" in app_details:
            cluster_state = get_cluster_state()
            change_queue.put(item['data'])

if __name__ == '__main__':

    q.join()
    change_queue.join()

    for i in range(number_of_threads):
        t = threading.Thread(target=check_app)
        t.daemon = True
        t.start()

    pubsub_thread = threading.Thread(target=monitor_changes)
    pubsub_thread.daemon = True
    pubsub_thread.start()

    #node_thread = threading.Thread(target=check_nodes)
    #node_thread.daemon = True
    #node_thread.start()

    change_thread = threading.Thread(target=process_change)
    change_thread.daemon = True
    change_thread.start()


    monitor_loop()





