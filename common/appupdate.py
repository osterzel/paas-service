#!/usr/bin/env python

from scheduler.maxpernode import MaxPerNodeScheduler as Scheduler
import time
import sys
import logging

from api.resources.applications import Applications
from api.resources.globalconfig import GlobalConfig
from common.notifications import Notifications
from common.config import Config
from common.dockerfunctions import DockerFunctions

class ApplicationUpdater():

	def __init__(self):
		self.config = Config()
		self.globalconfig = GlobalConfig(self.config)
		self.nodes = self.globalconfig.get('hosts')
		self.notifications = Notifications(self.config)
		self.application = Applications(self.config)
		self.logger = logging.getLogger(__name__)

	def process_app(self, app, number_per_node = 1, number_of_containers = 1):
		app_details = None
		if not self.application.set_application_lock(app):
			return False
		else:
			app_details = self.application.get(app, containers=False)
			if app_details['command'] == "":
				self.logger.debug("Command not set, application skipped")
				return False
			if app_details['docker_image'] == "":
				self.logger.debug("Docker Image not set, application skipped")
				return False

		number_per_node = 1
	 	number_of_containers = 1	
		if "container_count" in app_details:
			try:
				if app_details['container_count'] == "all":
					number_of_containers = len(self.nodes)
				else:
					number_of_containers = float(app_details['container_count'])
				number_per_node = number_of_containers / len(self.nodes) 
			except ValueError:
				pass

		try:
			app_class = DockerFunctions(app, self.nodes, self.config, self.notifications)
			ss = Scheduler(app_class.start_instance, app_class.shutdown_instance, app_class.list_nodes, app_class.health_check, number_per_node)
			self.logger.debug("Starting scheduler for app:{}".format(app))
			output = list()
			for event in ss.run(number_of_containers):
				self.logger.debug("Scheduler Event: {}".format(event))
				output.append(event)
			
			self.logger.debug("Finished scheduler for app: {}".format(app))
			print output
			if ss.success == True:
				self.application.set_application_state(app, "RUNNING")
			else:
				self.application.set_application_state(app, "ERROR: {}".format(output))
		except Exception as e:
			self.logger.info("======= Scheduler Failed: {}".format(e.message))
			self.application.set_application_state(app, e.message)

		self.application.remove_application_lock(app)	
		return True
