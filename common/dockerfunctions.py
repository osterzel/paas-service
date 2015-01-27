#!/usr/bin/env python

from scheduler.maxpernode import MaxPerNodeScheduler as Scheduler
import docker
import redis
import time
import sys
import random
import uuid
import re
import json
from common.logger import ConsoleLogger
from api.resources.applications import Applications
from collections import OrderedDict
import socket

logger = ConsoleLogger("INFO").getLogger()

class DockerFunctions():
	def __init__(self, app, nodes, config, notifications):
		self.config = config 
		self.notifications = notifications 
		self.application = Applications(self.config)
		self.app = app 
		self.nodes = nodes

	def health_check(self, container):
		#Check environment variables and endpoint
		app_details = self.application.get(self.app)
		all_containers = self.list_nodes()	
		for node in all_containers:
			if container in all_containers[node]:
				c = docker.Client(base_url="http://{}:4243".format(node), version="1.12")
				r = c.inspect_container(container)
				current_environment = { entry.split("=")[0]: entry.split("=")[1] for entry in r["Config"]["Env"] }
				del(current_environment['PATH'])
				try:
					del(current_environment['PORT'])
				except:
					pass
				if current_environment != app_details['environment']:
					print "Container - {}: {} on {} has a different environment".format(container, r['Name'], node)
					return False
				if not r['State']['Running']:
					print "Container - {}: {} on {} is not running".format(container, r['Name'], node)
					return False

				#If the container is not an app container then check the web endpoint
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
							return True
	                			except Exception as e:
	                        			time.sleep(2)

					if success == 0:
						return False

		return True

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
		app_details = self.application.get(self.app)
		c = docker.Client(base_url="http://{}:4243".format(node), version="1.12")
		docker_image = app_details['docker_image']
		environment = app_details['environment']
		memory = int(app_details['memory_in_mb']) * 1024**2
		command = app_details['command'].split()

		app_type = "web"
		if "type" in app_details:
			app_type = app_details['type']

		if app_type == "web":
			port = self.application.allocate_port()
       	       	 	r = c.create_container(docker_image, command, ports={"{}/tcp".format(port): {}}, environment=dict( environment.items() + {"PORT": port}.items()), mem_limit=memory, name="{}_{}_{}".format(self.app, app_type, port))
			c.start(r['Id'], port_bindings={"{}/tcp".format(port): port})
		else:
			app_unique = uuid.uuid1()
       	         	r = c.create_container(docker_image, command, environment=dict( environment.items()), mem_limit=memory, name="{}_{}_{}".format(self.app, app_type, app_unique))
			c.start(r['Id'])

		#Put info on queue to update loadbalancer
		self.notifications.send_message("paas", "docker_container_updates", json.dumps(self.application.get_all_urls())) 

		return True

	def shutdown_instance(self,container):
		all_containers = self.list_nodes()	
		for node in all_containers:
			if container in all_containers[node]:
				c = docker.Client(base_url="http://{}:4243".format(node), version="1.12")		
				container_details = c.inspect_container(container)
				if "web" in container_details['Name']:
					port = container.split('_')[-1]
					self.application.return_port(port)
				c.kill(container)
				c.remove_container(container)
				#Put info on queue to update loadbalancer
				self.notifications.send_message("paas", "docker_container_updates", json.dumps(self.application.get_all_urls())) 
		return True
