#!/usr/bin/env python

from scheduler.maxpernode import MaxPerNodeScheduler as Scheduler
import docker
import redis
import time
import sys
import random
import uuid
import re
import logging
from common.dockerfunctions import DockerFunctions
from common.config import Config
from api.resources.applications import Applications
from api.resources.globalconfig import GlobalConfig
from common.notifications import Notifications

def process_applications():
	config = Config()
	logging.basicConfig(level=config.log_level, format='%(asctime)s:%(levelname)s:%(name)s:%(message)s')
	#Remove verbose requests logging

	logging.getLogger("requests").setLevel(logging.WARNING)

	logger = logging.getLogger(__name__)
	redis_conn = redis.StrictRedis(config.redis_host)
	globalconfig = GlobalConfig(config)
	nodes = globalconfig.get('hosts')
	notifications = Notifications(config)
	application = Applications(config)
	while True:
		apps = redis_conn.lrange('monitor', 0, -1)
		#apps = [ "ci-trend-admin", "courtdocs.daemon.ci" ]
		redis_apps = redis_conn.keys("app#*")
		apps = []
		for redis_app in redis_apps:
			if not ":" in redis_app:
				name = redis_app.split('#')[1]
				apps.append(name)
		for app in apps: 
				logger.info("Processing app: {}".format(app))
				#if not application.set_application_lock(app):
				#	continue
				#else:
				#	print app
				app_details = application.get(app, containers=False)
				if app_details['command'] == "":
					logger.debug("Command not set, application skipped")
					continue
				if app_details['docker_image'] == "":
					logger.debug("Docker Image not set, application skipped")
					continue

				try:
					app_class = DockerFunctions(app, nodes, config, notifications)
					ss = Scheduler(app_class.start_instance, app_class.shutdown_instance, app_class.list_nodes, app_class.health_check, 1)
					logger.debug("Starting scheduler for app: {}".format(app))
					#output = list(ss.run(1))
					output = list()
					for event in ss.run(1):
						logger.debug("Scheduler Event: {}".format(event))
						output.append(event)

					logger.debug("Finished scheduler for app: {}".format(app))
					if ss.success == True:
						application.set_application_state(app, "RUNNING")
					else:
						application.set_application_state(app, "ERROR: Problem deploying application, {}".format(output))
				except Exception as e:
					logger.info("======= Scheduler Failed: {}".format(e.message))
					application.set_application_state(app, e.message)
				#application.remove_application_lock(app)
		time.sleep(5)

if __name__ == '__main__':
	process_applications()
