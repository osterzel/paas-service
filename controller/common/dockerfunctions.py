#!/usr/bin/env python

import time
import uuid
import json
from collections import OrderedDict
import socket
import logging
import sys
import requests
from paasevents import write_event

import docker
from common.applications import Applications


class DockerFunctions():

    def __init__(self, app, nodes, notifications):
        self.logger = logging.getLogger(__name__)
        self.notifications = notifications
        self.application = Applications()
        self.app = app
        self.nodes = nodes

    def dockerConfigSplit(self,environment):
        return { entry.split("=",1)[0]: entry.split("=", 1)[1] for entry in environment }

    def health_check(self, container):
        self.logger.debug("Health check start for container {}".format(container))
        #Check environment variables and endpoint
        app_details = self.application.get(self.app)
        all_containers = self.list_nodes()
        for node in all_containers:
            if container in all_containers[node]:
                c = docker.Client(base_url="http://{}:4243".format(node), version="1.12")
                r = c.inspect_container(container)
                current_environment = self.dockerConfigSplit(r["Config"]["Env"])
                #current_environment = { entry.split("=", 1)[0]: entry.split("=", 1)[1] for entry in r["Config"]["Env"] }
                if "PATH" in current_environment:
                    del(current_environment['PATH'])
                if "PORT" in current_environment:
                    del(current_environment['PORT'])

                if current_environment != app_details['environment']:
                    self.logger.info("Application: {}, Container - {}: {} on {} has a different environment".format(self.app, container, r['Name'], node))
                    write_event("HEALTHCHECK_APP", "Container has different configuration", self.app)
                    return False
                if not r['State']['Running']:
                    self.logger.info("Application: {}, Container - {}: {} on {} is not running".format(self.app, container, r['Name'], node))
                    write_event("HEALTHCHECK_APP", "Container is not running", self.app)
                    write_event("HEALTHCHECK_APP", "Last container logs {}".format(c.logs(container=container, tail=2)[0:500]), self.app)
                    return False

                #If the container is not an app container then check the web endpoint
                if "weburlcheck" in r['Name']:
                    port = r["Config"]["ExposedPorts"].iterkeys().next().split('/')[0]
                    success = 0
                    for count in range(60):
                        r = c.inspect_container(container)
                        if r['State']['Running'] == False:
                            return False
                        try:
                            healthcheck_url = 'http://' + node + ':' + port + '/internal/healthcheck' 
                            response = requests.get(healthcheck_url)
                            if response.status_code == 200:
                                self.logger.debug("Application: {}, Container {} healthcheck url successful".format(self.app, container))
                                return True
                            else: 
                                time.sleep(2)
                        except:
                            time.sleep(2)

                    if success == 0:
                        self.logger.info("Application: {}, Container {} healthcheck url failed".format(self.app, container))
                        write_event("HEALTHCHECK_APP", "No reply from container port {}, failed healthcheck".format(port), self.app)
                        return False


                if "web" in r['Name']:
                    port = r["Config"]["ExposedPorts"].iterkeys().next().split('/')[0]
                    s = socket.socket()
                    success = 0
                    for count in range(60):
                        r = c.inspect_container(container)
                        if r['State']['Running'] == False:
                            return False
                        try:
                            s = socket.socket()
                            socket.setdefaulttimeout(3)
                            s.connect((node, int(port)))
                            s.close()
                            self.logger.debug("Application: {}, Container {} port healthcheck successful".format(self.app, container))
                            return True
                        except Exception as e:
                                time.sleep(2)

                    if success == 0:
                        self.logger.info("Application: {}, Container {} port healthcheck failed".format(self.app, container))
                        return False

            self.logger.debug("Container {} healthcheck successful".format(container))
        return True

    def container_logs(self):
        application_logs = {}
        nodes = self.list_nodes()
        for node in nodes:
            c = docker.Client(base_url="http://{}:4243".format(node), version="1.12")
            for container in nodes[node]:
                print container
                application_logs[container[:8]] = (c.logs(container = container, timestamps=True, stream=True))
            c.close()

        return application_logs


    def list_nodes(self):
        nodes = dict()
        nodes_count = dict()
        output_nodes = OrderedDict()
        for node in self.nodes:
            c = docker.Client(base_url="http://{}:4243".format(node), version="1.12")
            nodes[node] = []
            containers = c.containers(all=True)
            nodes_count[node] = len(containers)
            for container in containers:
                if str(container['Names']).find(self.app) != -1:
                    nodes[node].append(container['Id'])

        for node in sorted(nodes_count, key=lambda e: nodes_count[e]):
            output_nodes[node] = nodes[node]
        return output_nodes

    def start_instance(self,node):
        self.logger.debug("Starting container on {} for app: {}".format(node, self.app))
        app_details = self.application.get(self.app)
        c = docker.Client(base_url="http://{}:4243".format(node), version="1.12")
        docker_image = app_details['docker_image']
        environment = app_details['environment']
        memory = int(app_details['memory_in_mb']) * 1024**2
        command = app_details['command'].split()

        app_type = "web"
        if "app_type" in app_details:
            app_type = app_details['app_type']
        else:
            if "type" in app_details:
                app_type = app_details['type']

        if app_type == "web" or app_type == "weburlcheck":
            self.logger.info("Starting a web type container")
            port = self.application.allocate_port()
            #Check if the container exists on the machine otherwise pull it
            try:
                r = c.inspect_image(docker_image)
            except docker.ApiError:
                write_event("START_CONTAINER", "Docker image {} did not exist on node".format(), self.app)
            r = c.create_container(docker_image, command, ports={"{}/tcp".format(port): {}}, environment=dict( environment.items() + {"PORT": port}.items()), mem_limit=memory, name="{}_{}_{}".format(self.app, app_type, port))

            c.start(r['Id'], port_bindings={"{}/tcp".format(port): port})
        else:
            self.logger.info("Starting a app type container")
            app_unique = uuid.uuid1()
            r = c.create_container(docker_image, command, environment=dict( environment.items()), mem_limit=memory, name="{}_{}_{}".format(self.app, app_type, app_unique))
            c.start(r['Id'])

        current_configuration = c.inspect_container(r['Id'])

        #Do healthcheck
        if self.health_check(r['Id']):
                #Put info on queue to update loadbalancer
                #TODO - actually make the update of the loadbalancer synchronous
                self.notifications.send_message("paas", "docker_container_updates", json.dumps(self.application.get_all_urls()))
                if app_type == "web":
                    time.sleep(2)
                self.logger.info("Completed starting container")
                return True
        else:
            self.logger.info("Application: {}, Failed starting container".format(self.app))
            return False

    def shutdown_instance(self,container, restart=False):
        self.logger.info("Shutting down container {} for app: {}".format(container, self.app))
        all_containers = self.list_nodes()
        for node in all_containers:
            if container in all_containers[node]:
                c = docker.Client(base_url="http://{}:4243".format(node), version="1.12")
                container_details = c.inspect_container(container)
                if "web" in container_details['Name']:
                    if container_details['HostConfig']['PortBindings']:
                        for key, value in container_details['HostConfig']['PortBindings'].iteritems():
                            port = value[0]['HostPort']
                            self.logger.debug("Returning port {}".format(port))
                            self.application.return_port(port)
                c.stop(container)
                c.remove_container(container)
                #Put info on queue to update loadbalancer
                self.notifications.send_message("paas", "docker_container_updates", json.dumps(self.application.get_all_urls()))
        return True
